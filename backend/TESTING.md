# OSImager API - Quick Testing Reference

## Server Status
```bash
# Health check
curl http://127.0.0.1:8000/api/health

# System information  
curl http://127.0.0.1:8000/api/info

# System resources
curl http://127.0.0.1:8000/api/status/system

# Build system status
curl http://127.0.0.1:8000/api/status/build-status

# Directory status
curl http://127.0.0.1:8000/api/status/directories
```

## Specs Management
```bash
# List all specs
curl http://127.0.0.1:8000/api/specs/

# Get spec names only
curl http://127.0.0.1:8000/api/specs/names

# Get specific spec
curl http://127.0.0.1:8000/api/specs/rhel-9

# Validate spec
curl -X POST http://127.0.0.1:8000/api/specs/rhel-9/validate
```

## Platforms & Locations
```bash
# List platforms
curl http://127.0.0.1:8000/api/platforms/

# Get platform config
curl http://127.0.0.1:8000/api/platforms/vmware

# List locations  
curl http://127.0.0.1:8000/api/locations/

# Get location config
curl http://127.0.0.1:8000/api/locations/local
```

## Build Management
```bash
# List builds
curl http://127.0.0.1:8000/api/builds/

# Filter by status
curl "http://127.0.0.1:8000/api/builds/?status=running"

# Create dry run build
curl -X POST http://127.0.0.1:8000/api/builds/ \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "platform": "vmware",
      "location": "local", 
      "spec": "rhel-9",
      "debug": true,
      "dry_run": true
    },
    "priority": 5
  }'
```

## Interactive Documentation
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## WebSocket Testing
```bash
# Install websocat first: brew install websocat
websocat ws://127.0.0.1:8000/api/builds/ws

# Send ping
echo '{"type": "ping"}' | websocat ws://127.0.0.1:8000/api/builds/ws
```

## Verified Test Results (2025-06-07)
✅ Health: `{"status":"healthy","api_version":"1.0.0","build_manager":"running","active_builds":0}`
✅ Specs: Found 20 specs (alma-8, rhel-9, centos-7, etc.)
✅ System: CPU 7.6%, Memory 52%, Disk 13.6%
✅ Server: Running on http://127.0.0.1:8000
