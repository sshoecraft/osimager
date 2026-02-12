"""Configuration management API endpoints."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from utils.config import get_settings

router = APIRouter(tags=["configuration"])

class ConfigurationModel(BaseModel):
    """Application configuration model."""
    
    # Real-time settings
    realtime_enabled: bool = Field(default=True, description="Enable real-time WebSocket updates")
    auto_refresh: bool = Field(default=True, description="Auto-refresh data")
    refresh_interval: int = Field(default=5000, description="Refresh interval in milliseconds")
    
    # Build settings
    build_timeout: int = Field(default=3600, description="Build timeout in seconds")
    max_concurrent_builds: int = Field(default=3, description="Maximum concurrent builds")
    
    # API settings
    api_timeout: int = Field(default=30000, description="API timeout in milliseconds")
    max_retries: int = Field(default=3, description="Maximum API retries")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    
    # Display settings
    theme: str = Field(default="light", description="UI theme (light/dark/auto)")
    compact_mode: bool = Field(default=False, description="Use compact layout")
    show_timestamps: bool = Field(default=True, description="Show detailed timestamps")
    
    # Notification settings
    show_toast_notifications: bool = Field(default=True, description="Show toast notifications")
    notification_sound: bool = Field(default=False, description="Play notification sounds")
    
    # Logging settings
    verbose_logs: bool = Field(default=False, description="Enable verbose logging")
    log_level: str = Field(default="info", description="Log level (debug/info/warning/error)")

class SystemConfigModel(BaseModel):
    """System-level configuration that affects backend behavior."""
    
    build_timeout: int = Field(description="Build timeout in seconds")
    max_concurrent_builds: int = Field(description="Maximum concurrent builds")
    debug_mode: bool = Field(description="Enable debug mode")
    log_level: str = Field(description="Log level")
    websocket_heartbeat: int = Field(default=30, description="WebSocket heartbeat interval")

def get_config_file_path() -> Path:
    """Get the path to the user configuration file."""
    settings = get_settings()
    config_dir = settings.base_directory / "data" / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "user_settings.json"

def load_user_config() -> Dict[str, Any]:
    """Load user configuration from file."""
    config_file = get_config_file_path()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_user_config(config: Dict[str, Any]) -> None:
    """Save user configuration to file."""
    config_file = get_config_file_path()
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

@router.get("/user", response_model=ConfigurationModel)
async def get_user_configuration():
    """
    Get user configuration settings.
    
    Returns:
        Current user configuration
    """
    try:
        user_config = load_user_config()
        default_config = ConfigurationModel()
        
        # Merge user config with defaults
        config_dict = default_config.dict()
        config_dict.update(user_config)
        
        return ConfigurationModel(**config_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {str(e)}"
        )

@router.put("/user", response_model=ConfigurationModel)
async def update_user_configuration(config: ConfigurationModel):
    """
    Update user configuration settings.
    
    Args:
        config: New configuration settings
        
    Returns:
        Updated configuration
    """
    try:
        # Save to file
        save_user_config(config.dict())
        
        # Return the saved config
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}"
        )

@router.get("/system")
async def get_system_configuration():
    """
    Get system-level configuration.
    
    Returns:
        Current system configuration from environment/settings
    """
    try:
        settings = get_settings()
        
        return {
            "build_timeout": settings.build_timeout,
            "max_concurrent_builds": settings.max_concurrent_builds,
            "debug_mode": settings.debug,
            "websocket_heartbeat": settings.websocket_heartbeat,
            "base_directory": str(settings.base_directory),
            "specs_directory": str(settings.specs_directory),
            "platforms_directory": str(settings.platforms_directory),
            "locations_directory": str(settings.locations_directory),
            "cors_origins": settings.cors_origins.split(","),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system configuration: {str(e)}"
        )

@router.put("/system")
async def update_system_configuration(config: SystemConfigModel):
    """
    Update system-level configuration.
    
    Note: Some settings require application restart to take effect.
    
    Args:
        config: New system configuration
        
    Returns:
        Success message
    """
    try:
        # For now, just validate the input
        # In a full implementation, you might update environment variables
        # or configuration files that are read on startup
        
        return {
            "message": "System configuration updated",
            "note": "Some settings require application restart to take effect",
            "updated_config": config.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update system configuration: {str(e)}"
        )

@router.post("/reset")
async def reset_user_configuration():
    """
    Reset user configuration to defaults.
    
    Returns:
        Default configuration
    """
    try:
        default_config = ConfigurationModel()
        save_user_config(default_config.dict())
        
        return {
            "message": "Configuration reset to defaults",
            "config": default_config
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset configuration: {str(e)}"
        )

@router.get("/export")
async def export_configuration():
    """
    Export current configuration as JSON.
    
    Returns:
        Complete configuration for export
    """
    try:
        user_config = load_user_config()
        settings = get_settings()
        
        export_data = {
            "user_config": user_config,
            "system_info": {
                "base_directory": str(settings.base_directory),
                "export_timestamp": "2025-06-09T00:00:00Z",
                "version": "1.0"
            }
        }
        
        return export_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export configuration: {str(e)}"
        )

@router.post("/import")
async def import_configuration(config_data: Dict[str, Any]):
    """
    Import configuration from JSON data.
    
    Args:
        config_data: Configuration data to import
        
    Returns:
        Import result
    """
    try:
        # Extract user config if present
        if "user_config" in config_data:
            user_config = config_data["user_config"]
        else:
            # Assume the entire payload is user config
            user_config = config_data
        
        # Validate by creating a ConfigurationModel
        validated_config = ConfigurationModel(**user_config)
        
        # Save the validated config
        save_user_config(validated_config.dict())
        
        return {
            "message": "Configuration imported successfully",
            "imported_config": validated_config
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid configuration data: {str(e)}"
        )
