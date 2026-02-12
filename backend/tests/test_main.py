"""
Tests for API health and basic endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test API health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "api_version" in data


def test_info_endpoint(client: TestClient):
    """Test API info endpoint."""
    response = client.get("/api/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "osimager_version" in data
    assert "base_directory" in data
    assert "python_version" in data


def test_cors_headers(client: TestClient):
    """Test CORS headers are present."""
    response = client.options("/api/health")
    assert "access-control-allow-origin" in response.headers


def test_api_docs(client: TestClient):
    """Test API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/redoc")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
