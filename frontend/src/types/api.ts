/**
 * TypeScript definitions for OSImager API models.
 * 
 * These types mirror the Pydantic models from the FastAPI backend.
 */

export type BuildStatus = 
  | 'queued'
  | 'preparing'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'timeout';

export type BuildLogLevel = 
  | 'debug'
  | 'info'
  | 'warning'
  | 'error'
  | 'critical';

export interface BuildLogEntry {
  timestamp: string;
  level: BuildLogLevel;
  message: string;
  source?: string;
  context?: Record<string, any>;
}

export interface BuildProgress {
  current_step: string;
  step_number: number;
  total_steps: number;
  percentage: number;
  estimated_remaining?: number;
}

export interface BuildConfig {
  platform: string;
  location: string;
  spec: string;
  name?: string;
  ip?: string;
  variables?: Record<string, any>;
  timeout?: number;
  debug?: boolean;
  dry_run?: boolean;
}

export interface BuildArtifact {
  name: string;
  path: string;
  size: number;
  checksum?: string;
  type: string;
  metadata?: Record<string, any>;
}

export interface Build {
  id: string;
  config: BuildConfig;
  status: BuildStatus;
  progress?: BuildProgress;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  logs: BuildLogEntry[];
  artifacts: BuildArtifact[];
  error_message?: string;
  created_by: string;
}

export interface BuildCreate {
  config: BuildConfig;
  priority?: number;
}

export interface BuildList {
  builds: Build[];
  total: number;
  active: number;
}

export interface BuildUpdate {
  status?: BuildStatus;
  progress?: BuildProgress;
  error_message?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  build_id?: string;
  data?: any;
  timestamp?: string;
}

export interface InitialStatusMessage extends WebSocketMessage {
  type: 'initial_status';
  data: {
    active_builds: number;
    total_builds: number;
    recent_builds: Build[];
  };
}

export interface BuildStatusMessage extends WebSocketMessage {
  type: 'build_status';
  build_id: string;
  data: Build;
}

export interface BuildLogMessage extends WebSocketMessage {
  type: 'build_log';
  build_id: string;
  data: BuildLogEntry;
}

export interface BuildProgressMessage extends WebSocketMessage {
  type: 'build_progress';
  build_id: string;
  data: BuildProgress;
}

// System information
export interface SystemInfo {
  timestamp: string;
  cpu: {
    usage_percent: number;
    count: number;
    load_average: number[];
  };
  memory: {
    total: number;
    available: number;
    used: number;
    percent: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
    percent: number;
  };
  python: {
    version: string;
    executable: string;
  };
}

export interface SystemApiInfo {
  osimager_version: string;
  base_directory: string;
  specs_directory: string;
  platforms_directory: string;
  locations_directory: string;
  python_version: string;
  api_docs: string;
  api_redoc: string;
}

export interface HealthCheck {
  timestamp: string;
  healthy: boolean;
  checks: {
    directories: boolean;
    build_manager: boolean;
    memory: boolean;
    disk: boolean;
  };
  details: {
    memory_usage: number;
    disk_usage: number;
    active_builds: number;
    websocket_connections: number;
  };
}

// Platform and Location types
export interface Platform {
  name: string;
  type: string;
  description?: string;
  config: Record<string, any>;
}

export interface PlatformInfo {
  name: string;
  path: string;
  size: number;
  modified: number;
  description: string;
  type: string;
  builder: string;
  config: Record<string, any>;
  include: string;
  defs: Record<string, any>;
  arches: string[];
}

export interface PlatformListResponse {
  platforms: PlatformInfo[];
  total: number;
}

export interface PlatformCreateRequest {
  name: string;
  description?: string;
  type: string;
  config: Record<string, any>;
  include?: string;
  defs?: Record<string, any>;
}

export interface PlatformUpdateRequest {
  description?: string;
  type?: string;
  config?: Record<string, any>;
  include?: string;
  defs?: Record<string, any>;
}

export interface Location {
  name: string;
  description?: string;
  config: Record<string, any>;
}

export interface LocationInfo {
  name: string;
  path: string;
  size: number;
  modified: number;
  description: string;
  platforms: string[];
  arches: string[];
  defs: Record<string, any>;
  config: Record<string, any>;
  platform_specific: Array<Record<string, any>>;
}

export interface LocationListResponse {
  locations: LocationInfo[];
  count: number;
}

export interface LocationCreateRequest {
  name: string;
  description?: string;
  platforms?: string[];
  arches?: string[];
  defs?: Record<string, any>;
  config?: Record<string, any>;
  platform_specific?: Array<Record<string, any>>;
}

export interface LocationUpdateRequest {
  name: string;
  description?: string;
  platforms?: string[];
  arches?: string[];
  defs?: Record<string, any>;
  config?: Record<string, any>;
  platform_specific?: Array<Record<string, any>>;
}

export interface SpecMetadata {
  name: string;
  path: string;
  size: number;
  modified: string;
  created: string;
}

export interface SpecList {
  specs: SpecMetadata[];
  total: number;
}

export interface Spec {
  name: string;
  description?: string;
  os_type?: string;
  version?: string;
  config: Record<string, any>;
  metadata?: SpecMetadata;
}

// API Response types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

// UI State types
export interface AppState {
  isLoading: boolean;
  error?: string;
  connected: boolean;
}

export interface NotificationState {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  timestamp: Date;
  dismissed?: boolean;
}
