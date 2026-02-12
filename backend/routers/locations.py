"""
Locations API router.

Provides REST endpoints for managing OSImager locations with full CRUD operations.
"""

import json
from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.config import get_settings

router = APIRouter()


class LocationRequest(BaseModel):
    """Location creation/update request model."""
    name: str
    description: str = ""
    platforms: List[str] = []
    arches: List[str] = []
    defs: Dict[str, Any] = {}
    config: Dict[str, Any] = {}
    platform_specific: List[Dict[str, Any]] = []


class LocationInfo(BaseModel):
    """Location information response model."""
    name: str
    path: str
    size: int
    modified: float
    description: str = ""
    platforms: List[str] = []
    arches: List[str] = []
    defs: Dict[str, Any] = {}
    config: Dict[str, Any] = {}
    platform_specific: List[Dict[str, Any]] = []


class LocationListResponse(BaseModel):
    """Location list response model."""
    locations: List[LocationInfo]
    count: int


@router.get("/", response_model=List[str])
async def list_locations() -> List[str]:
    """
    List all available location names.
    
    Returns:
        List of location names
    """
    settings = get_settings()
    locations_dir = settings.locations_directory
    
    if not locations_dir.exists():
        return []
    
    locations = []
    for file_path in locations_dir.glob("*.json"):
        if file_path.is_file():
            locations.append(file_path.stem)
    
    return sorted(locations)


@router.get("/detailed", response_model=LocationListResponse)
async def list_locations_detailed() -> LocationListResponse:
    """
    List all locations with detailed information.
    
    Returns:
        Detailed location information including metadata
    """
    settings = get_settings()
    locations_dir = settings.locations_directory
    
    if not locations_dir.exists():
        return LocationListResponse(locations=[], count=0)
    
    locations = []
    for file_path in locations_dir.glob("*.json"):
        if file_path.is_file():
            try:
                # Get file stats
                stat = file_path.stat()
                
                # Load location config
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                location_info = LocationInfo(
                    name=file_path.stem,
                    path=str(file_path),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    description=config.get("description", ""),
                    platforms=config.get("platforms", []),
                    arches=config.get("arches", []),
                    defs=config.get("defs", {}),
                    config=config.get("config", {}),
                    platform_specific=config.get("platform_specific", [])
                )
                
                locations.append(location_info)
                
            except Exception as e:
                print(f"Error loading location {file_path}: {e}")
                continue
    
    # Sort by name
    locations.sort(key=lambda x: x.name)
    
    return LocationListResponse(locations=locations, count=len(locations))


@router.get("/{name}", response_model=Dict[str, Any])
async def get_location(name: str) -> Dict[str, Any]:
    """
    Get location configuration by name.
    
    Args:
        name: Location name
        
    Returns:
        Location configuration
        
    Raises:
        HTTPException: If location not found
    """
    settings = get_settings()
    location_file = settings.locations_directory / f"{name}.json"
    
    if not location_file.exists():
        raise HTTPException(status_code=404, detail=f"Location '{name}' not found")
    
    try:
        with open(location_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading location: {str(e)}")


@router.get("/{name}/info", response_model=LocationInfo)
async def get_location_info(name: str) -> LocationInfo:
    """
    Get location information and metadata.
    
    Args:
        name: Location name
        
    Returns:
        Location information including metadata
        
    Raises:
        HTTPException: If location not found
    """
    settings = get_settings()
    location_file = settings.locations_directory / f"{name}.json"
    
    if not location_file.exists():
        raise HTTPException(status_code=404, detail=f"Location '{name}' not found")
    
    try:
        # Get file stats
        stat = location_file.stat()
        
        # Load location config
        with open(location_file, 'r') as f:
            config = json.load(f)
        
        return LocationInfo(
            name=name,
            path=str(location_file),
            size=stat.st_size,
            modified=stat.st_mtime,
            description=config.get("description", ""),
            platforms=config.get("platforms", []),
            arches=config.get("arches", []),
            defs=config.get("defs", {}),
            config=config.get("config", {}),
            platform_specific=config.get("platform_specific", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading location info: {str(e)}")


@router.post("/", response_model=Dict[str, str])
async def create_location(location: LocationRequest) -> Dict[str, str]:
    """
    Create a new location.
    
    Args:
        location: Location configuration
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If location already exists or error creating
    """
    settings = get_settings()
    location_file = settings.locations_directory / f"{location.name}.json"
    
    if location_file.exists():
        raise HTTPException(status_code=409, detail=f"Location '{location.name}' already exists")
    
    try:
        # Ensure locations directory exists
        settings.locations_directory.mkdir(parents=True, exist_ok=True)
        
        # Build location configuration
        config = {
            "description": location.description,
            "platforms": location.platforms,
            "arches": location.arches,
            "defs": location.defs,
            "config": location.config,
            "platform_specific": location.platform_specific
        }
        
        # Remove empty sections
        config = {k: v for k, v in config.items() if v}
        
        # Write location file
        with open(location_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {"message": f"Location '{location.name}' created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating location: {str(e)}")


@router.put("/{name}", response_model=Dict[str, str])
async def update_location(name: str, location: LocationRequest) -> Dict[str, str]:
    """
    Update an existing location.
    
    Args:
        name: Current location name
        location: Updated location configuration
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If location not found or error updating
    """
    settings = get_settings()
    location_file = settings.locations_directory / f"{name}.json"
    
    if not location_file.exists():
        raise HTTPException(status_code=404, detail=f"Location '{name}' not found")
    
    try:
        # Build location configuration
        config = {
            "description": location.description,
            "platforms": location.platforms,
            "arches": location.arches,
            "defs": location.defs,
            "config": location.config,
            "platform_specific": location.platform_specific
        }
        
        # Remove empty sections
        config = {k: v for k, v in config.items() if v}
        
        # If name changed, handle rename
        if location.name != name:
            new_location_file = settings.locations_directory / f"{location.name}.json"
            if new_location_file.exists():
                raise HTTPException(status_code=409, detail=f"Location '{location.name}' already exists")
            
            # Write new file and remove old one
            with open(new_location_file, 'w') as f:
                json.dump(config, f, indent=2)
            location_file.unlink()
            
            return {"message": f"Location renamed from '{name}' to '{location.name}' and updated successfully"}
        else:
            # Update existing file
            with open(location_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return {"message": f"Location '{name}' updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating location: {str(e)}")


@router.delete("/{name}", response_model=Dict[str, str])
async def delete_location(name: str) -> Dict[str, str]:
    """
    Delete a location.
    
    Args:
        name: Location name to delete
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If location not found or is protected
    """
    settings = get_settings()
    location_file = settings.locations_directory / f"{name}.json"
    
    if not location_file.exists():
        raise HTTPException(status_code=404, detail=f"Location '{name}' not found")
    
    # Protect certain core locations
    protected_locations = ["local"]
    if name in protected_locations:
        raise HTTPException(
            status_code=403, 
            detail=f"Cannot delete protected location '{name}'"
        )
    
    try:
        location_file.unlink()
        return {"message": f"Location '{name}' deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting location: {str(e)}")


@router.post("/{name}/validate", response_model=Dict[str, Any])
async def validate_location(name: str) -> Dict[str, Any]:
    """
    Validate a location configuration.
    
    Args:
        name: Location name to validate
        
    Returns:
        Validation results
        
    Raises:
        HTTPException: If location not found
    """
    settings = get_settings()
    location_file = settings.locations_directory / f"{name}.json"
    
    if not location_file.exists():
        raise HTTPException(status_code=404, detail=f"Location '{name}' not found")
    
    try:
        with open(location_file, 'r') as f:
            config = json.load(f)
        
        # Basic validation
        issues = []
        warnings = []
        
        # Check for required sections
        if not config.get("defs"):
            warnings.append("No 'defs' section found - location may not define any variables")
        
        # Check network configuration
        defs = config.get("defs", {})
        if not defs.get("domain"):
            warnings.append("No domain defined in defs")
        
        if not defs.get("gateway"):
            warnings.append("No gateway defined in defs")
        
        # Check platform support
        platforms = config.get("platforms", [])
        if not platforms:
            warnings.append("No platforms specified - location may not be usable")
        
        # Check platform_specific configurations
        platform_specific = config.get("platform_specific", [])
        specified_platforms = set()
        for ps_config in platform_specific:
            platform = ps_config.get("platform")
            if platform:
                specified_platforms.add(platform)
                if platform not in platforms:
                    warnings.append(f"Platform-specific config for '{platform}' but '{platform}' not in platforms list")
        
        # Check for platforms without specific config
        for platform in platforms:
            if platform not in specified_platforms:
                warnings.append(f"Platform '{platform}' has no platform-specific configuration")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "platforms": len(platforms),
                "architectures": len(config.get("arches", [])),
                "definitions": len(defs),
                "platform_specific_configs": len(platform_specific)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating location: {str(e)}")
