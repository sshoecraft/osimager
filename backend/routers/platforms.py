"""
Platforms API router.

Provides REST endpoints for managing OSImager platforms.
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from utils.config import get_settings

router = APIRouter()


class PlatformCreateRequest(BaseModel):
    """Request model for creating a new platform."""
    name: str = Field(..., description="Platform name", pattern="^[a-zA-Z0-9_-]+$")
    description: str = Field("", description="Platform description")
    type: str = Field(..., description="Platform type (e.g., vmware-iso, qemu, etc.)")
    config: Dict[str, Any] = Field(..., description="Platform configuration")
    include: str = Field("all", description="Base platform to include")
    defs: Dict[str, Any] = Field(default_factory=dict, description="Platform definitions")


class PlatformUpdateRequest(BaseModel):
    """Request model for updating a platform."""
    description: str = Field(None, description="Platform description")
    type: str = Field(None, description="Platform type")
    config: Dict[str, Any] = Field(None, description="Platform configuration")
    include: str = Field(None, description="Base platform to include")
    defs: Dict[str, Any] = Field(None, description="Platform definitions")


class PlatformInfo(BaseModel):
    """Platform information with metadata."""
    name: str
    path: str
    size: int
    modified: float
    description: str
    type: str
    builder: str
    config: Dict[str, Any]
    include: str = ""
    defs: Dict[str, Any]
    arches: List[str] = []


class PlatformListResponse(BaseModel):
    """Response model for platform list with metadata."""
    platforms: List[PlatformInfo]
    total: int


@router.get("/", response_model=List[str])
async def list_platforms() -> List[str]:
    """
    List all available platforms.
    
    Returns:
        List of platform names
    """
    settings = get_settings()
    platforms_dir = settings.platforms_directory
    
    if not platforms_dir.exists():
        return []
    
    platforms = []
    for file_path in platforms_dir.glob("*.json"):
        if file_path.is_file():
            platforms.append(file_path.stem)
    
    return sorted(platforms)


@router.get("/list/detailed", response_model=PlatformListResponse)
async def list_platforms_detailed() -> PlatformListResponse:
    """
    List all platforms with detailed metadata.
    
    Returns:
        Detailed list of platforms with metadata
    """
    settings = get_settings()
    platforms_dir = settings.platforms_directory
    
    if not platforms_dir.exists():
        return PlatformListResponse(platforms=[], total=0)
    
    platforms = []
    for file_path in platforms_dir.glob("*.json"):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                platform_info = PlatformInfo(
                    name=file_path.stem,
                    path=str(file_path),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    description=config.get("description", ""),
                    type=config.get("config", {}).get("type", "unknown"),
                    builder=config.get("builder", config.get("config", {}).get("type", "unknown")),
                    config=config.get("config", {}),
                    include=config.get("include", ""),
                    defs=config.get("defs", {}),
                    arches=config.get("arches", [])
                )
                platforms.append(platform_info)
            except Exception as e:
                # Skip invalid platform files but log the error
                print(f"Warning: Error loading platform {file_path.stem}: {e}")
                continue
    
    platforms.sort(key=lambda p: p.name)
    return PlatformListResponse(platforms=platforms, total=len(platforms))


@router.get("/{name}", response_model=Dict[str, Any])
async def get_platform(name: str) -> Dict[str, Any]:
    """
    Get platform configuration by name.
    
    Args:
        name: Platform name
        
    Returns:
        Platform configuration
        
    Raises:
        HTTPException: If platform not found
    """
    settings = get_settings()
    platform_file = settings.platforms_directory / f"{name}.json"
    
    if not platform_file.exists():
        raise HTTPException(status_code=404, detail=f"Platform '{name}' not found")
    
    try:
        with open(platform_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading platform: {str(e)}")


@router.get("/{name}/info", response_model=Dict[str, Any])
async def get_platform_info(name: str) -> Dict[str, Any]:
    """
    Get platform information and metadata.
    
    Args:
        name: Platform name
        
    Returns:
        Platform information including metadata
        
    Raises:
        HTTPException: If platform not found
    """
    settings = get_settings()
    platform_file = settings.platforms_directory / f"{name}.json"
    
    if not platform_file.exists():
        raise HTTPException(status_code=404, detail=f"Platform '{name}' not found")
    
    try:
        # Get file stats
        stat = platform_file.stat()
        
        # Load platform config
        with open(platform_file, 'r') as f:
            config = json.load(f)
        
        return {
            "name": name,
            "path": str(platform_file),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "config": config,
            "description": config.get("description", ""),
            "type": config.get("type", "unknown"),
            "builder": config.get("builder", "unknown")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading platform info: {str(e)}")


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_platform(platform_request: PlatformCreateRequest) -> Dict[str, Any]:
    """
    Create a new platform.
    
    Args:
        platform_request: Platform configuration
        
    Returns:
        Created platform configuration
        
    Raises:
        HTTPException: If platform already exists or creation fails
    """
    settings = get_settings()
    platform_file = settings.platforms_directory / f"{platform_request.name}.json"
    
    # Check if platform already exists
    if platform_file.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Platform '{platform_request.name}' already exists"
        )
    
    # Create platform configuration
    platform_config = {
        "description": platform_request.description,
        "include": platform_request.include,
        "defs": platform_request.defs,
        "config": platform_request.config
    }
    
    # Add type to config if not present
    if "type" not in platform_config["config"]:
        platform_config["config"]["type"] = platform_request.type
    
    try:
        # Ensure platforms directory exists
        platform_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write platform file
        with open(platform_file, 'w') as f:
            json.dump(platform_config, f, indent=2)
        
        return platform_config
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating platform: {str(e)}"
        )


@router.put("/{name}", response_model=Dict[str, Any])
async def update_platform(name: str, platform_request: PlatformUpdateRequest) -> Dict[str, Any]:
    """
    Update an existing platform.
    
    Args:
        name: Platform name
        platform_request: Updated platform configuration
        
    Returns:
        Updated platform configuration
        
    Raises:
        HTTPException: If platform not found or update fails
    """
    settings = get_settings()
    platform_file = settings.platforms_directory / f"{name}.json"
    
    if not platform_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{name}' not found"
        )
    
    try:
        # Load existing configuration
        with open(platform_file, 'r') as f:
            existing_config = json.load(f)
        
        # Update configuration with provided values
        if platform_request.description is not None:
            existing_config["description"] = platform_request.description
        if platform_request.include is not None:
            existing_config["include"] = platform_request.include
        if platform_request.defs is not None:
            existing_config["defs"] = platform_request.defs
        if platform_request.config is not None:
            existing_config["config"] = platform_request.config
            # Update type in config if provided
            if platform_request.type is not None:
                existing_config["config"]["type"] = platform_request.type
        
        # Write updated configuration
        with open(platform_file, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        return existing_config
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating platform: {str(e)}"
        )


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform(name: str) -> None:
    """
    Delete a platform.
    
    Args:
        name: Platform name
        
    Raises:
        HTTPException: If platform not found or deletion fails
    """
    settings = get_settings()
    platform_file = settings.platforms_directory / f"{name}.json"
    
    if not platform_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{name}' not found"
        )
    
    # Prevent deletion of core platforms
    core_platforms = ["all"]
    if name in core_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete core platform '{name}'"
        )
    
    try:
        platform_file.unlink()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting platform: {str(e)}"
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_platform_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate platform configuration.
    
    Args:
        config: Platform configuration to validate
        
    Returns:
        Validation result with errors if any
    """
    errors = []
    
    # Check required fields
    if "config" not in config:
        errors.append("Missing 'config' section")
    else:
        platform_config = config["config"]
        
        # Check for required configuration fields
        if "type" not in platform_config:
            errors.append("Missing 'type' in config section")
        
        # Type-specific validation
        platform_type = platform_config.get("type", "")
        
        if platform_type.startswith("vmware"):
            required_fields = ["vm_name", "output_directory", "cpus", "memory", "disk_size"]
            for field in required_fields:
                if field not in platform_config:
                    errors.append(f"Missing required VMware field: {field}")
        
        elif platform_type == "qemu":
            required_fields = ["vm_name", "output_directory", "cpus", "memory", "disk_size"]
            for field in required_fields:
                if field not in platform_config:
                    errors.append(f"Missing required QEMU field: {field}")
        
        elif platform_type == "virtualbox-iso":
            required_fields = ["vm_name", "cpus", "memory", "disk_size"]
            for field in required_fields:
                if field not in platform_config:
                    errors.append(f"Missing required VirtualBox field: {field}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
