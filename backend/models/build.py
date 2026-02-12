"""
Pydantic models for build-related API endpoints.

Defines data models for build operations, status, and real-time monitoring.
"""

import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class BuildStatus(str, Enum):
    """
    Build status enumeration.
    
    Values:
        QUEUED: Build is queued and waiting to start
        PREPARING: Build is being prepared (validating config, etc.)
        RUNNING: Build is actively running
        COMPLETED: Build completed successfully
        FAILED: Build failed with errors
        CANCELLED: Build was cancelled by user
        TIMEOUT: Build exceeded timeout limit
    """
    
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class BuildLogLevel(str, Enum):
    """
    Build log level enumeration.
    
    Values:
        DEBUG: Debug information
        INFO: Informational messages
        WARNING: Warning messages
        ERROR: Error messages
        CRITICAL: Critical errors
    """
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BuildLogEntry(BaseModel):
    """
    Single build log entry.
    
    Attributes:
        timestamp: Log entry timestamp
        level: Log level
        message: Log message
        source: Source component (packer, ansible, etc.)
        context: Additional context information
    """
    
    timestamp: datetime = Field(..., description="Log timestamp")
    level: BuildLogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    source: str = Field(default="osimager", description="Log source")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class BuildProgress(BaseModel):
    """
    Build progress information.
    
    Attributes:
        current_step: Current step description
        step_number: Current step number (1-based)
        total_steps: Total number of steps
        percentage: Overall completion percentage (0-100)
        estimated_remaining: Estimated remaining time in seconds
    """
    
    current_step: str = Field(..., description="Current step description")
    step_number: int = Field(..., description="Current step number", ge=1)
    total_steps: int = Field(..., description="Total number of steps", ge=1)
    percentage: float = Field(..., description="Completion percentage", ge=0, le=100)
    estimated_remaining: Optional[int] = Field(None, description="Estimated remaining seconds")
    
    @validator('step_number')
    def validate_step_number(cls, v, values):
        """Validate step number is not greater than total steps."""
        if 'total_steps' in values and v > values['total_steps']:
            raise ValueError("Step number cannot exceed total steps")
        return v


class BuildConfig(BaseModel):
    """
    Build configuration parameters.
    
    Attributes:
        platform: Target platform name
        location: Target location name
        spec: Spec name to use
        name: Optional hostname for the build
        ip: Optional IP address for the build
        variables: Custom variables for the build
        timeout: Build timeout in seconds
        debug: Enable debug mode
        dry_run: Perform dry run without actual build
    """
    
    platform: str = Field(..., description="Target platform name")
    location: str = Field(..., description="Target location name")
    spec: str = Field(..., description="Spec name")
    name: Optional[str] = Field(None, description="Optional hostname")
    ip: Optional[str] = Field(None, description="Optional IP address")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Custom variables")
    timeout: Optional[int] = Field(None, description="Build timeout in seconds", gt=0)
    debug: bool = Field(default=False, description="Enable debug mode")
    dry_run: bool = Field(default=False, description="Perform dry run")


class BuildArtifact(BaseModel):
    """
    Build artifact information.
    
    Attributes:
        name: Artifact name
        path: Local path to artifact
        size: Artifact size in bytes
        checksum: Artifact checksum (SHA256)
        type: Artifact type (image, iso, etc.)
        metadata: Additional artifact metadata
    """
    
    name: str = Field(..., description="Artifact name")
    path: str = Field(..., description="Local artifact path")
    size: int = Field(..., description="Artifact size in bytes", ge=0)
    checksum: Optional[str] = Field(None, description="SHA256 checksum")
    type: str = Field(..., description="Artifact type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Build(BaseModel):
    """
    Complete build information model.
    
    Attributes:
        id: Unique build ID
        config: Build configuration
        status: Current build status
        progress: Build progress information
        started_at: Build start timestamp
        completed_at: Build completion timestamp
        duration: Build duration in seconds
        logs: Recent log entries (limited)
        artifacts: Generated artifacts
        error_message: Error message if build failed
        created_by: User who created the build
    """
    
    id: str = Field(..., description="Unique build ID")
    config: BuildConfig = Field(..., description="Build configuration")
    status: BuildStatus = Field(..., description="Current status")
    progress: Optional[BuildProgress] = Field(None, description="Progress information")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration: Optional[int] = Field(None, description="Duration in seconds", ge=0)
    logs: List[BuildLogEntry] = Field(default_factory=list, description="Recent log entries")
    artifacts: List[BuildArtifact] = Field(default_factory=list, description="Generated artifacts")
    error_message: Optional[str] = Field(None, description="Error message")
    created_by: str = Field(default="api", description="User who created build")
    
    @validator('id', pre=True, always=True)
    def generate_id(cls, v):
        """Generate UUID if ID not provided."""
        return v or str(uuid.uuid4())


class BuildCreate(BaseModel):
    """
    Model for creating a new build.
    
    Attributes:
        config: Build configuration
        priority: Build priority (higher = more priority)
    """
    
    config: BuildConfig = Field(..., description="Build configuration")
    priority: int = Field(default=0, description="Build priority", ge=0, le=10)


class BuildList(BaseModel):
    """
    Model for build list response.
    
    Attributes:
        builds: List of builds
        total: Total number of builds
        active: Number of active builds
    """
    
    builds: List[Build] = Field(..., description="List of builds")
    total: int = Field(..., description="Total number of builds")
    active: int = Field(..., description="Number of active builds")


class BuildUpdate(BaseModel):
    """
    Model for updating build information.
    
    Attributes:
        status: New build status
        progress: Updated progress information
        error_message: Error message for failed builds
    """
    
    status: Optional[BuildStatus] = Field(None, description="New status")
    progress: Optional[BuildProgress] = Field(None, description="Updated progress")
    error_message: Optional[str] = Field(None, description="Error message")


class BuildWebSocketMessage(BaseModel):
    """
    Model for WebSocket messages about builds.
    
    Attributes:
        type: Message type (status, progress, log, etc.)
        build_id: Build ID this message relates to
        data: Message data
        timestamp: Message timestamp
    """
    
    type: str = Field(..., description="Message type")
    build_id: str = Field(..., description="Related build ID")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
