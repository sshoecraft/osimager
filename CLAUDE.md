# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OSImager is a comprehensive OS image building and automation system that provides a unified interface for creating virtual machine images across multiple platforms using HashiCorp Packer as the core engine.

## Architecture

### Core Components
- **Python Core Library** (`lib/osimager/`): Central `OSImager` class orchestrating builds
- **FastAPI Backend** (`backend/`): REST API with WebSocket support for real-time monitoring
- **React Frontend** (`frontend/`): Modern TypeScript web interface
- **CLI Tools** (`bin/`): Command-line utilities (mkosimage, rfosimage, mkvenv)
- **Configuration System** (`data/`): Hierarchical JSON configs for platforms/locations/specs

### Data Flow
1. Configuration loading with hierarchical inheritance (platform → location → spec)
2. Advanced variable substitution with vault integration
3. Packer command generation and execution
4. Real-time progress monitoring via WebSocket
5. Ansible-based provisioning and configuration

## Common Development Commands

### Setup and Testing
```bash
# Install dependencies and setup development environment
make dev

# Install Packer plugins (required after updating Packer)
make install-plugins

# Run all tests
make test

# Run configuration validation
make validate

# Code linting and formatting
make lint
make format

# Start development servers (both backend and frontend)
./start-dev.sh
```

### Backend Development
```bash
# Start backend server only
cd backend && python run_server.py

# Run backend tests
cd backend && python -m pytest tests/

# Install backend dependencies
cd backend && pip install -r requirements.txt
```

### Frontend Development
```bash
# Start frontend development server
cd frontend && npm run dev

# Install frontend dependencies
cd frontend && npm install

# Build frontend for production
cd frontend && npm run build
```

### CLI Usage
```bash
# List available specs
python3 bin/mkosimage.py --list

# Build an image (installed version)
mkosimage vmware/lab/rhel-9.0-x86_64

# Build with debug and custom variables
python3 bin/mkosimage.py --debug --define hostname=myserver vmware/lab/rhel-9.0-x86_64

# Dry run to see what would be executed
python3 bin/mkosimage.py --dry vmware/lab/centos-7.9-x86_64
```

## Configuration System

### File Structure
```
data/
├── platforms/          # Virtualization platform configs (vmware.json, virtualbox.json)
├── locations/          # Environment configs (dev.json, lab.json, production.json)
├── specs/             # OS specification configs (rhel/, debian/, windows/)
└── tasks/             # Ansible playbooks for provisioning
```

### Advanced Templating
- `>>variable<<` - Variable substitution
- `%>variable<%` - Alternative variable syntax
- `#>expression<#` - Mathematical expressions
- `|>vault_path<|` - HashiCorp Vault lookups
- `E>condition<E` - Conditional logic
- `[>list_variable<]` - List expansion

### Configuration Inheritance
Configurations merge hierarchically with platform/location/distribution-specific overrides:
1. Base platform configuration
2. Location-specific overrides
3. Spec-specific settings
4. Architecture/version-specific modifications

## Key Files and Their Purpose

### Core Python Library
- `lib/osimager/core.py` - Main OSImager class with build orchestration
- `lib/osimager/utils.py` - Utility functions and helpers
- `lib/osimager/constants.py` - System constants and defaults

### Backend
- `backend/main.py` - FastAPI application setup with CORS and static serving
- `backend/routers/` - API endpoints organized by resource type
- `backend/services/build_manager.py` - Build process management and monitoring
- `backend/models/` - Pydantic models for type-safe API contracts

### Frontend
- `frontend/src/app.tsx` - Main React application component
- `frontend/src/lib/api-client.ts` - Type-safe API client
- `frontend/src/hooks/websocket-hook.ts` - Real-time WebSocket integration
- `frontend/src/components/pages/` - Main application pages

### CLI Tools
- `bin/mkosimage.py` - Primary image building command
- `bin/rfosimage.py` - RetroFit existing images utility
- `bin/mkvenv.py` - Virtual environment management

## Development Workflow

### Adding New Platform Support
1. Create platform JSON in `data/platforms/`
2. Add platform-specific Packer builders
3. Update validation schemas if needed
4. Add platform option to frontend

### Adding New OS Specs
1. Create spec directory in `data/specs/`
2. Define spec.json with OS configuration
3. Add any required Ansible tasks
4. Include kickstart/preseed files as needed

### Testing Changes
1. Run `make validate` to check configuration syntax
2. Use `--dry` flag to test without actual builds
3. Run unit tests with `make test`
4. Test API endpoints at http://localhost:8000/docs

## Web Interface Access

- **Frontend**: http://localhost:3000 (development)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **WebSocket**: ws://localhost:8000/ws for real-time updates

## Troubleshooting

### Common Issues
- **Configuration validation errors**: Run `make validate` to identify syntax issues
- **Missing dependencies**: Run `make install` or check requirements.txt
- **Build failures**: Check logs in build output, use `--debug` flag
- **WebSocket connection issues**: Verify backend server is running on port 8000

### Debugging
- Use `--debug` flag for verbose output
- Check `backend/osimager-api.log` for backend errors
- Frontend console shows WebSocket connection status
- Packer logs are preserved with `--keep` flag

## Security Considerations

- Vault integration for secrets management via `|>vault_path<|` syntax
- Configuration files should not contain plaintext passwords
- Use environment variables or vault for sensitive data
- API endpoints use CORS protection

## Build Process Understanding

1. **Configuration Resolution**: Merge platform + location + spec configs
2. **Variable Substitution**: Process templates including vault lookups
3. **Packer Generation**: Create dynamic Packer JSON configuration
4. **Image Building**: Execute Packer with appropriate builder
5. **Provisioning**: Run Ansible playbooks for configuration
6. **Monitoring**: Real-time progress updates via WebSocket
7. **Artifact Management**: Store completed images per configuration