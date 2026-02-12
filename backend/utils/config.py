"""Configuration utilities for OSImager API."""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        base_directory: Base OSImager directory path
        specs_directory: Specs directory path
        platforms_directory: Platforms directory path
        locations_directory: Locations directory path
        debug: Enable debug mode
        cors_origins: Allowed CORS origins
        websocket_heartbeat: WebSocket heartbeat interval in seconds
        build_timeout: Default build timeout in seconds
        max_concurrent_builds: Maximum concurrent builds
    """
    
    # Directory settings
    base_directory: Path = Field(
        default_factory=lambda: Path.home() / "src" / "osimager",
        description="Base OSImager directory"
    )
    
    specs_directory: Optional[Path] = Field(
        default=None,
        description="Specs directory (defaults to base_directory/data/specs)"
    )
    
    platforms_directory: Optional[Path] = Field(
        default=None,
        description="Platforms directory (defaults to base_directory/data/platforms)"
    )
    
    locations_directory: Optional[Path] = Field(
        default=None,
        description="Locations directory (defaults to base_directory/data/locations)"
    )
    
    # API settings
    debug: bool = Field(default=False, description="Enable debug mode")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated CORS origins"
    )
    
    # WebSocket settings
    websocket_heartbeat: int = Field(default=30, description="WebSocket heartbeat interval")
    
    # Build settings
    build_timeout: int = Field(default=3600, description="Default build timeout in seconds")
    max_concurrent_builds: int = Field(default=3, description="Maximum concurrent builds")
    
    class Config:
        env_prefix = "OSIMAGER_"
        env_file = ".env"
    
    def __post_init_post_parse__(self):
        """Set default directory paths if not provided."""
        if not self.specs_directory:
            self.specs_directory = self.base_directory / "specs"
        
        if not self.platforms_directory:
            self.platforms_directory = self.base_directory / "platforms"
        
        if not self.locations_directory:
            self.locations_directory = self.base_directory / "locations"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings instance.
    """
    settings = Settings()
    settings.__post_init_post_parse__()
    return settings


def get_osimager_path() -> Path:
    """
    Get the OSImager CLI package path.
    
    Returns:
        Path to the OSImager CLI package.
    """
    return get_settings().base_directory / "cli" / "osimager"
