"""
Spec service for managing OSImager specifications.

Handles loading, saving, validation, and manipulation of spec files.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from models.spec import (
    Spec, SpecMetadata, SpecCreate, SpecUpdate, SpecList,
    SpecValidationResult, SpecValidationError, SpecProvides, SpecDefaults
)
from utils.config import get_settings

logger = logging.getLogger(__name__)


class SpecService:
    """
    Service for managing OSImager specifications.
    
    Provides methods for CRUD operations on spec files and validation.
    """
    
    def __init__(self):
        """Initialize spec service."""
        self.settings = get_settings()
        self.specs_dir = self.settings.specs_directory
    
    async def list_specs(self) -> SpecList:
        """
        List all available specs.
        
        Returns:
            SpecList containing metadata for all specs.
        """
        specs = []
        
        if not self.specs_dir.exists():
            logger.warning(f"Specs directory does not exist: {self.specs_dir}")
            return SpecList(specs=[], total=0)
        
        # Find all spec.json files
        for spec_dir in self.specs_dir.iterdir():
            if not spec_dir.is_dir():
                continue
            
            spec_file = spec_dir / "spec.json"
            if not spec_file.exists():
                continue
            
            try:
                # Get file metadata
                stat = spec_file.stat()
                metadata = SpecMetadata(
                    name=spec_dir.name,
                    path=str(spec_file),
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                    created=datetime.fromtimestamp(stat.st_ctime)
                )
                specs.append(metadata)
                
            except Exception as e:
                logger.error(f"Error reading spec metadata for {spec_file}: {e}")
                continue
        
        # Sort by name
        specs.sort(key=lambda s: s.name)
        
        return SpecList(specs=specs, total=len(specs))
    
    async def get_spec(self, name: str) -> Optional[Spec]:
        """
        Get a specific spec by name.
        
        Args:
            name: Spec name
            
        Returns:
            Spec object or None if not found
        """
        spec_file = self._get_spec_path(name)
        if not spec_file.exists():
            return None
        
        try:
            # Load JSON content
            with open(spec_file, 'r') as f:
                content = json.load(f)
            
            # Get file metadata
            stat = spec_file.stat()
            metadata = SpecMetadata(
                name=name,
                path=str(spec_file),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
                created=datetime.fromtimestamp(stat.st_ctime)
            )
            
            # Parse provides section
            provides = None
            if 'provides' in content:
                provides_data = content['provides']
                provides = SpecProvides(
                    dist=provides_data.get('dist'),
                    versions=provides_data.get('versions', []),
                    arches=provides_data.get('arches', [])
                )
            
            # Parse defs section
            defs = None
            if 'defs' in content:
                defs = SpecDefaults(**content['defs'])
            
            # Create spec object
            spec = Spec(
                platforms=content.get('platforms', []),
                locations=content.get('locations', []),
                provides=provides,
                defs=defs,
                metadata=metadata,
                **{k: v for k, v in content.items() 
                   if k not in ['platforms', 'locations', 'provides', 'defs']}
            )
            
            return spec
            
        except Exception as e:
            logger.error(f"Error loading spec {name}: {e}")
            return None
    
    async def create_spec(self, spec_create: SpecCreate) -> Spec:
        """
        Create a new spec.
        
        Args:
            spec_create: Spec creation data
            
        Returns:
            Created spec object
            
        Raises:
            ValueError: If spec already exists or invalid data
        """
        # Check if spec already exists
        if await self.get_spec(spec_create.name):
            raise ValueError(f"Spec '{spec_create.name}' already exists")
        
        # Validate content
        validation_result = await self.validate_spec_content(spec_create.content)
        if not validation_result.valid:
            error_messages = [e.message for e in validation_result.errors]
            raise ValueError(f"Invalid spec content: {'; '.join(error_messages)}")
        
        # Create spec directory
        spec_dir = self.specs_dir / spec_create.name
        spec_dir.mkdir(parents=True, exist_ok=True)
        
        # Write spec file
        spec_file = spec_dir / "spec.json"
        with open(spec_file, 'w') as f:
            json.dump(spec_create.content, f, indent=2)
        
        logger.info(f"Created spec: {spec_create.name}")
        
        # Rebuild the specs index
        await self.rebuild_specs_index()
        
        # Return the created spec
        return await self.get_spec(spec_create.name)
    
    async def update_spec(self, name: str, spec_update: SpecUpdate) -> Optional[Spec]:
        """
        Update an existing spec.
        
        Args:
            name: Spec name
            spec_update: Updated spec data
            
        Returns:
            Updated spec object or None if not found
            
        Raises:
            ValueError: If invalid data
        """
        # Check if spec exists
        if not await self.get_spec(name):
            return None
        
        # Validate content
        validation_result = await self.validate_spec_content(spec_update.content)
        if not validation_result.valid:
            error_messages = [e.message for e in validation_result.errors]
            raise ValueError(f"Invalid spec content: {'; '.join(error_messages)}")
        
        # Update spec file
        spec_file = self._get_spec_path(name)
        with open(spec_file, 'w') as f:
            json.dump(spec_update.content, f, indent=2)
        
        logger.info(f"Updated spec: {name}")
        
        # Rebuild the specs index
        await self.rebuild_specs_index()
        
        # Return the updated spec
        return await self.get_spec(name)
    
    async def delete_spec(self, name: str) -> bool:
        """
        Delete a spec.
        
        Args:
            name: Spec name
            
        Returns:
            True if deleted, False if not found
        """
        spec_dir = self.specs_dir / name
        if not spec_dir.exists():
            return False
        
        try:
            # Remove spec directory and all contents
            import shutil
            shutil.rmtree(spec_dir)
            
            logger.info(f"Deleted spec: {name}")
            
            # Rebuild the specs index
            await self.rebuild_specs_index()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting spec {name}: {e}")
            return False
    
    async def validate_spec_content(self, content: Dict[str, Any]) -> SpecValidationResult:
        """
        Validate spec content.
        
        Args:
            content: Spec content to validate
            
        Returns:
            SpecValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        
        # Check required fields (basic validation)
        if not isinstance(content, dict):
            errors.append(SpecValidationError(
                field="root",
                message="Spec content must be a JSON object",
                value=type(content).__name__
            ))
            return SpecValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # Validate platforms field
        if 'platforms' in content:
            platforms = content['platforms']
            if not isinstance(platforms, list):
                errors.append(SpecValidationError(
                    field="platforms",
                    message="Platforms must be a list",
                    value=type(platforms).__name__
                ))
            elif not platforms:
                warnings.append(SpecValidationError(
                    field="platforms",
                    message="No platforms specified",
                    value=platforms
                ))
        
        # Validate locations field
        if 'locations' in content:
            locations = content['locations']
            if not isinstance(locations, list):
                errors.append(SpecValidationError(
                    field="locations",
                    message="Locations must be a list",
                    value=type(locations).__name__
                ))
            elif not locations:
                warnings.append(SpecValidationError(
                    field="locations",
                    message="No locations specified",
                    value=locations
                ))
        
        # Validate provides section
        if 'provides' in content:
            provides = content['provides']
            if not isinstance(provides, dict):
                errors.append(SpecValidationError(
                    field="provides",
                    message="Provides must be an object",
                    value=type(provides).__name__
                ))
            else:
                # Check dist field
                if 'dist' in provides and not isinstance(provides['dist'], str):
                    errors.append(SpecValidationError(
                        field="provides.dist",
                        message="Distribution must be a string",
                        value=type(provides['dist']).__name__
                    ))
                
                # Check versions field
                if 'versions' in provides:
                    versions = provides['versions']
                    if not isinstance(versions, list):
                        errors.append(SpecValidationError(
                            field="provides.versions",
                            message="Versions must be a list",
                            value=type(versions).__name__
                        ))
                    elif not all(isinstance(v, str) for v in versions):
                        errors.append(SpecValidationError(
                            field="provides.versions",
                            message="All version entries must be strings",
                            value=versions
                        ))
                
                # Check arches field
                if 'arches' in provides:
                    arches = provides['arches']
                    if not isinstance(arches, list):
                        errors.append(SpecValidationError(
                            field="provides.arches",
                            message="Architectures must be a list",
                            value=type(arches).__name__
                        ))
                    elif not all(isinstance(a, str) for a in arches):
                        errors.append(SpecValidationError(
                            field="provides.arches",
                            message="All architecture entries must be strings",
                            value=arches
                        ))
        
        # Check for common required sections
        common_sections = ['platforms', 'locations']
        for section in common_sections:
            if section not in content:
                warnings.append(SpecValidationError(
                    field=section,
                    message=f"Missing recommended section: {section}",
                    value=None
                ))
        
        return SpecValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def get_spec_names(self) -> List[str]:
        """
        Get list of all spec names.
        
        Returns:
            List of spec names
        """
        spec_list = await self.list_specs()
        return [spec.name for spec in spec_list.specs]
    
    async def copy_spec(self, source_name: str, target_name: str) -> Optional[Spec]:
        """
        Copy an existing spec to a new name.
        
        Args:
            source_name: Name of spec to copy
            target_name: Name for the new copy
            
        Returns:
            New spec object or None if source not found
            
        Raises:
            ValueError: If target already exists or invalid name
        """
        # Get source spec
        source_spec = await self.get_spec(source_name)
        if not source_spec:
            return None
        
        # Check if target already exists
        if await self.get_spec(target_name):
            raise ValueError(f"Spec '{target_name}' already exists")
        
        # Load source content
        source_file = self._get_spec_path(source_name)
        with open(source_file, 'r') as f:
            content = json.load(f)
        
        # Create new spec
        spec_create = SpecCreate(name=target_name, content=content)
        return await self.create_spec(spec_create)
    
    def _get_spec_path(self, name: str) -> Path:
        """
        Get the path to a spec file.
        
        Args:
            name: Spec name
            
        Returns:
            Path to spec.json file
        """
        return self.specs_dir / name / "spec.json"
    
    async def get_specs_index(self) -> Dict[str, Any]:
        """
        Load and return the specs index.
        
        Returns:
            Dictionary containing the complete specs index
            
        Raises:
            FileNotFoundError: If index file doesn't exist
        """
        index_file = self.specs_dir / "index.json"
        
        if not index_file.exists():
            # Try to generate the index if it doesn't exist
            logger.info("Specs index not found, attempting to generate it")
            if await self.rebuild_specs_index():
                # If generation was successful, try to load again
                if index_file.exists():
                    with open(index_file, 'r') as f:
                        return json.load(f)
            
            raise FileNotFoundError(f"Specs index file not found: {index_file}")
        
        try:
            with open(index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading specs index: {e}")
            raise
    
    async def rebuild_specs_index(self) -> bool:
        """
        Rebuild the specs index by calling the index generator.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            import sys
            
            # Get the path to the index generator script
            script_path = self.settings.data_directory.parent / "generate_specs_index.py"
            
            if not script_path.exists():
                logger.error(f"Index generator script not found: {script_path}")
                return False
            
            # Run the index generator script
            result = subprocess.run([
                sys.executable,
                str(script_path),
                "--data-dir", str(self.settings.data_directory)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Successfully rebuilt specs index")
                return True
            else:
                logger.error(f"Failed to rebuild specs index: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error rebuilding specs index: {e}")
            return False
