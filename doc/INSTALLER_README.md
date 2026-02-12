# OSImager Linux Installer

This installer provides a complete automated installation of OSImager on Linux systems.

## Quick Install

```bash
# Clone the repository
git clone https://github.com/sshoecraft/OSImager.git
cd OSImager

# Install dependencies (optional - installer will handle this)
sudo ./setup.sh

# Install OSImager
sudo ./install.sh

# Access web interface
firefox http://localhost:8000
```

## What Gets Installed

### Installation Layout (`/opt/osimager/`)

```
/opt/osimager/
├── bin/                    # Executable programs
│   ├── mkosimage          # Main image building CLI
│   ├── rfosimage          # Image modification CLI  
│   ├── mkvenv             # Virtual environment manager
│   └── osimager-admin     # Administration tool
├── data/                   # Configuration and build data
│   ├── platforms/         # Platform definitions (VMware, VirtualBox, etc.)
│   ├── locations/         # Location configurations (lab, prod, etc.)
│   ├── specs/            # OS specifications (RHEL, Ubuntu, etc.)
│   └── builds/           # Build outputs and artifacts
├── ui/                    # Web interface files
│   ├── index.html        # Main web page
│   ├── assets/           # CSS, JavaScript, images
│   └── favicon.svg       # Application icon
├── lib/                   # Libraries and backend code
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

### System Integration

- **Systemd Service**: Auto-starts OSImager on boot
- **CLI Tools**: Available system-wide (`mkosimage`, `rfosimage`, `mkvenv`)
- **Admin Tool**: Management utility (`osimager-admin`)
- **Desktop Entry**: GUI shortcut for web interface
- **Firewall**: Automatic port configuration
- **Log Rotation**: Automatic log management
- **Security**: Dedicated service user with minimal privileges

## Installation Options

### Default Installation
```bash
sudo ./install.sh
```
- Install location: `/opt/osimager`
- Web port: `8000`
- Service user: `osimager`

### Custom Installation
```bash
# Custom directory
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
export OSIMAGER_INSTALL_DIR=/custom/path
sudo ./install.sh
```

## Dependencies

### Automatically Installed
- **Node.js 18+** (for React frontend)
- **Python packages** (FastAPI, uvicorn, etc.)
- **HashiCorp Packer** (image building engine)
- **Ansible** (configuration management)

### System Requirements
- **Linux** (Ubuntu 18.04+, RHEL/CentOS 7+, Debian 10+, SUSE 15+)
- **Python 3.6+**
- **systemd**
- **2GB+ RAM**
- **10GB+ disk space**

## Usage After Installation

### Web Interface
- **Local**: http://localhost:8000
- **Network**: http://YOUR_IP:8000

### Command Line Tools
```bash
# Create an OS image
mkosimage --platform vmware --location lab --spec rhel8

# List available configurations  
mkosimage --list

# Modify existing image
rfosimage --image myimage.vmdk --patch security-updates

# Administration
osimager-admin status
osimager-admin logs
osimager-admin restart
osimager-admin backup
```

### Service Management
```bash
# Check status
sudo systemctl status osimager

# Restart service
sudo systemctl restart osimager

# View logs
sudo journalctl -u osimager -f

# Stop/start
sudo systemctl stop osimager
sudo systemctl start osimager
```

## Configuration

### Main Configuration (`/opt/osimager/etc/osimager.conf`)
```ini
[global]
base_dir = /opt/osimager
data_dir = /opt/osimager/data
log_dir = /opt/osimager/logs
host = 0.0.0.0
port = 8000

[build]
build_timeout = 7200
concurrent_builds = 2
```

### Log Files
- **API logs**: `/opt/osimager/logs/api.log`
- **Service logs**: `/opt/osimager/logs/service.log`  
- **Build logs**: `/opt/osimager/logs/builds.log`
- **CLI logs**: `/opt/osimager/logs/cli.log`

## Network Access

### Local Access
Web interface available at `http://localhost:8000`

### Remote Access
1. Web interface available at `http://YOUR_IP:8000`
2. Firewall automatically configured for port 8000
3. Configure custom port if needed: `--port NNNN`

### Security
- Service runs as dedicated `osimager` user
- Minimal filesystem permissions
- systemd security hardening enabled
- No remote shell access for service user

## Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status osimager

# View detailed logs
sudo journalctl -u osimager --no-pager

# Test configuration
sudo -u osimager /opt/osimager/lib/python/venv/bin/python -c "import api.main"
```

### Port Already in Use
```bash
# Find process using port
sudo netstat -tlnp | grep :8000

# Kill conflicting process
sudo kill -9 PID

# Or install on different port
sudo ./install.sh --port 9000
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R osimager:osimager /opt/osimager

# Fix permissions  
sudo chmod -R 755 /opt/osimager
```

### Web Interface Not Loading
```bash
# Check if service is running
sudo systemctl status osimager

# Test web response
curl http://localhost:8000

# Rebuild frontend if needed
cd frontend && npm run build
sudo cp -r dist/* /opt/osimager/ui/
```

## Uninstallation

### Complete Removal
```bash
sudo ./install.sh --uninstall
```

This will:
- Stop and disable the service
- Remove all files (with confirmation)
- Remove CLI tools and desktop entries
- Remove firewall rules
- Remove service user

### Partial Removal
```bash
# Stop service only
sudo systemctl stop osimager
sudo systemctl disable osimager

# Keep data but remove service
sudo rm /etc/systemd/system/osimager.service
sudo systemctl daemon-reload
```

## Upgrading

### Update Installation
```bash
# Pull latest code
git pull origin main

# Stop service
sudo systemctl stop osimager

# Reinstall (preserves data)
sudo ./install.sh

# Service automatically restarted
```

### Backup Before Upgrade
```bash
# Create backup
osimager-admin backup

# Or manual backup
sudo tar -czf osimager-backup.tar.gz /opt/osimager/data /opt/osimager/etc
```

## Development Mode

### Local Development
```bash
# Install in development mode
sudo ./install.sh --install-dir /home/developer/osimager --user developer

# Or run from source without installing
cd api && python -m uvicorn main:app --reload
cd frontend && npm run dev
```

## Support

### Getting Help
- **Documentation**: Built-in help at http://localhost:8000/docs
- **Logs**: Check `/opt/osimager/logs/` for error details
- **GitHub**: Report issues at https://github.com/sshoecraft/OSImager
- **Admin Tool**: Run `osimager-admin status` for system overview

### Common Issues
- **Port conflicts**: Use `--port` option for different port
- **Permission errors**: Check service user ownership
- **Build failures**: Verify Packer and Ansible installation
- **Network issues**: Check firewall configuration

## Contributing

### Testing the Installer
```bash
# Test installer syntax
./test-installer.sh

# Test in VM or container
docker run -it --privileged ubuntu:20.04
# Install git, then clone and test
```

### Reporting Issues
Include in bug reports:
- Operating system and version
- Installation command used
- Error messages from logs
- Output of `osimager-admin status`
