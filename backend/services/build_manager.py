"""
Build manager service for handling OSImager builds.

Manages build lifecycle, real-time monitoring, and WebSocket communication.
"""

import asyncio
import logging
import json
import uuid
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from queue import PriorityQueue
from dataclasses import dataclass, field

# Add CLI to path for OSImager imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))

from models.build import (
    Build, BuildStatus, BuildConfig, BuildProgress, 
    BuildLogEntry, BuildLogLevel, BuildWebSocketMessage
)
from utils.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class QueuedBuild:
    """Represents a queued build with priority."""
    priority: int
    created_at: datetime
    build: Build
    
    def __lt__(self, other):
        """Compare builds by priority (higher priority first), then by creation time."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at


class BuildRunner:
    """
    Handles execution of a single build.
    
    Manages the build process, captures output, and reports progress.
    """
    
    def __init__(self, build: Build, manager: 'BuildManager'):
        """
        Initialize build runner.
        
        Args:
            build: Build to execute
            manager: Build manager instance
        """
        self.build = build
        self.manager = manager
        self.process: Optional[asyncio.subprocess.Process] = None
        self.cancelled = False
        
    async def run(self) -> None:
        """
        Execute the build.
        
        Runs the OSImager build process and monitors progress.
        """
        logger.info(f"Starting build {self.build.id}")
        
        try:
            # Update build status to preparing
            await self._update_status(BuildStatus.PREPARING)
            await self._log(BuildLogLevel.INFO, "Preparing build environment")
            
            # Validate configuration
            await self._validate_config()
            
            # Update status to running
            await self._update_status(BuildStatus.RUNNING)
            await self._log(BuildLogLevel.INFO, "Starting OSImager build process")
            
            # Build the command
            cmd = await self._build_command()
            logger.info(f"Executing command: {' '.join(cmd)}")
            
            # Start the process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=get_settings().base_directory / "cli"
            )
            
            # Monitor process output
            await self._monitor_output()
            
            # Wait for completion
            return_code = await self.process.wait()
            
            if return_code == 0:
                await self._update_status(BuildStatus.COMPLETED)
                await self._log(BuildLogLevel.INFO, "Build completed successfully")
            else:
                await self._update_status(BuildStatus.FAILED)
                await self._log(BuildLogLevel.ERROR, f"Build failed with exit code {return_code}")
                
        except asyncio.CancelledError:
            self.cancelled = True
            await self._update_status(BuildStatus.CANCELLED)
            await self._log(BuildLogLevel.WARNING, "Build was cancelled")
            if self.process:
                try:
                    self.process.terminate()
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
            raise
            
        except Exception as e:
            logger.exception(f"Build {self.build.id} failed with exception")
            await self._update_status(BuildStatus.FAILED)
            await self._log(BuildLogLevel.ERROR, f"Build failed with exception: {str(e)}")
            self.build.error_message = str(e)
            
        finally:
            # Calculate duration
            if self.build.started_at:
                self.build.completed_at = datetime.utcnow()
                self.build.duration = int((self.build.completed_at - self.build.started_at).total_seconds())
            
            logger.info(f"Build {self.build.id} finished with status {self.build.status}")
    
    async def _validate_config(self) -> None:
        """Validate build configuration."""
        settings = get_settings()
        
        # Check if spec exists using the specs index
        await self._validate_spec()
        
        # Check if platform exists
        platform_path = settings.platforms_directory / f"{self.build.config.platform}.json"
        if not platform_path.exists():
            raise ValueError(f"Platform '{self.build.config.platform}' not found")
        
        # Check if location exists
        location_path = settings.locations_directory / f"{self.build.config.location}.json"
        if not location_path.exists():
            raise ValueError(f"Location '{self.build.config.location}' not found")
    
    async def _validate_spec(self) -> None:
        """Validate spec exists using the specs index."""
        settings = get_settings()
        
        # Load specs index
        index_file = settings.specs_directory / "index.json"
        if not index_file.exists():
            raise ValueError("Specs index not found. Run 'python generate_specs_index.py' to create it.")
        
        try:
            with open(index_file, 'r') as f:
                index = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load specs index: {e}")
        
        # Check if spec key exists in index
        spec_key = self.build.config.spec
        if spec_key not in index:
            raise ValueError(f"Spec '{spec_key}' not found")
        
        # Verify the actual spec file exists
        spec_info = index[spec_key]
        spec_path = Path(spec_info['path'])
        if not spec_path.exists():
            raise ValueError(f"Spec file not found: {spec_path}")
    
    async def _build_command(self) -> List[str]:
        """Build the mkosimage command."""
        cmd = ["python3", "mkosimage"]
        
        # Resolve spec key to directory name
        spec_dir = await self._resolve_spec_directory()
        
        # Add platform/location/spec as single argument
        plan = f"{self.build.config.platform}/{self.build.config.location}/{spec_dir}"
        cmd.append(plan)
        
        # Add optional name and ip if provided
        if self.build.config.name:
            cmd.append(self.build.config.name)
            
        if self.build.config.ip:
            cmd.append(self.build.config.ip)
        
        # Add debug flag if enabled
        if self.build.config.debug:
            cmd.append("--debug")
        
        # Add dry run flag if enabled
        if self.build.config.dry_run:
            cmd.append("--dry-run")
        
        # Add timeout if specified
        if self.build.config.timeout:
            cmd.extend(["--timeout", str(self.build.config.timeout)])
        
        # Add custom variables
        for key, value in self.build.config.variables.items():
            cmd.extend(["--set", f"{key}={value}"])
        
        return cmd
    
    async def _resolve_spec_directory(self) -> str:
        """Resolve spec key to directory name for CLI."""
        settings = get_settings()
        
        # Load specs index
        index_file = settings.specs_directory / "index.json"
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        # Get spec info
        spec_key = self.build.config.spec
        spec_info = index[spec_key]
        spec_path = Path(spec_info['path'])
        
        # Extract directory name from path
        # Path format: /path/to/data/specs/DIRECTORY/spec.json
        spec_directory = spec_path.parent.name
        
        return spec_directory
    
    async def _monitor_output(self) -> None:
        """Monitor process output and parse progress."""
        if not self.process or not self.process.stdout:
            return
        
        step_count = 0
        total_steps = 10  # Default estimate, will be updated if we can parse it
        
        while True:
            try:
                line = await asyncio.wait_for(
                    self.process.stdout.readline(), 
                    timeout=1.0
                )
                
                if not line:
                    break
                
                line_str = line.decode('utf-8', errors='ignore').strip()
                if not line_str:
                    continue
                
                # Log the output
                await self._log(BuildLogLevel.INFO, line_str, source="mkosimage")
                
                # Parse progress information
                progress_info = self._parse_progress(line_str, step_count, total_steps)
                if progress_info:
                    step_count, total_steps = progress_info
                    percentage = min((step_count / total_steps) * 100, 100)
                    
                    self.build.progress = BuildProgress(
                        current_step=line_str,
                        step_number=step_count,
                        total_steps=total_steps,
                        percentage=percentage
                    )
                    
                    # Send progress update
                    await self.manager._broadcast_message(
                        BuildWebSocketMessage(
                            type="progress",
                            build_id=self.build.id,
                            data={
                                "progress": self.build.progress.dict(),
                                "status": self.build.status
                            }
                        )
                    )
                
            except asyncio.TimeoutError:
                # Check if process is still running
                if self.process.returncode is not None:
                    break
                continue
            except Exception as e:
                logger.error(f"Error monitoring output: {e}")
                break
    
    def _parse_progress(self, line: str, current_step: int, total_steps: int) -> Optional[tuple]:
        """
        Parse progress information from output line.
        
        Args:
            line: Output line to parse
            current_step: Current step number
            total_steps: Total steps estimate
            
        Returns:
            Tuple of (new_step_count, new_total_steps) or None
        """
        line_lower = line.lower()
        
        # Common progress indicators
        progress_indicators = [
            "building", "creating", "downloading", "installing",
            "configuring", "provisioning", "finishing", "uploading"
        ]
        
        # Check if this line indicates progress
        if any(indicator in line_lower for indicator in progress_indicators):
            return (current_step + 1, total_steps)
        
        # Try to parse specific Packer output patterns
        if "==> " in line and ":" in line:
            return (current_step + 1, total_steps)
        
        # If we see "Step X/Y" pattern, extract it
        import re
        step_match = re.search(r'step\s+(\d+)[\s/]+(\d+)', line_lower)
        if step_match:
            step_num = int(step_match.group(1))
            total_num = int(step_match.group(2))
            return (step_num, total_num)
        
        return None
    
    async def _update_status(self, status: BuildStatus) -> None:
        """Update build status and broadcast."""
        old_status = self.build.status
        self.build.status = status
        
        if status == BuildStatus.RUNNING and not self.build.started_at:
            self.build.started_at = datetime.utcnow()
        
        # Broadcast status change
        await self.manager._broadcast_message(
            BuildWebSocketMessage(
                type="status",
                build_id=self.build.id,
                data={
                    "old_status": old_status,
                    "new_status": status,
                    "started_at": self.build.started_at.isoformat() if self.build.started_at else None
                }
            )
        )
    
    async def _log(self, level: BuildLogLevel, message: str, source: str = "osimager") -> None:
        """Add log entry and broadcast."""
        log_entry = BuildLogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            source=source
        )
        
        # Add to build logs (keep last 100 entries)
        self.build.logs.append(log_entry)
        if len(self.build.logs) > 100:
            self.build.logs = self.build.logs[-100:]
        
        # Broadcast log entry
        await self.manager._broadcast_message(
            BuildWebSocketMessage(
                type="log",
                build_id=self.build.id,
                data={
                    "log": log_entry.dict()
                }
            )
        )


class BuildManager:
    """
    Manages OSImager builds and real-time monitoring.
    
    Handles build queue, execution, and WebSocket communication for real-time updates.
    """
    
    def __init__(self):
        """Initialize build manager."""
        self.settings = get_settings()
        self.is_running = False
        
        # Build storage
        self.builds: Dict[str, Build] = {}
        self.active_builds: Dict[str, BuildRunner] = {}
        self.build_queue = asyncio.Queue()
        
        # WebSocket connections
        self.websocket_connections: Set[Any] = set()  # Will store WebSocket objects
        
        # Background tasks
        self.worker_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the build manager."""
        if self.is_running:
            return
        
        logger.info("Starting build manager")
        self.is_running = True
        
        # Start background tasks
        self.worker_task = asyncio.create_task(self._build_worker())
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        logger.info("Build manager started")
    
    async def stop(self) -> None:
        """Stop the build manager."""
        if not self.is_running:
            return
        
        logger.info("Stopping build manager")
        self.is_running = False
        
        # Cancel active builds
        for runner in list(self.active_builds.values()):
            await self.cancel_build(runner.build.id)
        
        # Cancel background tasks
        if self.worker_task:
            self.worker_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Close WebSocket connections
        for ws in list(self.websocket_connections):
            try:
                await ws.close()
            except:
                pass
        
        logger.info("Build manager stopped")
    
    async def create_build(self, config: BuildConfig, priority: int = 0) -> Build:
        """
        Create a new build.
        
        Args:
            config: Build configuration
            priority: Build priority (0-10, higher = more priority)
            
        Returns:
            Created build object
        """
        build = Build(
            id=str(uuid.uuid4()),
            config=config,
            status=BuildStatus.QUEUED
        )
        
        # Store build
        self.builds[build.id] = build
        
        # Add to queue
        await self.build_queue.put(QueuedBuild(
            priority=priority,
            created_at=datetime.utcnow(),
            build=build
        ))
        
        logger.info(f"Created build {build.id} with priority {priority}")
        
        # Broadcast build creation
        await self._broadcast_message(
            BuildWebSocketMessage(
                type="created",
                build_id=build.id,
                data={"build": build.dict()}
            )
        )
        
        return build
    
    async def get_build(self, build_id: str) -> Optional[Build]:
        """Get build by ID."""
        return self.builds.get(build_id)
    
    async def get_builds(self, status: Optional[BuildStatus] = None, limit: int = 50) -> List[Build]:
        """
        Get builds with optional filtering.
        
        Args:
            status: Filter by status
            limit: Maximum number of builds to return
            
        Returns:
            List of builds
        """
        builds = list(self.builds.values())
        
        if status:
            builds = [b for b in builds if b.status == status]
        
        # Sort by creation time (newest first)
        builds.sort(key=lambda b: b.started_at or datetime.min, reverse=True)
        
        return builds[:limit]
    
    async def cancel_build(self, build_id: str) -> bool:
        """
        Cancel a build.
        
        Args:
            build_id: Build ID to cancel
            
        Returns:
            True if build was cancelled, False if not found or not cancellable
        """
        build = self.builds.get(build_id)
        if not build:
            return False
        
        # Cancel if queued
        if build.status == BuildStatus.QUEUED:
            build.status = BuildStatus.CANCELLED
            await self._broadcast_message(
                BuildWebSocketMessage(
                    type="cancelled",
                    build_id=build_id,
                    data={"reason": "cancelled_by_user"}
                )
            )
            return True
        
        # Cancel if running
        runner = self.active_builds.get(build_id)
        if runner:
            runner.cancelled = True
            if runner.process:
                try:
                    runner.process.terminate()
                except:
                    pass
            return True
        
        return False
    
    async def add_websocket(self, websocket) -> None:
        """Add WebSocket connection for real-time updates."""
        self.websocket_connections.add(websocket)
        logger.info(f"WebSocket connected, total connections: {len(self.websocket_connections)}")
    
    async def remove_websocket(self, websocket) -> None:
        """Remove WebSocket connection."""
        self.websocket_connections.discard(websocket)
        logger.info(f"WebSocket disconnected, total connections: {len(self.websocket_connections)}")
    
    async def _build_worker(self) -> None:
        """Background worker for processing build queue."""
        logger.info("Build worker started")
        
        while self.is_running:
            try:
                # Check if we can start a new build
                if len(self.active_builds) >= self.settings.max_concurrent_builds:
                    await asyncio.sleep(1)
                    continue
                
                # Get next build from queue
                try:
                    queued_build = await asyncio.wait_for(
                        self.build_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Skip if build was cancelled while queued
                if queued_build.build.status == BuildStatus.CANCELLED:
                    continue
                
                # Start the build
                runner = BuildRunner(queued_build.build, self)
                self.active_builds[queued_build.build.id] = runner
                
                # Run build in background
                task = asyncio.create_task(runner.run())
                
                # Clean up when done
                def cleanup_build(task_ref):
                    build_id = queued_build.build.id
                    if build_id in self.active_builds:
                        del self.active_builds[build_id]
                    logger.info(f"Cleaned up build {build_id}")
                
                task.add_done_callback(cleanup_build)
                
            except Exception as e:
                logger.exception("Error in build worker")
                await asyncio.sleep(1)
        
        logger.info("Build worker stopped")
    
    async def _cleanup_worker(self) -> None:
        """Background worker for cleaning up old builds."""
        logger.info("Cleanup worker started")
        
        while self.is_running:
            try:
                # Clean up builds older than 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                builds_to_remove = []
                
                for build_id, build in self.builds.items():
                    if (build.completed_at and build.completed_at < cutoff and 
                        build.status in [BuildStatus.COMPLETED, BuildStatus.FAILED, BuildStatus.CANCELLED]):
                        builds_to_remove.append(build_id)
                
                for build_id in builds_to_remove:
                    del self.builds[build_id]
                    logger.info(f"Cleaned up old build {build_id}")
                
                # Sleep for 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.exception("Error in cleanup worker")
                await asyncio.sleep(60)
        
        logger.info("Cleanup worker stopped")
    
    async def _broadcast_message(self, message: BuildWebSocketMessage) -> None:
        """Broadcast message to all connected WebSockets."""
        if not self.websocket_connections:
            return
        
        message_json = json.dumps(message.dict(), default=str)
        
        # Send to all connections
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(ws)
        
        # Remove disconnected connections
        for ws in disconnected:
            self.websocket_connections.discard(ws)
