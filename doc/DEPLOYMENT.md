# OSImager Deployment Guide

This document covers the deployment process for OSImager to remote servers, including the lessons learned from the vserv deployment and best practices for future deployments.

## Overview

OSImager can be deployed to remote Linux servers using either the packaged installer or manual deployment scripts. This guide documents both approaches and troubleshooting steps.

## Deployment Methods

### Method 1: Packaged Installation (Recommended)

The standard approach uses the packaged tar.gz file created by the `package.sh` script:

```bash
# Create package locally
./package.sh

# Deploy using automated script
./deploy_to_vserv.sh
```

### Method 2: Manual Deployment (Fallback)

When the packaged installer has issues, use the manual deployment script:

```bash
# Use manual deployment script
./manual_deploy.sh
```

## Deployment Scripts

### 1. deploy_to_vserv.sh

Automated deployment script that:
- Tests SSH connectivity
- Copies package and checksums to remote server
- Verifies package integrity
- Runs the packaged installer
- Validates installation
- Provides access information

### 2. manual_deploy.sh

Manual deployment script that:
- Creates directory structure manually
- Copies all components individually
- Creates Python virtual environment
- Installs dependencies
- Creates systemd service
- Sets up CLI wrapper scripts
- Configures admin tools

## vserv Deployment (2025-06-14)

### Issues Encountered

1. **Corrupted Installer**: The packaged install.sh was incomplete/corrupted
2. **Import Path Issues**: Python modules couldn't find each other due to path configuration
3. **Missing Dependencies**: Required packages not installed in virtual environment
4. **CLI Script Paths**: CLI wrapper scripts used wrong module import syntax

### Solutions Applied

1. **Manual Component Copy**: Used manual_deploy.sh to copy components individually
2. **PYTHONPATH Configuration**: Added proper PYTHONPATH to systemd service
3. **Dependency Installation**: Installed missing packages:
   - `pydantic-settings`
   - `psutil`
4. **CLI Script Fix**: Updated wrapper scripts to use direct .py file paths instead of module imports

### Final Configuration

**Installation Directory**: `/opt/osimager/`

**Directory Structure**:
```
/opt/osimager/
├── api/              # FastAPI backend
├── cli/              # CLI modules  
├── frontend/         # React frontend (dist)
├── platforms/        # Platform configs
├── locations/        # Location configs
├── specs/           # OS specifications
├── tasks/           # Ansible tasks
├── files/           # Install files
├── install/         # Install directories
├── etc/             # Configuration files
├── logs/            # Log files
├── venv/            # Python virtual environment
└── bin/             # Binary/script files
```

**Systemd Service**: `/etc/systemd/system/osimager.service`

**CLI Commands**: Available system-wide
- `/usr/local/bin/mkosimage`
- `/usr/local/bin/rfosimage`
- `/usr/local/bin/mkvenv`
- `/usr/local/bin/osimager-admin`

## Access Information

### vserv Deployment
- **Web Interface**: http://192.168.1.3:8000
- **API Documentation**: http://192.168.1.3:8000/docs
- **Health Check**: http://192.168.1.3:8000/api/status/health

### Service Management
```bash
# Check service status
osimager-admin status
systemctl status osimager

# View logs
osimager-admin logs
journalctl -u osimager -f

# Restart service
osimager-admin restart
systemctl restart osimager
```

### CLI Usage
```bash
# List available specs
mkosimage --list

# Create an image
mkosimage vsphere/lab/centos-6 hostname 192.168.1.100

# Retrofit existing image
rfosimage vsphere/lab/centos-6 existing-template

# Create virtual environment
mkvenv python-version requirements.txt
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check logs for specific error
journalctl -u osimager --no-pager -n 20

# Common causes:
# - Missing Python dependencies
# - Import path issues
# - Configuration file not found
# - Port already in use
```

#### 2. Import Errors
```bash
# Check PYTHONPATH in service
systemctl cat osimager

# Should include:
Environment=PYTHONPATH=/opt/osimager:/opt/osimager/api:/opt/osimager/cli
```

#### 3. Missing Dependencies
```bash
# Install in virtual environment
source /opt/osimager/venv/bin/activate
pip install package-name
systemctl restart osimager
```

#### 4. Web Interface Not Loading
```bash
# Check if frontend files exist
ls -la /opt/osimager/frontend/

# Check if API is responding
curl http://localhost:8000/api/status/system

# Check asset serving
curl http://localhost:8000/assets/
```

#### 5. CLI Commands Not Working
```bash
# Check CLI script syntax
cat /usr/local/bin/mkosimage

# Should use direct .py file paths, not module imports:
# ✓ Correct:   python3 cli/osimager/scripts/mkosimage.py
# ✗ Incorrect: python3 -m osimager.scripts.mkosimage

# Test CLI directly
cd /opt/osimager && source venv/bin/activate && python3 cli/osimager/scripts/mkosimage.py --version
```

### Package Issues

If the packaged installer is corrupted:

1. **Use Manual Deployment**: Switch to `manual_deploy.sh`
2. **Rebuild Package**: Run `./package.sh` with fresh checkout
3. **Check Tar Warnings**: macOS extended attributes cause warnings but don't break functionality

### Import Path Issues

For Python import problems:

1. **Check PYTHONPATH**: Ensure service has correct paths
2. **Use Absolute Imports**: Prefer absolute over relative imports
3. **Add __init__.py**: Ensure all packages have init files

## Best Practices

### Pre-Deployment Checklist

- [ ] Test package locally with `./package.sh --test-only`
- [ ] Verify SSH access to target server
- [ ] Check target server has required dependencies (Python 3.6+, pip, etc.)
- [ ] Ensure target server has sufficient disk space (>500MB)
- [ ] Backup existing installations if upgrading

### Post-Deployment Verification

- [ ] Service is running: `systemctl status osimager`
- [ ] Web interface loads: `curl http://server:8000/`
- [ ] API responds: `curl http://server:8000/api/status/system`
- [ ] CLI commands work: `mkosimage --version`
- [ ] Health checks pass: `curl http://server:8000/api/status/health`

### Security Considerations

- [ ] Configure firewall rules for port 8000
- [ ] Use HTTPS in production (reverse proxy)
- [ ] Restrict SSH access to deployment keys
- [ ] Set appropriate file permissions (755 for binaries, 644 for configs)
- [ ] Consider running service as non-root user

## Future Improvements

### Packaging
- Fix install.sh corruption issue in package.sh
- Include dependency pre-check in installer
- Add rollback capability to installer

### Deployment
- Create Ansible playbook for multi-server deployment
- Add Docker containerization option
- Implement blue-green deployment strategy

### Monitoring
- Add deployment health monitoring
- Create automated deployment testing
- Implement log aggregation for multiple servers

## Files Created

This deployment process created the following new files:

1. **deploy_to_vserv.sh** - Automated deployment script
2. **manual_deploy.sh** - Manual fallback deployment script
3. **DEPLOYMENT.md** - This documentation file

All files are located in the project root directory and should be maintained alongside the main OSImager codebase.
