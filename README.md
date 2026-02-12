# OSImager

OSImager is a comprehensive OS image building and automation system that provides a unified interface for creating virtual machine images across multiple platforms using HashiCorp Packer as the core engine.

## 🎯 Features

- **Multi-Platform Support**: VMware, VirtualBox, QEMU, libvirt, Proxmox, vSphere, Hyper-V
- **OS Coverage**: RHEL, CentOS, AlmaLinux, Rocky Linux, Oracle Linux (OEL), Debian, Ubuntu, SLES, Windows
- **Automated Provisioning**: Ansible-based configuration management
- **Secrets Management**: HashiCorp Vault integration
- **Web Interface**: Visual spec editor using Webix framework
- **Network Management**: IP pool management and DNS integration
- **Flexible Configuration**: JSON-based platform, location, and spec definitions

## 🚀 Quick Start

### Prerequisites

- Python 3.6 or higher
- HashiCorp Packer
- Ansible (for provisioning)
- Virtualization platform (VMware, VirtualBox, etc.)
- **mkisofs** (from cdrtools) - required for creating kickstart CD images. On macOS: `brew install cdrtools`. On Linux: install `cdrtools` or `genisoimage` from your package manager. Without this, Packer falls back to macOS `hdiutil` which creates hybrid ISOs with Mac partition tables that Linux installers cannot mount.

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sshoecraft/OSImager.git
   cd OSImager
   ```

2. **Install Python dependencies** (if developing):
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Quick Setup** (recommended):
   ```bash
   # For Linux production installation:
   sudo ./install.sh
   
   # For development:
   ./start-dev.sh
   ```

### Basic Usage

1. **List available specs**:
   ```bash
   python3 bin/mkosimage.py --list
   # or if installed via install.sh:
   mkosimage --list
   ```

2. **Build an image**:
   ```bash
   python3 bin/mkosimage.py platform/location/spec
   # or if installed:
   mkosimage platform/location/spec
   ```

   Example:
   ```bash
   mkosimage vmware/lab/rhel-9.0-x86_64
   ```

## 📁 Project Structure

```
osimager/
├── bin/                   # Command-line interface programs
│   ├── mkosimage.py       # Main CLI script
│   ├── rfosimage.py       # RetroFit OS Image utility
│   └── mkvenv.py          # Virtual environment manager
├── lib/                   # Python libraries
│   └── osimager/          # OSImager Python package
│       ├── core.py        # Main OSImager class
│       ├── utils.py       # Utility functions
│       └── constants.py   # Constants and configuration
├── platforms/             # Platform definitions
├── locations/             # Location configurations
├── specs/                # OS specifications
├── tasks/                # Ansible playbooks
├── files/                # Template files
├── install/              # Installation-specific files
├── backend/              # FastAPI backend server
├── frontend/             # Modern React/TypeScript web interface
├── logs/                 # Log files (configurable)
│   ├── backend.log       # Backend server logs
│   ├── frontend.log      # Frontend dev server logs
│   └── builds.log       # Build process logs
├── osimager.conf        # Main configuration file
├── osimager_config.py   # Configuration module
└── install.sh           # Linux installer script
```

## ⚙️ Configuration

### Settings File

OSImager stores settings in `~/.config/osimager/settings.json`:

```json
{
    "packer_cmd": "packer",
    "base_dir": "/opt/osimager",
    "packer_cache_dir": "/tmp",
    "local_only": false
}
```

### Platform Configuration

Define virtualization platforms in `data/platforms/`:

```json
{
    "type": "vmware-vmx",
    "guest_os_type": "rhel8-64",
    "memory": 2048,
    "cpus": 2,
    "disk_size": 20480
}
```

### Location Configuration

Define network environments in `data/locations/`:

```json
{
    "platforms": ["vmware", "virtualbox"],
    "defs": {
        "domain": "example.com",
        "dns": {
            "servers": ["8.8.8.8", "8.8.4.4"]
        },
        "ntp": {
            "servers": ["pool.ntp.org"]
        }
    }
}
```

## 🔧 CLI Reference

### mkosimage

Main image building command:

```bash
python3 bin/mkosimage.py [OPTIONS] PLATFORM/LOCATION/SPEC
# or if installed:
mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC
```

**Options**:
- `-l, --list`: List available specs with dist-version-arch details
- `-a, --avail`: Only list specs where ISO is present
- `-d, --debug`: Enable debug mode
- `-v, --verbose`: Enable verbose output
- `-f, --force`: Force rebuild
- `-k, --keep`: Keep temporary files
- `-n, --dry`: Dry run (show commands without executing)
- `-D, --define KEY=VALUE`: Define custom variables
- `-F, --fqdn FQDN`: Set fully qualified domain name
- `--local-only`: Use local ISO files instead of downloading

**Examples**:
```bash
# List all available specs (shows dist-version-arch combinations)
mkosimage --list

# Build RHEL 9.0 x86_64 on VMware in lab environment
mkosimage vmware/lab/rhel-9.0-x86_64

# Build with custom variables and hostname
mkosimage --define hostname=myserver --fqdn myserver.example.com vmware/lab/rhel-9.0-x86_64

# Dry run to see what would be executed
mkosimage --dry vmware/lab/rhel-9.0-x86_64

# Use local ISO instead of downloading
mkosimage --local-only vmware/lab/centos-7.9-x86_64
```

### rfosimage

RetroFit OS Image utility for updating and modifying existing images without complete rebuilds:

```bash
python3 bin/rfosimage.py [OPTIONS] IMAGE_PATH [RETROFIT_SPEC]
# or if installed:
rfosimage [OPTIONS] IMAGE_PATH [RETROFIT_SPEC]
```

### mkvenv

Virtual environment management utility:

```bash
python3 bin/mkvenv.py [OPTIONS] ENV_NAME
# or if installed:
mkvenv [OPTIONS] ENV_NAME
```

## 🌐 Web Interface

OSImager provides two web interfaces:

### Modern React Frontend (Recommended)

A modern, responsive web application built with React and TypeScript:

**Features**:
- 📊 **Real-time Dashboard**: Live system overview and build monitoring
- 🚀 **Build Management**: Complete build lifecycle with real-time progress
- 🔄 **Live Updates**: WebSocket-based real-time status updates
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile
- 🎯 **Type Safety**: Full TypeScript implementation

**Quick Start**:
```bash
# Start both backend and frontend
./start-dev.sh

# Or start individually:
# Backend: cd backend && python run_server.py
# Frontend: cd frontend && npm run dev
```

**Access**:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Backend Documentation**: http://localhost:8000/docs

### Legacy Webix Interface

Original web interface using Webix framework:

**Access**: Open `http://localhost:8000` in a web browser (modern React interface)

**Features**:
- **Spec Editor**: Visual editor for OS specifications
- **Configuration Management**: Basic JSON configuration editing
- **Legacy Support**: Maintained for backward compatibility

## 🔐 Vault Integration

OSImager supports HashiCorp Vault for secrets management. Configure vault access in `data/.vaultconfig`:

```
addr=https://vault.example.com:8200
token=your-vault-token
```

## 🧪 Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Formatting

```bash
black lib/osimager/
```

### Type Checking

```bash
mypy lib/osimager/
```

### Development Setup

1. **Clone and setup**:
   ```bash
   git clone https://github.com/sshoecraft/OSImager.git
   cd OSImager
   ```

2. **Run development servers**:
   ```bash
   ./start-dev.sh  # Starts both backend and frontend
   ```

3. **Test CLI tools**:
   ```bash
   python3 bin/mkosimage.py --list
   python3 bin/mkosimage.py --help
   ```

## 📚 Documentation

- [PLANNING.md](PLANNING.md): Project architecture and design principles
- [TASK.md](TASK.md): Current development tasks and roadmap
- [DEPLOYMENT.md](DEPLOYMENT.md): Deployment guide and remote server setup
- [CONFIGURATION.md](CONFIGURATION.md): Detailed configuration format documentation
- [INSTALL.md](INSTALL.md): Linux installation guide and system requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/sshoecraft/OSImager/issues)
- **Documentation**: See docs/ directory
- **Community**: [GitHub Discussions](https://github.com/sshoecraft/OSImager/discussions)

## 🔄 Version History

- **0.1.0**: Initial release with basic Packer integration
- **Current**: Active development - see TASK.md for roadmap
