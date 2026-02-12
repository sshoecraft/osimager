"""
Tests for specs API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_list_specs(client: TestClient):
    """Test listing specs."""
    response = client.get("/api/specs/")
    assert response.status_code == 200
    
    data = response.json()
    assert "specs" in data
    assert "total" in data
    assert data["total"] >= 1  # Should have at least the test spec


def test_get_spec_names(client: TestClient):
    """Test getting spec names."""
    response = client.get("/api/specs/names")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert "test-spec" in data


def test_get_spec(client: TestClient):
    """Test getting a specific spec."""
    response = client.get("/api/specs/test-spec")
    assert response.status_code == 200
    
    data = response.json()
    assert "platforms" in data
    assert "locations" in data
    assert "provides" in data
    assert "metadata" in data
    
    # Check specific content
    assert "vmware" in data["platforms"]
    assert "local" in data["locations"]
    assert data["provides"]["dist"] == "ubuntu"


def test_get_nonexistent_spec(client: TestClient):
    """Test getting a non-existent spec."""
    response = client.get("/api/specs/nonexistent")
    assert response.status_code == 404


def test_validate_spec(client: TestClient):
    """Test spec validation."""
    response = client.post("/api/specs/test-spec/validate")
    assert response.status_code == 200
    
    data = response.json()
    assert "valid" in data
    assert "errors" in data
    assert "warnings" in data


def test_validate_spec_content(client: TestClient):
    """Test validating spec content directly."""
    spec_content = {
        "platforms": ["vmware"],
        "locations": ["local"],
        "provides": {
            "dist": "ubuntu",
            "versions": ["22.04"],
            "arches": ["amd64"]
        }
    }
    
    response = client.post("/api/specs/validate", json=spec_content)
    assert response.status_code == 200
    
    data = response.json()
    assert data["valid"] is True


def test_validate_invalid_spec_content(client: TestClient):
    """Test validating invalid spec content."""
    invalid_content = {
        "platforms": "not_a_list",  # Should be a list
        "provides": {
            "versions": "not_a_list"  # Should be a list
        }
    }
    
    response = client.post("/api/specs/validate", json=invalid_content)
    assert response.status_code == 200
    
    data = response.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


def test_create_spec(client: TestClient):
    """Test creating a new spec."""
    new_spec = {
        "name": "test-new-spec",
        "content": {
            "platforms": ["virtualbox"],
            "locations": ["local"],
            "provides": {
                "dist": "debian",
                "versions": ["11"],
                "arches": ["amd64"]
            }
        }
    }
    
    response = client.post("/api/specs/", json=new_spec)
    assert response.status_code == 201
    
    data = response.json()
    assert data["platforms"] == ["virtualbox"]
    assert data["provides"]["dist"] == "debian"


def test_create_duplicate_spec(client: TestClient):
    """Test creating a spec that already exists."""
    duplicate_spec = {
        "name": "test-spec",  # Already exists
        "content": {
            "platforms": ["virtualbox"],
            "locations": ["local"]
        }
    }
    
    response = client.post("/api/specs/", json=duplicate_spec)
    assert response.status_code == 400


def test_update_spec(client: TestClient):
    """Test updating an existing spec."""
    updated_content = {
        "content": {
            "platforms": ["vmware", "virtualbox", "qemu"],
            "locations": ["local", "datacenter"],
            "provides": {
                "dist": "ubuntu",
                "versions": ["20.04", "22.04", "24.04"],
                "arches": ["amd64", "arm64"]
            },
            "defs": {
                "firmware": "uefi"
            }
        }
    }
    
    response = client.put("/api/specs/test-spec", json=updated_content)
    assert response.status_code == 200
    
    data = response.json()
    assert "qemu" in data["platforms"]
    assert "arm64" in data["provides"]["arches"]


def test_update_nonexistent_spec(client: TestClient):
    """Test updating a non-existent spec."""
    update_data = {
        "content": {
            "platforms": ["vmware"]
        }
    }
    
    response = client.put("/api/specs/nonexistent", json=update_data)
    assert response.status_code == 404


def test_copy_spec(client: TestClient):
    """Test copying a spec."""
    response = client.post("/api/specs/test-spec/copy?target_name=test-spec-copy")
    assert response.status_code == 201
    
    data = response.json()
    assert data["metadata"]["name"] == "test-spec-copy"
    assert data["platforms"] == ["vmware", "virtualbox"]  # Same as original


def test_copy_nonexistent_spec(client: TestClient):
    """Test copying a non-existent spec."""
    response = client.post("/api/specs/nonexistent/copy?target_name=copy-target")
    assert response.status_code == 404


def test_delete_spec(client: TestClient):
    """Test deleting a spec."""
    # First create a spec to delete
    new_spec = {
        "name": "test-delete-spec",
        "content": {
            "platforms": ["virtualbox"],
            "locations": ["local"]
        }
    }
    
    create_response = client.post("/api/specs/", json=new_spec)
    assert create_response.status_code == 201
    
    # Now delete it
    delete_response = client.delete("/api/specs/test-delete-spec")
    assert delete_response.status_code == 204
    
    # Verify it's gone
    get_response = client.get("/api/specs/test-delete-spec")
    assert get_response.status_code == 404


def test_delete_nonexistent_spec(client: TestClient):
    """Test deleting a non-existent spec."""
    response = client.delete("/api/specs/nonexistent")
    assert response.status_code == 404
