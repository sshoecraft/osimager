# OSImager - Project Planning & Architecture

## 🎯 Project Overview

OSImager is a comprehensive OS image building and automation system that provides a unified interface for creating virtual machine images across multiple platforms using HashiCorp Packer as the core engine.

## 🏗️ Architecture & Design Principles

### Core Architecture
- **CLI-First Design**: Primary interface through Python CLI tools
- **Configuration-Driven**: JSON-based specs for platforms, locations, and OS configurations
- **Modular Components**: Clear separation between CLI, core logic, and web UI
- **Platform Agnostic**: Support for multiple virtualization platforms

### Key Components

#### 1. CLI Module (`/bin` and `/lib`)
- **Primary Interface**: `bin/mkosimage.py` - main image building tool
- **Utilities**: `bin/rfosimage.py` - RetroFit OS Image utility, `bin/mkvenv.py` - virtual environment management
- **Core Logic**: `lib/osimager/core.py` - main OSImager class and build orchestration
- **Utilities**: `lib/osimager/utils.py` - helper functions and utilities

#### 2. Core Configuration (Root Directory)
- **Platforms**: Define virtualization platforms (VMware, VirtualBox, QEMU, etc.)
- **Locations**: Network and environment-specific configurations
- **Specs**: OS-specific build specifications and provisioning logic
- **Tasks**: Ansible playbooks for OS configuration
- **Files**: Template files and scripts

#### 3. Web UI (`/frontend` and `/api`)
- **Frontend**: Modern React/TypeScript interface with real-time monitoring
- **Backend**: FastAPI server with WebSocket support
- **Legacy**: Original Webix-based editor (deprecated)

#### 4. Installation (`/install.sh`)
- **System Installation**: Complete Linux installer with systemd service

## 🔧 Technology Stack

### Core Technologies
- **Python 3.6+**: Primary development language
- **HashiCorp Packer**: Image building engine
- **Ansible**: Configuration management and provisioning
- **HashiCorp Vault**: Secrets management (optional)

### Dependencies
- **hvac**: Vault client library
- **dnspython**: DNS resolution utilities
- **argparse**: CLI argument parsing
- **json**: Configuration file handling
- **tempfile**: Temporary file management

### Web UI Technologies
- **React**: Modern frontend framework with TypeScript
- **FastAPI**: Python-based backend API server
- **WebSocket**: Real-time communication for build monitoring
- **Tailwind CSS**: Utility-first CSS framework

## 📁 File Structure & Naming Conventions

### Directory Structure
```
osimager/
├── bin/                   # Command-line interface programs
│   ├── mkosimage.py       # Main CLI script
│   ├── rfosimage.py       # RetroFit OS Image utility
│   └── mkvenv.py          # Virtual environment manager
├── lib/                   # Python libraries
│   └── osimager/          # OSImager Python package
│       ├── __init__.py
│       ├── core.py        # Main OSImager class
│       ├── constants.py   # Constants and configuration
│       └── utils.py       # Utility functions
├── platforms/             # Platform definitions
├── locations/             # Location configurations
├── specs/                # OS specifications
├── tasks/                # Ansible playbooks
├── files/                # Template files
├── install/              # Installation-specific files
├── api/                  # FastAPI backend server
├── frontend/             # Modern React/TypeScript web interface
├── logs/                 # Log files
│   ├── backend.log       # API server logs
│   ├── frontend.log      # Frontend dev server logs
│   ├── cli.log          # CLI operation logs
│   └── builds.log       # Build process logs
├── osimager.conf        # Main configuration file
├── osimager_config.py   # Configuration module
├── install.sh           # Linux installer script
└── old/                 # Legacy/deprecated components
```

### Naming Conventions
- **Files**: lowercase with underscores (snake_case)
- **Classes**: PascalCase (e.g., `OSImager`)
- **Functions**: snake_case (e.g., `make_build`)
- **Variables**: snake_case (e.g., `platform_name`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)

## 🎨 Code Style & Standards

### Python Standards
- **PEP8 Compliance**: Follow PEP8 style guidelines
- **Type Hints**: Use type hints for function parameters and returns
- **Black Formatting**: Use Black code formatter
- **Docstrings**: Google-style docstrings for all functions and classes
- **Max Line Length**: 500 lines per file (refactor if exceeded)

### Documentation Standards
- **README.md**: Project overview and setup instructions
- **Inline Comments**: Explain complex logic with `# Reason:` comments
- **Function Documentation**: Document parameters, returns, and exceptions

## 🧪 Testing Strategy

### Unit Testing
- **Framework**: pytest
- **Coverage**: Minimum 80% code coverage
- **Test Types**: 
  - Expected use cases
  - Edge cases
  - Failure scenarios
- **Test Location**: `/tests` directory mirroring main structure

### Integration Testing
- **Packer Integration**: Test image building workflows
- **Platform Testing**: Verify platform-specific configurations
- **End-to-end**: Complete build cycle testing

## 🚀 Build & Development Workflow

### Development Environment
- **Python Virtual Environment**: Use venv for dependency isolation
- **Configuration**: `~/.config/osimager/` for user settings
- **Base Directory**: `/opt/osimager` for system installation

### Build Process
1. **Spec Selection**: Choose platform/location/spec combination
2. **Configuration Loading**: Load and merge JSON configurations
3. **Variable Substitution**: Process templates and variables
4. **Packer Execution**: Generate Packer JSON and execute build
5. **Provisioning**: Run Ansible playbooks for OS configuration

## 🔒 Security & Constraints

### Security Considerations
- **Vault Integration**: Optional HashiCorp Vault for secrets
- **Network Isolation**: Support for local-only builds
- **Credential Management**: Secure handling of platform credentials

### Constraints
- **Platform Dependencies**: Requires Packer and platform-specific tools
- **Network Requirements**: Internet access for ISO downloads (unless local-only)
- **Resource Requirements**: Sufficient disk space and memory for image builds

## 🎯 Current Goals & Priorities

### Phase 1: Code Organization & Testing
- Implement comprehensive unit test coverage
- Refactor large files to meet 500-line limit
- Add type hints throughout codebase
- Improve error handling and logging

### Phase 2: Documentation & Usability
- Create comprehensive README.md
- Add setup and configuration guides
- Improve CLI help and documentation
- Add example configurations

### Phase 3: Feature Enhancement
- Expand platform support
- Improve web UI functionality
- Add advanced networking features
- Enhance Vault integration

## 📊 Success Metrics

- **Reliability**: 99%+ successful builds for tested configurations
- **Performance**: Build times within acceptable ranges per platform
- **Maintainability**: Clear code structure and comprehensive tests
- **Usability**: Intuitive CLI and web interfaces
