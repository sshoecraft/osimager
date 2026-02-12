#!/usr/bin/env python3
"""
OSImager API Server startup script.

Starts the FastAPI server with proper configuration.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path to access osimager_config
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the configuration module
from osimager_config import config

# Add the api directory to Python path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    # Ensure logs directory exists
    config.ensure_directories()
    
    # Get logging configuration
    log_config = config.get_logging_config()
    level = logging.DEBUG if debug else getattr(logging, log_config['level'].upper())
    
    # Create log file path
    log_file = config.get_log_path('backend_log')
    
    logging.basicConfig(
        level=level,
        format=log_config['format'],
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    
    # Reduce noise from some third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    if not debug:
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="OSImager API Server")
    parser.add_argument(
        "--host", 
        default=config.get('development', 'backend_host', '127.0.0.1'), 
        help="Host to bind to (default from config)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=config.getint('development', 'backend_port', 8000), 
        help="Port to bind to (default from config)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        default=config.getboolean('development', 'auto_reload', False),
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        default=config.getboolean('development', 'debug', False),
        help="Enable debug mode"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    
    # Set environment variables
    if args.debug:
        os.environ["OSIMAGER_DEBUG"] = "true"
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting OSImager API server on {args.host}:{args.port}")
    
    if args.debug:
        logger.info("Debug mode enabled")
    if args.reload:
        logger.info("Auto-reload enabled")
    
    try:
        import uvicorn
        
        # Run the server
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
            log_level="debug" if args.debug else "info",
            access_log=args.debug
        )
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
