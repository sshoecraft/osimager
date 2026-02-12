"""
Test configuration and fixtures.
"""

import pytest
import tempfile
import json
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from ..utils.config import get_settings


@pytest.fixture
def temp_osimager_dir():
    """Create a temporary OSImager directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir) / "osimager"
        base_dir.mkdir()
        
        # Create directory structure
        (base_dir / "core").mkdir()
        (base_dir / "core" / "specs").mkdir()
        (base_dir / "core" / "platforms").mkdir()
        (base_dir / "core" / "locations").mkdir()
        (base_dir / "cli").mkdir()
        
        # Create sample spec
        spec_dir = base_dir / "core" / "specs" / "test-spec"
        spec_dir.mkdir()
        spec_content = {
            "platforms": ["vmware", "virtualbox"],
            "locations": ["local", "datacenter"],
            "provides": {
                "dist": "ubuntu",
                "versions": ["20.04", "22.04"],
                "arches": ["amd64"]
            },
            "defs": {
                "firmware": "uefi"
            }
        }
        with open(spec_dir / "spec.json", 'w') as f:
            json.dump(spec_content, f, indent=2)
        
        # Create sample platform
        platform_content = {
            "type": "vmware",
            "builder": "vmware-iso",
            "description": "VMware platform"
        }
        with open(base_dir / "core" / "platforms" / "vmware.json", 'w') as f:
            json.dump(platform_content, f, indent=2)
        
        # Create sample location
        location_content = {
            "type": "local",
            "description": "Local development environment",
            "network": {"type": "nat"},
            "storage": {"type": "local"}
        }
        with open(base_dir / "core" / "locations" / "local.json", 'w') as f:
            json.dump(location_content, f, indent=2)
        
        yield base_dir


@pytest.fixture
def client(temp_osimager_dir):
    """Create test client with temporary directory."""
    # Override settings for testing
    import os
    os.environ["OSIMAGER_BASE_DIRECTORY"] = str(temp_osimager_dir)
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_build_config():
    """Sample build configuration for testing."""
    return {
        "platform": "vmware",
        "location": "local",
        "spec": "test-spec",
        "variables": {"custom_var": "test_value"},
        "debug": True,
        "dry_run": True
    }
