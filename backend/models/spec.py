"""
Pydantic models for spec-related API endpoints.

Defines data models for OS specifications, including validation and serialization.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, validator


class SpecProvides(BaseModel):
    """
    Specification provides information.
    
    Attributes:
        dist: Distribution name (e.g., 'ubuntu', 'centos')
        versions: List of supported versions
        arches: List of supported architectures
    """
    
    dist: Optional[str] = Field(None, description="Distribution name")
    versions: List[str] = Field(default_factory=list, description="Supported versions")
    arches: List[str] = Field(default_factory=list, description="Supported architectures")


class SpecDefaults(BaseModel):
    """
    Specification default values.
    
    Attributes:
        firmware: Default firmware type (e.g., 'bios', 'uefi')
        Additional dynamic fields based on spec content
    """
    
    firmware: Optional[str] = Field(None, description="Default firmware type")
    
    class Config:
        extra = "allow"  # Allow additional dynamic fields


class SpecMetadata(BaseModel):
    """
    Specification metadata.
    
    Attributes:
        name: Spec name (derived from filename)
        path: Full path to spec file
        size: File size in bytes
        modified: Last modified timestamp
        created: Creation timestamp
    """
    
    name: str = Field(..., description="Spec name")
    path: str = Field(..., description="Full path to spec file")
    size: int = Field(..., description="File size in bytes")
    modified: datetime = Field(..., description="Last modified timestamp")
    created: Optional[datetime] = Field(None, description="Creation timestamp")


class Spec(BaseModel):
    """
    Complete OS specification model.
    
    Attributes:
        platforms: List of supported platforms
        locations: List of supported locations
        provides: What this spec provides (dist, versions, arches)
        defs: Default values and configuration
        metadata: File metadata information
        Additional dynamic fields from JSON content
    """
    
    platforms: List[str] = Field(default_factory=list, description="Supported platforms")
    locations: List[str] = Field(default_factory=list, description="Supported locations")
    provides: Optional[SpecProvides] = Field(None, description="Spec capabilities")
    defs: Optional[SpecDefaults] = Field(None, description="Default values")
    metadata: Optional[SpecMetadata] = Field(None, description="File metadata")
    
    class Config:
        extra = "allow"  # Allow additional dynamic fields from JSON
    
    @validator('platforms', 'locations', pre=True)
    def ensure_list(cls, v):
        """Ensure platforms and locations are lists."""
        if isinstance(v, str):
            return [v]
        return v or []


class SpecCreate(BaseModel):
    """
    Model for creating a new specification.
    
    Attributes:
        name: Spec name (used for filename)
        content: Spec content as dictionary
    """
    
    name: str = Field(..., description="Spec name", pattern=r"^[a-zA-Z0-9_-]+$")
    content: Dict[str, Any] = Field(..., description="Spec JSON content")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate spec name format."""
        if not v or len(v) < 2:
            raise ValueError("Spec name must be at least 2 characters")
        if len(v) > 50:
            raise ValueError("Spec name must be less than 50 characters")
        return v.lower()


class SpecUpdate(BaseModel):
    """
    Model for updating an existing specification.
    
    Attributes:
        content: Updated spec content
    """
    
    content: Dict[str, Any] = Field(..., description="Updated spec JSON content")


class SpecList(BaseModel):
    """
    Model for spec list response.
    
    Attributes:
        specs: List of spec summaries
        total: Total number of specs
    """
    
    specs: List[SpecMetadata] = Field(..., description="List of specs")
    total: int = Field(..., description="Total number of specs")


class SpecValidationError(BaseModel):
    """
    Model for spec validation errors.
    
    Attributes:
        field: Field that failed validation
        message: Error message
        value: Invalid value
    """
    
    field: str = Field(..., description="Field name")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Invalid value")


class SpecValidationResult(BaseModel):
    """
    Model for spec validation results.
    
    Attributes:
        valid: Whether spec is valid
        errors: List of validation errors
        warnings: List of validation warnings
    """
    
    valid: bool = Field(..., description="Validation result")
    errors: List[SpecValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[SpecValidationError] = Field(default_factory=list, description="Validation warnings")
