"""
Specs API router.

Provides REST endpoints for managing OSImager specifications.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from models.spec import (
    Spec, SpecCreate, SpecUpdate, SpecList, SpecValidationResult
)
from services.spec_service import SpecService

router = APIRouter()


def get_spec_service() -> SpecService:
    """Dependency to get spec service instance."""
    return SpecService()


@router.get("/", response_model=SpecList)
async def list_specs(
    service: SpecService = Depends(get_spec_service)
) -> SpecList:
    """
    List all available specs.
    
    Returns:
        List of spec metadata
    """
    return await service.list_specs()


@router.get("/index", response_model=dict)
async def get_specs_index(
    service: SpecService = Depends(get_spec_service)
) -> dict:
    """
    Get the specs index for build creation.
    
    Returns:
        Dictionary containing the complete specs index
        
    Raises:
        HTTPException: If index file not found or invalid
    """
    try:
        return await service.get_specs_index()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Specs index not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load specs index: {str(e)}")


@router.post("/rebuild-index", status_code=204)
async def rebuild_specs_index(
    service: SpecService = Depends(get_spec_service)
) -> None:
    """
    Rebuild the specs index from all spec files.
    
    This endpoint triggers a regeneration of the specs index,
    which should be called whenever specs are added, modified, or removed.
    
    Raises:
        HTTPException: If index rebuild fails
    """
    try:
        success = await service.rebuild_specs_index()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to rebuild specs index")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild specs index: {str(e)}")


@router.get("/names", response_model=List[str])
async def get_spec_names(
    service: SpecService = Depends(get_spec_service)
) -> List[str]:
    """
    Get list of all spec names.
    
    Returns:
        List of spec names
    """
    return await service.get_spec_names()


@router.get("/{name}", response_model=Spec)
async def get_spec(
    name: str,
    service: SpecService = Depends(get_spec_service)
) -> Spec:
    """
    Get a specific spec by name.
    
    Args:
        name: Spec name
        
    Returns:
        Spec object
        
    Raises:
        HTTPException: If spec not found
    """
    spec = await service.get_spec(name)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Spec '{name}' not found")
    return spec


@router.post("/", response_model=Spec, status_code=201)
async def create_spec(
    spec_create: SpecCreate,
    service: SpecService = Depends(get_spec_service)
) -> Spec:
    """
    Create a new spec.
    
    Args:
        spec_create: Spec creation data
        
    Returns:
        Created spec object
        
    Raises:
        HTTPException: If spec already exists or invalid data
    """
    try:
        return await service.create_spec(spec_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create spec: {str(e)}")


@router.put("/{name}", response_model=Spec)
async def update_spec(
    name: str,
    spec_update: SpecUpdate,
    service: SpecService = Depends(get_spec_service)
) -> Spec:
    """
    Update an existing spec.
    
    Args:
        name: Spec name
        spec_update: Updated spec data
        
    Returns:
        Updated spec object
        
    Raises:
        HTTPException: If spec not found or invalid data
    """
    try:
        spec = await service.update_spec(name, spec_update)
        if not spec:
            raise HTTPException(status_code=404, detail=f"Spec '{name}' not found")
        return spec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update spec: {str(e)}")


@router.delete("/{name}", status_code=204)
async def delete_spec(
    name: str,
    service: SpecService = Depends(get_spec_service)
) -> None:
    """
    Delete a spec.
    
    Args:
        name: Spec name
        
    Raises:
        HTTPException: If spec not found
    """
    success = await service.delete_spec(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Spec '{name}' not found")


@router.post("/{name}/copy", response_model=Spec, status_code=201)
async def copy_spec(
    name: str,
    target_name: str = Query(..., description="Target name for the copy"),
    service: SpecService = Depends(get_spec_service)
) -> Spec:
    """
    Copy an existing spec to a new name.
    
    Args:
        name: Source spec name
        target_name: Target spec name
        
    Returns:
        New spec object
        
    Raises:
        HTTPException: If source not found, target exists, or invalid data
    """
    try:
        spec = await service.copy_spec(name, target_name)
        if not spec:
            raise HTTPException(status_code=404, detail=f"Source spec '{name}' not found")
        return spec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy spec: {str(e)}")


@router.post("/{name}/validate", response_model=SpecValidationResult)
async def validate_spec(
    name: str,
    service: SpecService = Depends(get_spec_service)
) -> SpecValidationResult:
    """
    Validate an existing spec.
    
    Args:
        name: Spec name to validate
        
    Returns:
        Validation result
        
    Raises:
        HTTPException: If spec not found
    """
    spec = await service.get_spec(name)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Spec '{name}' not found")
    
    # Extract content from spec (excluding metadata)
    content = spec.dict(exclude={'metadata'})
    return await service.validate_spec_content(content)
