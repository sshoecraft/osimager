"""
Status API router.

Provides system status and monitoring endpoints.
"""

import psutil
import sys
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends

from utils.config import get_settings
from services.build_manager import BuildManager

router = APIRouter()


async def get_build_manager() -> BuildManager:
    """Dependency to get build manager instance."""
    from main import get_build_manager
    return get_build_manager()


@router.get("/system", response_model=Dict[str, Any])
async def get_system_status() -> Dict[str, Any]:
    """
    Get system status information.
    
    Returns:
        System status including CPU, memory, disk usage
    """
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Get memory usage
    memory = psutil.virtual_memory()
    
    # Get disk usage for the OSImager directory
    settings = get_settings()
    try:
        disk_usage = psutil.disk_usage(str(settings.base_directory))
    except:
        # Fallback to root disk if base directory doesn't exist
        disk_usage = psutil.disk_usage("/")
    
    # Get load average (Unix only)
    load_avg = None
    try:
        load_avg = psutil.getloadavg()
    except AttributeError:
        # Windows doesn't have load average
        pass
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": {
            "usage_percent": cpu_percent,
            "count": cpu_count,
            "load_average": load_avg
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        },
        "disk": {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "percent": (disk_usage.used / disk_usage.total) * 100
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable
        }
    }


@router.get("/build-status", response_model=Dict[str, Any])
async def get_build_status(
    manager: BuildManager = Depends(get_build_manager)
) -> Dict[str, Any]:
    """
    Get build system status.
    
    Returns:
        Build system status and statistics
    """
    # Get recent builds
    builds = await manager.get_builds(limit=100)
    
    # Calculate statistics
    status_counts = {}
    for build in builds:
        status = build.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    active_builds = [b for b in builds if b.status.value in ["queued", "preparing", "running"]]
    completed_builds = [b for b in builds if b.status.value == "completed"]
    failed_builds = [b for b in builds if b.status.value == "failed"]
    
    # Calculate average build time for completed builds
    avg_duration = None
    if completed_builds:
        durations = [b.duration for b in completed_builds if b.duration]
        if durations:
            avg_duration = sum(durations) / len(durations)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "manager": {
            "running": manager.is_running,
            "active_builds": len(active_builds),
            "max_concurrent": manager.settings.max_concurrent_builds,
            "queue_size": manager.build_queue.qsize(),
            "websocket_connections": len(manager.websocket_connections)
        },
        "statistics": {
            "total_builds": len(builds),
            "status_counts": status_counts,
            "success_rate": len(completed_builds) / len(builds) * 100 if builds else 0,
            "average_duration": avg_duration
        },
        "recent_builds": [
            {
                "id": b.id,
                "status": b.status.value,
                "platform": b.config.platform,
                "location": b.config.location,
                "spec": b.config.spec,
                "started_at": b.started_at.isoformat() if b.started_at else None,
                "duration": b.duration
            }
            for b in builds[:10]
        ]
    }


@router.get("/directories", response_model=Dict[str, Any])
async def get_directory_status() -> Dict[str, Any]:
    """
    Get OSImager directory status.
    
    Returns:
        Directory existence and content information
    """
    settings = get_settings()
    
    def check_directory(path: Path) -> Dict[str, Any]:
        """Check directory status and contents."""
        if not path.exists():
            return {"exists": False, "path": str(path)}
        
        try:
            files = list(path.iterdir())
            return {
                "exists": True,
                "path": str(path),
                "file_count": len([f for f in files if f.is_file()]),
                "dir_count": len([f for f in files if f.is_dir()]),
                "total_size": sum(f.stat().st_size for f in files if f.is_file())
            }
        except PermissionError:
            return {
                "exists": True,
                "path": str(path),
                "error": "Permission denied"
            }
        except Exception as e:
            return {
                "exists": True,
                "path": str(path),
                "error": str(e)
            }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "base_directory": check_directory(settings.base_directory),
        "specs_directory": check_directory(settings.specs_directory),
        "platforms_directory": check_directory(settings.platforms_directory),
        "locations_directory": check_directory(settings.locations_directory),
        "cli_directory": check_directory(settings.base_directory / "cli")
    }


@router.get("/health", response_model=Dict[str, Any])
async def health_check(
    manager: BuildManager = Depends(get_build_manager)
) -> Dict[str, Any]:
    """
    Comprehensive health check.
    
    Returns:
        Overall system health status
    """
    settings = get_settings()
    
    # Check directory health
    directories_ok = all([
        settings.base_directory.exists(),
        settings.specs_directory.exists(),
        settings.platforms_directory.exists(),
        settings.locations_directory.exists()
    ])
    
    # Check build manager health
    manager_ok = manager.is_running
    
    # Check system resources
    memory = psutil.virtual_memory()
    disk_usage = psutil.disk_usage(str(settings.base_directory))
    
    memory_ok = memory.percent < 90  # Less than 90% memory usage
    disk_ok = (disk_usage.used / disk_usage.total) < 0.95  # Less than 95% disk usage
    
    overall_health = all([directories_ok, manager_ok, memory_ok, disk_ok])
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "healthy": overall_health,
        "checks": {
            "directories": directories_ok,
            "build_manager": manager_ok,
            "memory": memory_ok,
            "disk": disk_ok
        },
        "details": {
            "memory_usage": memory.percent,
            "disk_usage": (disk_usage.used / disk_usage.total) * 100,
            "active_builds": len(manager.active_builds),
            "websocket_connections": len(manager.websocket_connections)
        }
    }
