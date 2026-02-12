# OSImager API

FastAPI-based REST API for OSImager with real-time build monitoring.

## Features

- **REST API** for managing specs, builds, platforms, and locations
- **Real-time monitoring** via WebSockets for live build updates
- **Build management** with queue, priority, and cancellation support
- **Spec validation** with detailed error reporting
- **System monitoring** with health checks and status endpoints
- **Auto-generated documentation** with OpenAPI/Swagger

## Quick Start

### Prerequisites

- Python 3.8+
- OSImager CLI tools (in `../cli/`)
- Required system tools (Packer, etc.)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python run_server.py
```

Or with custom options:
```bash
python run_server.py --host 0.0.0.0 --port 8080 --reload --debug
```

### Development Mode

For development with auto-reload:
```bash
python run_server.py --reload --debug
```

## API Documentation

Once the server is running, visit:

- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Health & Status
- `GET /api/health` - Overall system health
- `GET /api/info` - System information
- `GET /api/status/system` - System resource usage
- `GET /api/status/build-status` - Build system status
- `GET /api/status/directories` - Directory status

### Specs Management
- `GET /api/specs/` - List all specs
- `GET /api/specs/names` - Get spec names only
- `GET /api/specs/{name}` - Get specific spec
- `POST /api/specs/` - Create new spec
- `PUT /api/specs/{name}` - Update spec
- `DELETE /api/specs/{name}` - Delete spec
- `POST /api/specs/{name}/copy` - Copy spec
- `POST /api/specs/{name}/validate` - Validate spec
- `POST /api/specs/validate` - Validate spec content

### Build Management
- `GET /api/builds/` - List builds (with filtering)
- `GET /api/builds/{id}` - Get specific build
- `POST /api/builds/` - Create new build
- `POST /api/builds/{id}/cancel` - Cancel build
- `GET /api/builds/{id}/logs` - Get build logs

### Real-time Monitoring
- `WebSocket /api/builds/ws` - Real-time build updates

### Platforms & Locations
- `GET /api/platforms/` - List platforms
- `GET /api/platforms/{name}` - Get platform config
- `GET /api/locations/` - List locations
- `GET /api/locations/{name}` - Get location config

## WebSocket API

Connect to `/api/builds/ws` for real-time updates:

### Client → Server Messages
```json
{\"type\": \"ping\"}
{\"type\": \"subscribe_build\", \"build_id\": \"uuid\"}
```

### Server → Client Messages
```json
{\"type\": \"initial_status\", \"data\": {...}}
{\"type\": \"status\", \"build_id\": \"uuid\", \"data\": {...}}
{\"type\": \"progress\", \"build_id\": \"uuid\", \"data\": {...}}
{\"type\": \"log\", \"build_id\": \"uuid\", \"data\": {...}}
{\"type\": \"created\", \"build_id\": \"uuid\", \"data\": {...}}
```

## Configuration

Configure via environment variables:

- `OSIMAGER_BASE_DIRECTORY` - Base OSImager directory
- `OSIMAGER_DEBUG` - Enable debug mode
- `OSIMAGER_MAX_CONCURRENT_BUILDS` - Max concurrent builds (default: 3)
- `OSIMAGER_BUILD_TIMEOUT` - Default build timeout in seconds
- `OSIMAGER_CORS_ORIGINS` - Allowed CORS origins

## Testing

Run the test suite:
```bash
pytest tests/
```

With coverage:
```bash
pytest tests/ --cov=api --cov-report=html
```

## Testing the API

### Quick Health Check

Once the server is running, verify it's working:

```bash
# Basic health check
curl http://127.0.0.1:8000/api/health
# Expected: {"status":"healthy","api_version":"1.0.0","build_manager":"running","active_builds":0}

# System information
curl http://127.0.0.1:8000/api/info
# Shows OSImager version, directories, Python version, etc.

# System resource usage
curl http://127.0.0.1:8000/api/status/system
# Shows CPU, memory, disk usage
```

### Specs Management Testing

```bash
# List all available specs
curl http://127.0.0.1:8000/api/specs/
# Returns JSON with specs array and total count

# Get spec names only
curl http://127.0.0.1:8000/api/specs/names
# Returns simple array of spec names

# Get a specific spec (replace 'rhel-9' with any spec name)
curl http://127.0.0.1:8000/api/specs/rhel-9
# Returns complete spec configuration

# Validate a spec
curl -X POST http://127.0.0.1:8000/api/specs/rhel-9/validate
# Returns validation result with errors/warnings

# Create a new spec
curl -X POST http://127.0.0.1:8000/api/specs/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-spec",
    "content": {
      "platforms": ["vmware", "virtualbox"],
      "locations": ["local"],
      "provides": {
        "dist": "ubuntu",
        "versions": ["22.04"],
        "arches": ["amd64"]
      }
    }
  }'

# Copy an existing spec
curl -X POST "http://127.0.0.1:8000/api/specs/rhel-9/copy?target_name=rhel-9-copy"

# Update a spec
curl -X PUT http://127.0.0.1:8000/api/specs/test-spec \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "platforms": ["vmware", "virtualbox", "qemu"],
      "locations": ["local", "datacenter"],
      "provides": {
        "dist": "ubuntu",
        "versions": ["22.04", "24.04"],
        "arches": ["amd64", "arm64"]
      }
    }
  }'

# Delete a spec
curl -X DELETE http://127.0.0.1:8000/api/specs/test-spec
```

### Platforms and Locations

```bash
# List available platforms
curl http://127.0.0.1:8000/api/platforms/
# Returns array of platform names

# Get platform configuration
curl http://127.0.0.1:8000/api/platforms/vmware
# Returns platform JSON configuration

# Get platform info with metadata
curl http://127.0.0.1:8000/api/platforms/vmware/info

# List available locations
curl http://127.0.0.1:8000/api/locations/
# Returns array of location names

# Get location configuration
curl http://127.0.0.1:8000/api/locations/local
# Returns location JSON configuration

# Get location info with metadata
curl http://127.0.0.1:8000/api/locations/local/info
```

### Build Management Testing

```bash
# List all builds
curl http://127.0.0.1:8000/api/builds/
# Returns builds array with metadata

# Filter builds by status
curl "http://127.0.0.1:8000/api/builds/?status=running"
curl "http://127.0.0.1:8000/api/builds/?status=completed"
curl "http://127.0.0.1:8000/api/builds/?status=failed"

# Create a new build (dry run)
curl -X POST http://127.0.0.1:8000/api/builds/ \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "platform": "vmware",
      "location": "local",
      "spec": "rhel-9",
      "debug": true,
      "dry_run": true,
      "variables": {
        "custom_var": "test_value"
      }
    },
    "priority": 5
  }'
# Returns created build with unique ID

# Get specific build (replace BUILD_ID with actual ID)
curl http://127.0.0.1:8000/api/builds/BUILD_ID

# Get build logs
curl http://127.0.0.1:8000/api/builds/BUILD_ID/logs

# Cancel a build
curl -X POST http://127.0.0.1:8000/api/builds/BUILD_ID/cancel
```

### Status and Monitoring

```bash
# Overall system health
curl http://127.0.0.1:8000/api/status/health
# Returns health status for all system components

# Build system status
curl http://127.0.0.1:8000/api/status/build-status
# Returns build manager status and statistics

# Directory status
curl http://127.0.0.1:8000/api/status/directories
# Shows status of OSImager directories

# System resource usage
curl http://127.0.0.1:8000/api/status/system
# CPU, memory, disk usage with timestamps
```

### WebSocket Testing

For real-time build monitoring, connect to the WebSocket endpoint:

```bash
# Using websocat (install with: brew install websocat)
websocat ws://127.0.0.1:8000/api/builds/ws

# Send ping message
echo '{"type": "ping"}' | websocat ws://127.0.0.1:8000/api/builds/ws

# Subscribe to specific build updates
echo '{"type": "subscribe_build", "build_id": "your-build-id"}' | websocat ws://127.0.0.1:8000/api/builds/ws
```

### Interactive Documentation

The best way to test the API is through the interactive documentation:

1. **Swagger UI**: http://127.0.0.1:8000/docs
   - Interactive interface to test all endpoints
   - Built-in request/response examples
   - Authentication handling

2. **ReDoc**: http://127.0.0.1:8000/redoc
   - Clean, comprehensive API documentation
   - Detailed schemas and examples

### Expected Response Examples

#### Health Check Response
```json
{
  "status": "healthy",
  "api_version": "1.0.0",
  "build_manager": "running",
  "active_builds": 0
}
```

#### Specs List Response
```json
{
  "specs": [
    {
      "name": "rhel-9",
      "path": "/Users/steve/src/osimager/core/specs/rhel-9/spec.json",
      "size": 3312,
      "modified": "2025-05-19T21:10:13",
      "created": "2025-06-07T09:12:59.758880"
    }
  ],
  "total": 20
}
```

#### System Status Response
```json
{
  "timestamp": "2025-06-07T19:13:22.690601",
  "cpu": {
    "usage_percent": 7.6,
    "count": 10,
    "load_average": [1.48, 1.98, 2.05]
  },
  "memory": {
    "total": 34359738368,
    "available": 16485187584,
    "used": 16860348416,
    "percent": 52.0
  },
  "disk": {
    "total": 494384795648,
    "used": 67175297024,
    "free": 407623716864,
    "percent": 13.58
  }
}
```

## Architecture

```
api/
├── main.py              # FastAPI app and startup
├── requirements.txt     # Python dependencies
├── run_server.py       # Server startup script
├── models/             # Pydantic data models
│   ├── spec.py
│   └── build.py
├── routers/            # API route handlers
│   ├── specs.py
│   ├── builds.py
│   ├── platforms.py
│   ├── locations.py
│   └── status.py
├── services/           # Business logic
│   ├── spec_service.py
│   └── build_manager.py
├── utils/              # Utilities
│   └── config.py
└── tests/              # Test suite
```

## Development

### Adding New Endpoints

1. Define Pydantic models in `models/`
2. Create business logic in `services/`
3. Add route handlers in `routers/`
4. Include router in `main.py`
5. Add tests in `tests/`

### WebSocket Events

To add new WebSocket event types:

1. Update `BuildWebSocketMessage` model
2. Add event emission in `BuildManager`
3. Handle in frontend client

## Troubleshooting

### Common Issues

**Build manager not starting:**
- Check that CLI tools are accessible
- Verify directory permissions
- Check logs in `osimager-api.log`

**WebSocket connections failing:**
- Ensure firewall allows WebSocket connections
- Check CORS configuration
- Verify network connectivity

**Builds not starting:**
- Check platform/location/spec files exist
- Verify Packer is installed and accessible
- Check build queue status via `/api/status/build-status`

### Logs

- API logs: `osimager-api.log`
- Build logs: Available via API `/api/builds/{id}/logs`
- System logs: Check via `/api/status/system`

## License

Same as OSImager project license.
