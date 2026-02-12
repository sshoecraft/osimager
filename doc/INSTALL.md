# OSImager Linux Installation Guide

This guide covers the complete installation process for OSImager on Linux systems.

## Quick Start

```bash
# 1. Download or clone OSImager
git clone https://github.com/sshoecraft/OSImager.git
cd OSImager

# 2. Run setup (installs dependencies)
sudo ./setup.sh

# 3. Run installer
sudo ./install.sh

# 4. Access web interface
firefox http://localhost:8000
```

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 18.04+, RHEL/CentOS 7+, Debian 10+, SUSE 15+)
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB free space
- **Network**: Internet access for downloads

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 100+ GB free space (for image builds)
- **Network**: High-speed internet

### Required Software
- Python 3.6+
- Node.js 16+ (installed automatically)
- systemd (for service management)

### Optional Software
- HashiCorp Packer (installed automatically)
- Ansible (installed automatically)
- HashiCorp Vault (for secrets management)

## Installation Options

### Standard Installation

```bash
sudo ./install.sh
```

This installs OSImager to `/opt/osimager` with default settings.

### Custom Installation

```bash
# Custom installation directory
sudo ./install.sh --install-dir /usr/local/osimager

# Custom port
sudo ./install.sh --port 9000

# Custom service user
sudo ./install.sh --user myuser

# Combined options
sudo ./install.sh --install-dir /home/osimager --port 8080 --user osimager
```

### Environment Variables

```bash
# Override installation directory
export OSIMAGER_INSTALL_DIR=/custom/path
sudo ./install.sh
```

## Installation Process

The installer performs these steps:

1. **System Check**: Verifies requirements and dependencies
2. **User Creation**: Creates dedicated service user
3. **Directory Setup**: Creates installation directory structure
4. **Python Package**: Installs OSImager in virtual environment
5. **CLI Tools**: Installs command-line utilities
6. **Data Files**: Copies platform specs and configurations
7. **Web UI**: Builds and installs React frontend
8. **Configuration**: Sets up configuration files
9. **Service Setup**: Creates systemd service
10. **Logging**: Configures log rotation
11. **Firewall**: Opens required ports
12. **Service Start**: Starts OSImager service

## Directory Structure

After installation:

```
/opt/osimager/
├── bin/                    # CLI executables
│   ├── mkosimage          # Image creation tool
│   ├── rfosimage          # Image modification tool
│   └── mkvenv             # Virtual environment manager
├── data/                   # Configuration data
│   ├── platforms/         # Platform definitions
│   ├── locations/         # Location configurations
│   ├── specs/            # OS specifications
│   └── builds/           # Build outputs
├── ui/                    # Web interface
│   ├── index.html        # Main page
│   ├── assets/           # CSS, JS, images
│   └── favicon.svg       # Icon
├── lib/                   # Libraries and code
│   ├── python/           # Python virtual environment
│   └── api/              # FastAPI backend
├── logs/                  # Log files
│   ├── api.log           # API server logs
│   ├── service.log       # System service logs
│   ├── cli.log           # CLI operation logs
│   └── builds.log        # Build process logs
└── etc/                   # Configuration files
    ├── osimager.conf     # Main configuration
    └── api.conf          # API configuration
```

## Service Management

### Service Commands

```bash
# Check service status
sudo systemctl status osimager

# Start service
sudo systemctl start osimager

# Stop service
sudo systemctl stop osimager

# Restart service
sudo systemctl restart osimager

# Enable auto-start
sudo systemctl enable osimager

# Disable auto-start
sudo systemctl disable osimager

# View service logs
sudo journalctl -u osimager -f
```

### Log Files

```bash
# View API logs
sudo tail -f /opt/osimager/logs/api.log

# View service logs
sudo tail -f /opt/osimager/logs/service.log

# View build logs
sudo tail -f /opt/osimager/logs/builds.log

# View all logs
sudo tail -f /opt/osimager/logs/*.log
```

## CLI Usage

After installation, CLI tools are available system-wide:

```bash
# Create an OS image
mkosimage --platform vmware --location lab --spec rhel8

# List available configurations
mkosimage --list

# Get help
mkosimage --help

# Modify existing image
rfosimage --image myimage.vmdk --patch security-updates

# Manage virtual environments
mkvenv --create myenv
```

## Web Interface

The web interface is available at:
- Local: http://localhost:8000
- Network: http://YOUR_IP:8000

### Features
- **Dashboard**: System overview and build monitoring
- **Builds**: Build history and management
- **Platforms**: Platform configuration
- **Locations**: Location management
- **Specs**: OS specification editing
- **Settings**: System configuration

## Configuration

### Main Configuration

Edit `/opt/osimager/etc/osimager.conf`:

```ini
[global]
base_dir = /opt/osimager
data_dir = /opt/osimager/data
log_dir = /opt/osimager/logs
host = 0.0.0.0
port = 8000
web_root = /opt/osimager/ui

[logging]
log_level = info
log_file = /opt/osimager/logs/osimager.log

[build]
build_timeout = 7200
concurrent_builds = 2
```

### API Configuration

Edit `/opt/osimager/etc/api.conf`:

```ini
[api]
host = 0.0.0.0
port = 8000
debug = false
data_dir = /opt/osimager/data
log_file = /opt/osimager/logs/api.log
static_dir = /opt/osimager/ui
```

## Network Access

### Firewall Configuration

The installer automatically configures common firewalls:

```bash
# FirewallD (RHEL/CentOS/Fedora)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# UFW (Ubuntu/Debian)
sudo ufw allow 8000/tcp

# iptables (manual)
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### Remote Access

To access from other machines:
1. Ensure firewall allows port 8000
2. Use server's IP address: http://SERVER_IP:8000
3. Configure host in `/opt/osimager/etc/osimager.conf` if needed

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status osimager

# View detailed logs
sudo journalctl -u osimager --no-pager

# Check configuration
sudo -u osimager /opt/osimager/lib/python/venv/bin/python -m uvicorn api.main:app --check

# Test manually
sudo -u osimager /opt/osimager/lib/python/venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --app-dir /opt/osimager/lib
```

### Port Already in Use

```bash
# Find process using port
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000

# Kill process
sudo kill -9 PID

# Or change port in configuration
sudo vim /opt/osimager/etc/osimager.conf
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R osimager:osimager /opt/osimager

# Fix permissions
sudo chmod -R 755 /opt/osimager
sudo chmod -R 750 /opt/osimager/logs /opt/osimager/etc
```

### Web Interface Not Loading

```bash
# Check if service is running
sudo systemctl status osimager

# Check if port is accessible
curl http://localhost:8000

# Check frontend files
ls -la /opt/osimager/ui/

# Rebuild frontend
cd /path/to/source/frontend
npm run build
sudo cp -r dist/* /opt/osimager/ui/
sudo chown -R osimager:osimager /opt/osimager/ui
```

### Build Failures

```bash
# Check build logs
sudo tail -f /opt/osimager/logs/builds.log

# Check Packer installation
packer version

# Check Ansible installation
ansible --version

# Test build manually
sudo -u osimager mkosimage --platform test --location local --spec minimal
```

## Uninstallation

### Complete Removal

```bash
# Uninstall OSImager
sudo ./install.sh --uninstall

# Remove dependencies (optional)
sudo apt remove python3-pip python3-venv  # Ubuntu/Debian
sudo yum remove python3-pip               # RHEL/CentOS
```

### Partial Removal

```bash
# Stop and disable service
sudo systemctl stop osimager
sudo systemctl disable osimager

# Remove service file
sudo rm /etc/systemd/system/osimager.service
sudo systemctl daemon-reload

# Remove CLI links
sudo rm /usr/local/bin/{mkosimage,rfosimage,mkvenv}

# Remove desktop entry
sudo rm /usr/share/applications/osimager.desktop
```

## Updates

### Updating OSImager

```bash
# Download new version
git pull origin main

# Stop service
sudo systemctl stop osimager

# Run installer (preserves data)
sudo ./install.sh

# Start service
sudo systemctl start osimager
```

### Backing Up Data

```bash
# Backup configuration and data
sudo tar -czf osimager-backup-$(date +%Y%m%d).tar.gz \
  /opt/osimager/data \
  /opt/osimager/etc \
  /opt/osimager/logs

# Restore backup
sudo tar -xzf osimager-backup-YYYYMMDD.tar.gz -C /
```

## Security Considerations

### Service User
- OSImager runs as dedicated `osimager` user
- No shell access for security
- Limited filesystem permissions

### Network Security
- Change default port if needed
- Use firewall to restrict access
- Consider reverse proxy for HTTPS

### File Permissions
- Configuration files: 640 (owner read/write, group read)
- Log files: 644 (owner read/write, group/other read)
- Executables: 755 (owner read/write/execute, group/other read/execute)

## Support

### Getting Help
- Documentation: Check `/opt/osimager/ui/` for built-in help
- Logs: Check `/opt/osimager/logs/` for error details
- GitHub: Report issues at https://github.com/sshoecraft/OSImager

### Community
- Submit bug reports and feature requests on GitHub
- Contribute improvements via pull requests
- Share configurations and tips in discussions
