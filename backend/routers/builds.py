"""
Builds API router.

Provides REST endpoints for managing OSImager builds and WebSocket for real-time monitoring.
"""

import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from models.build import (
    Build, BuildCreate, BuildUpdate, BuildList, BuildStatus, BuildLogEntry
)
from services.build_manager import BuildManager

router = APIRouter()


async def get_build_manager() -> BuildManager:
    """
    Dependency to get build manager instance.
    
    Returns:
        BuildManager instance
        
    Raises:
        HTTPException: If build manager not available
    """
    # Import here to avoid circular import
    from main import get_build_manager
    return get_build_manager()


@router.get("/", response_model=BuildList)
async def list_builds(
    status: Optional[BuildStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of builds"),
    manager: BuildManager = Depends(get_build_manager)
) -> BuildList:
    """
    List builds with optional filtering.
    
    Args:
        status: Optional status filter
        limit: Maximum number of builds to return
        
    Returns:
        List of builds with metadata
    """
    builds = await manager.get_builds(status=status, limit=limit)
    active_count = len([b for b in builds if b.status in [
        BuildStatus.QUEUED, BuildStatus.PREPARING, BuildStatus.RUNNING
    ]])
    
    return BuildList(
        builds=builds,
        total=len(builds),
        active=active_count
    )


@router.get("/{build_id}", response_model=Build)
async def get_build(
    build_id: str,
    manager: BuildManager = Depends(get_build_manager)
) -> Build:
    """
    Get a specific build by ID.
    
    Args:
        build_id: Build ID
        
    Returns:
        Build object
        
    Raises:
        HTTPException: If build not found
    """
    build = await manager.get_build(build_id)
    if not build:
        raise HTTPException(status_code=404, detail=f"Build '{build_id}' not found")
    return build


@router.post("/", response_model=Build, status_code=201)
async def create_build(
    build_create: BuildCreate,
    manager: BuildManager = Depends(get_build_manager)
) -> Build:
    """
    Create and queue a new build.
    
    Args:
        build_create: Build configuration and priority
        
    Returns:
        Created build object
        
    Raises:
        HTTPException: If invalid configuration
    """
    try:
        return await manager.create_build(
            config=build_create.config,
            priority=build_create.priority
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create build: {str(e)}")


@router.post("/{build_id}/cancel", response_model=Build)
async def cancel_build(
    build_id: str,
    manager: BuildManager = Depends(get_build_manager)
) -> Build:
    """
    Cancel a build.
    
    Args:
        build_id: Build ID to cancel
        
    Returns:
        Updated build object
        
    Raises:
        HTTPException: If build not found or not cancellable
    """
    success = await manager.cancel_build(build_id)
    if not success:
        build = await manager.get_build(build_id)
        if not build:
            raise HTTPException(status_code=404, detail=f"Build '{build_id}' not found")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Build '{build_id}' cannot be cancelled (status: {build.status})"
            )
    
    # Return updated build
    build = await manager.get_build(build_id)
    return build


@router.get("/{build_id}/logs", response_model=List[BuildLogEntry])
async def get_build_logs(
    build_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries"),
    manager: BuildManager = Depends(get_build_manager)
) -> List[BuildLogEntry]:
    """
    Get build logs.
    
    Args:
        build_id: Build ID
        limit: Maximum number of log entries
        
    Returns:
        List of log entries
        
    Raises:
        HTTPException: If build not found
    """
    build = await manager.get_build(build_id)
    if not build:
        raise HTTPException(status_code=404, detail=f"Build '{build_id}' not found")
    
    # Return most recent logs (limited)
    return build.logs[-limit:] if build.logs else []


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    manager: BuildManager = Depends(get_build_manager)
):
    """
    WebSocket endpoint for real-time build monitoring.
    
    Provides real-time updates for:
    - Build status changes
    - Build progress updates
    - Log entries
    - Build creation/completion
    """
    await websocket.accept()
    await manager.add_websocket(websocket)
    
    try:
        # Send initial status
        builds = await manager.get_builds(limit=10)
        active_builds = [b for b in builds if b.status in [
            BuildStatus.QUEUED, BuildStatus.PREPARING, BuildStatus.RUNNING
        ]]
        
        await websocket.send_json({
            "type": "initial_status",
            "data": {
                "active_builds": len(active_builds),
                "total_builds": len(builds),
                "recent_builds": [b.dict() for b in builds[:5]]
            }
        })
        
        # Send periodic heartbeat and handle client messages
        last_heartbeat = asyncio.get_event_loop().time()
        heartbeat_interval = 20  # Send heartbeat every 20 seconds
        
        while True:
            try:
                current_time = asyncio.get_event_loop().time()
                
                # Send heartbeat if needed
                if current_time - last_heartbeat > heartbeat_interval:
                    await websocket.send_json({"type": "heartbeat"})
                    last_heartbeat = current_time
                
                # Wait for client messages with short timeout
                try:
                    message = await asyncio.wait_for(
                        websocket.receive_json(), 
                        timeout=1.0
                    )
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif message.get("type") == "pong":
                        # Client responded to our heartbeat
                        pass
                    elif message.get("type") == "subscribe_build":
                        # Client wants updates for specific build
                        build_id = message.get("build_id")
                        if build_id:
                            build = await manager.get_build(build_id)
                            if build:
                                await websocket.send_json({
                                    "type": "build_status",
                                    "build_id": build_id,
                                    "data": build.dict()
                                })
                            else:
                                await websocket.send_json({
                                    "type": "error",
                                    "data": {"error": f"Build {build_id} not found"}
                                })
                                
                except asyncio.TimeoutError:
                    # No message received, continue with heartbeat check
                    continue
                    
            except Exception as e:
                # Log error but continue
                import logging
                logging.getLogger(__name__).error(f"WebSocket message error: {e}")
                break
                
    except WebSocketDisconnect:
        import logging
        logging.getLogger(__name__).info("WebSocket client disconnected")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"WebSocket error: {e}")
    finally:
        await manager.remove_websocket(websocket)
