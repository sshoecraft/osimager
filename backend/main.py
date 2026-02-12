"""
OSImager FastAPI Backend.

Main application entry point for the OSImager web API.
Provides RESTful endpoints and WebSocket connections for real-time build monitoring.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

# Add the CLI package to the path so we can import OSImager
sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))

# Import routers and services
try:
    # Try relative imports first (when imported as package)
    from .routers import specs, builds, status, platforms, locations, config
    from .services.build_manager import BuildManager
    from .utils.config import get_settings
except ImportError:
    # Fall back to absolute imports (when run directly)
    from routers import specs, builds, status, platforms, locations, config
    from services.build_manager import BuildManager
    from utils.config import get_settings

logger = logging.getLogger(__name__)

# Global build manager instance
build_manager: BuildManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global build_manager
    
    # Startup
    logger.info("Starting OSImager API...")
    build_manager = BuildManager()
    await build_manager.start()
    logger.info("Build manager started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OSImager API...")
    if build_manager:
        await build_manager.stop()
    logger.info("API shutdown complete")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="OSImager API",
    description="REST API for OSImager - OS Image Building and Automation System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(specs.router, prefix="/api/specs", tags=["specs"])
app.include_router(builds.router, prefix="/api/builds", tags=["builds"])
app.include_router(status.router, prefix="/api/status", tags=["status"])
app.include_router(platforms.router, prefix="/api/platforms", tags=["platforms"])
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])
app.include_router(config.router, prefix="/api/config", tags=["configuration"])

# Mount static files for production
static_path = Path(__file__).parent.parent / "frontend" / "dist"
if static_path.exists():
    # Mount the entire dist directory for static assets
    app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")
    
    # Handle favicon.svg separately
    @app.get("/favicon.svg")
    async def get_favicon():
        favicon_path = static_path / "favicon.svg"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        raise HTTPException(status_code=404, detail="Favicon not found")

    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        """Serve the React app."""
        index_file = static_path / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(), status_code=200)
        return HTMLResponse(content="<h1>OSImager API</h1><p>Frontend not built yet.</p>")
    
    # Catch-all route for React Router
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_react_app(full_path: str):
        """Serve React app for all frontend routes."""
        # Don't serve React app for API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        index_file = static_path / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(), status_code=200)
        raise HTTPException(status_code=404, detail="Frontend not available")


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Dict containing API status and build manager health.
    """
    global build_manager
    
    health_data = {
        "status": "healthy",
        "api_version": "1.0.0",
        "build_manager": "not_initialized"
    }
    
    if build_manager:
        health_data["build_manager"] = "running" if build_manager.is_running else "stopped"
        health_data["active_builds"] = len(build_manager.active_builds)
    
    return health_data


@app.get("/api/info")
async def get_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        Dict containing system and configuration information.
    """
    settings = get_settings()
    
    return {
        "osimager_version": "1.0.0",
        "base_directory": str(settings.base_directory),
        "specs_directory": str(settings.specs_directory),
        "platforms_directory": str(settings.platforms_directory),
        "locations_directory": str(settings.locations_directory),
        "python_version": sys.version,
        "api_docs": "/docs",
        "api_redoc": "/redoc"
    }


def get_build_manager() -> BuildManager:
    """
    Get the global build manager instance.
    
    Returns:
        BuildManager instance.
        
    Raises:
        HTTPException: If build manager is not initialized.
    """
    global build_manager
    if not build_manager:
        raise HTTPException(status_code=503, detail="Build manager not initialized")
    return build_manager


if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run the server on all interfaces
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,
        reload=True,
        log_level="info"
    )
