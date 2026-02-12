#!/bin/bash

# OSImager Linux Installer
# Installs OSImager to /opt/osimager with all components
# Usage: sudo ./install.sh [--uninstall]

set -euo pipefail

# Configuration
DEFAULT_INSTALL_DIR="/opt/osimager"
INSTALL_DIR="${OSIMAGER_INSTALL_DIR:-$DEFAULT_INSTALL_DIR}"
SERVICE_NAME="osimager"
SERVICE_USER="osimager"
WEB_PORT="8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/tmp/osimager-install.log"

# Helper functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

print_banner() {
    echo -e "${BLUE}"
    cat << 'EOF'
  ___  ____  ___                               
 / _ \/ ___|_ _|_ __ ___   __ _  __ _  ___ _ __ 
| | | \___ \| || '_ ` _ \ / _` |/ _` |/ _ \ '__|
| |_| |___) | || | | | | | (_| | (_| |  __/ |   
 \___/|____/___|_| |_| |_|\__,_|\__, |\___|_|   
                               |___/           
EOF
    echo -e "${NC}"
    echo "OSImager Linux Installer"
    echo "========================"
    echo
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
    fi
    
    # Check Python 3.6+
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [[ $PYTHON_MAJOR -lt 3 || ($PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 6) ]]; then
        error "Python 3.6+ is required, found $PYTHON_VERSION"
    fi
    
    log "Python $PYTHON_VERSION found ✓"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
    fi
    
    # Check systemd
    if ! command -v systemctl &> /dev/null; then
        error "systemd is required for service management"
    fi
    
    log "System requirements check passed ✓"
}

create_user() {
    log "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d "$INSTALL_DIR" -c "OSImager Service User" "$SERVICE_USER"
        log "Created user $SERVICE_USER ✓"
    else
        log "User $SERVICE_USER already exists ✓"
    fi
}

create_directories() {
    log "Creating directory structure..."
    
    # Create main directories
    mkdir -p "$INSTALL_DIR"/{bin,data,ui,logs,etc,lib/python}
    
    # Set ownership and permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 750 "$INSTALL_DIR"/{logs,etc}
    chmod 755 "$INSTALL_DIR"/{bin,data,ui,lib}
    
    log "Directory structure created ✓"
}

install_python_package() {
    log "Installing OSImager Python package..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/lib/python/venv"
    
    # Activate virtual environment
    source "$INSTALL_DIR/lib/python/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Copy osimager library to installation
    if [[ -d "./lib/osimager" ]]; then
        cp -r "./lib/osimager" "$INSTALL_DIR/lib/"
        chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/lib/osimager"
        log "Copied OSImager library to $INSTALL_DIR/lib/osimager ✓"
    else
        error "lib/osimager directory not found - run installer from OSImager project root"
    fi
    
    # Install requirements if available
    if [[ -f "./cli/requirements.txt" ]]; then
        pip install -r ./cli/requirements.txt
        log "Installed Python requirements ✓"
    fi
    
    # Install backend dependencies
    if [[ -d "./backend" ]]; then
        pip install -r backend/requirements.txt
        log "Installed backend dependencies ✓"
    fi
    
    deactivate
}

install_cli_programs() {
    log "Installing CLI programs..."
    
    # Ensure /opt/osimager/bin directory exists
    mkdir -p "$INSTALL_DIR/bin"
    
    # Copy Python scripts directly from bin/ to /opt/osimager/bin
    # Remove .py extension so they can be executed directly
    if [[ -d "./bin" ]]; then
        for script_py in ./bin/mkosimage.py ./bin/mkvenv.py ./bin/rfosimage.py; do
            if [[ -f "$script_py" ]]; then
                script_name=$(basename "$script_py" .py)
                # Copy the Python script and remove .py extension
                cp "$script_py" "$INSTALL_DIR/bin/$script_name"
                # Make it executable
                chmod +x "$INSTALL_DIR/bin/$script_name"
                log "Installed $script_name (from ${script_name}.py) to $INSTALL_DIR/bin/ ✓"
            fi
        done
    else
        warn "CLI scripts directory ./bin not found"
    fi
    
    # Set proper ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/bin"
    
    # Create /etc/profile.d/osimager.sh to add /opt/osimager/bin to PATH
    cat > "/etc/profile.d/osimager.sh" << 'EOF'
# Add OSImager bin directory to PATH
if [ -d "/opt/osimager/bin" ]; then
    export PATH="/opt/osimager/bin:$PATH"
fi
EOF
    
    chmod 644 "/etc/profile.d/osimager.sh"
    log "Created /etc/profile.d/osimager.sh to add /opt/osimager/bin to PATH ✓"
    
    log "CLI programs installed ✓"
}

install_data() {
    log "Installing data files..."
    
    # Copy data components individually from project root
    for component in platforms locations specs tasks files; do
        if [[ -d "./$component" ]]; then
            cp -r "./$component" "$INSTALL_DIR/data/"
            log "Copied $component directory ✓"
        else
            warn "$component directory not found"
        fi
    done
    
    # Copy additional configuration files
    for config_file in ansible.cfg inventory.ini generate_specs_index.py validate_config.py config_converter.py osimager_config.py; do
        if [[ -f "./$config_file" ]]; then
            cp "./$config_file" "$INSTALL_DIR/data/"
            log "Copied $config_file ✓"
        fi
    done
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/data"
    log "Data files installed ✓"
}

install_ui() {
    log "Installing web UI..."
    
    # Copy backend files
    if [[ -d "./backend" ]]; then
        cp -r ./backend "$INSTALL_DIR/lib/"
        chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/lib/backend"
        log "Backend files installed ✓"
    fi
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/ui"
}

install_configuration() {
    log "Installing configuration files..."
    
    # Main configuration
    if [[ -f "./osimager.conf" ]]; then
        cp ./osimager.conf "$INSTALL_DIR/etc/"
        
        # Update paths in configuration
        sed -i "s|base_dir = .*|base_dir = $INSTALL_DIR|g" "$INSTALL_DIR/etc/osimager.conf"
        sed -i "s|data_dir = .*|data_dir = $INSTALL_DIR/data|g" "$INSTALL_DIR/etc/osimager.conf"
        sed -i "s|log_dir = .*|log_dir = $INSTALL_DIR/logs|g" "$INSTALL_DIR/etc/osimager.conf"
        sed -i "s|web_root = .*|web_root = $INSTALL_DIR/ui|g" "$INSTALL_DIR/etc/osimager.conf"
        sed -i "s|host = 127.0.0.1|host = 0.0.0.0|g" "$INSTALL_DIR/etc/osimager.conf"
        
        log "Main configuration installed ✓"
    fi
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/etc"
    log "Configuration files installed ✓"
}

create_systemd_service() {
    log "Creating systemd service..."
    
    # Main OSImager service
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=OSImager API Server
Documentation=https://github.com/sshoecraft/OSImager
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/lib/python/venv/bin:/opt/osimager/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR/lib
Environment=OSIMAGER_CONFIG=$INSTALL_DIR/etc/osimager.conf
ExecStart=$INSTALL_DIR/lib/python/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port $WEB_PORT --app-dir $INSTALL_DIR/lib
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
Restart=always
RestartSec=5
StandardOutput=append:$INSTALL_DIR/logs/service.log
StandardError=append:$INSTALL_DIR/logs/service.log

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/data
ProtectHome=yes

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    log "Systemd service created and enabled ✓"
}

setup_logging() {
    log "Setting up logging..."
    
    # Create log files
    touch "$INSTALL_DIR/logs"/{api.log,service.log,cli.log,builds.log}
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/logs"/*
    
    log "Logging configured ✓"
}

create_admin_script() {
    log "Creating admin scripts..."
    
    # Create osimager-admin script
    cat > "$INSTALL_DIR/bin/osimager-admin" << 'EOF'
#!/bin/bash

# OSImager Administration Script
set -euo pipefail

SERVICE_NAME="osimager"
INSTALL_DIR="/opt/osimager"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    cat << USAGE_EOF
OSImager Administration Script

Usage: osimager-admin [COMMAND]

Commands:
    status      Show service status
    start       Start the OSImager service
    stop        Stop the OSImager service
    restart     Restart the OSImager service
    logs        Show service logs
    tail        Tail service logs
    check       Run system health check
    backup      Create backup of data and configuration
    help        Show this help message

USAGE_EOF
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error:${NC} This command requires root privileges"
        echo "Please run with sudo: sudo osimager-admin $1"
        exit 1
    fi
}

service_status() {
    echo -e "${BLUE}OSImager Service Status:${NC}"
    systemctl status "$SERVICE_NAME" --no-pager
}

service_start() {
    check_root "start"
    systemctl start "$SERVICE_NAME"
    echo -e "${GREEN}Service started successfully${NC}"
}

service_stop() {
    check_root "stop"
    systemctl stop "$SERVICE_NAME"
    echo -e "${GREEN}Service stopped successfully${NC}"
}

service_restart() {
    check_root "restart"
    systemctl restart "$SERVICE_NAME"
    echo -e "${GREEN}Service restarted successfully${NC}"
}

show_logs() {
    journalctl -u "$SERVICE_NAME" --no-pager
}

tail_logs() {
    journalctl -u "$SERVICE_NAME" -f
}

health_check() {
    echo -e "${BLUE}OSImager Health Check:${NC}"
    echo
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}✓${NC} Service is running"
    else
        echo -e "${RED}✗${NC} Service is not running"
    fi
    
    for cmd in mkosimage rfosimage mkvenv; do
        if [[ -f "$INSTALL_DIR/bin/$cmd" ]]; then
            echo -e "${GREEN}✓${NC} CLI command available: $cmd"
        else
            echo -e "${RED}✗${NC} CLI command missing: $cmd"
        fi
    done
}

create_backup() {
    check_root "backup"
    
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="/tmp/osimager_backup_$BACKUP_DATE"
    
    echo -e "${BLUE}Creating OSImager backup...${NC}"
    
    mkdir -p "$BACKUP_DIR"
    
    if [[ -d "$INSTALL_DIR/data" ]]; then
        cp -r "$INSTALL_DIR/data" "$BACKUP_DIR/"
        echo -e "${GREEN}✓${NC} Data backed up"
    fi
    
    if [[ -d "$INSTALL_DIR/etc" ]]; then
        cp -r "$INSTALL_DIR/etc" "$BACKUP_DIR/"
        echo -e "${GREEN}✓${NC} Configuration backed up"
    fi
    
    cd /tmp
    tar -czf "osimager_backup_$BACKUP_DATE.tar.gz" "osimager_backup_$BACKUP_DATE"
    rm -rf "$BACKUP_DIR"
    
    echo -e "${GREEN}Backup created:${NC} /tmp/osimager_backup_$BACKUP_DATE.tar.gz"
}

case "${1:-help}" in
    status) service_status ;;
    start) service_start ;;
    stop) service_stop ;;
    restart) service_restart ;;
    logs) show_logs ;;
    tail) tail_logs ;;
    check) health_check ;;
    backup) create_backup ;;
    help|--help|-h) usage ;;
    *) echo -e "${RED}Error:${NC} Unknown command: $1"; usage; exit 1 ;;
esac
EOF
    
    chmod +x "$INSTALL_DIR/bin/osimager-admin"
    ln -sf "$INSTALL_DIR/bin/osimager-admin" "/usr/local/bin/osimager-admin"
    
    # Create log cleanup script
    cat > "$INSTALL_DIR/bin/osimager-logclean" << 'EOF'
#!/bin/bash
INSTALL_DIR="/opt/osimager"
LOG_DIR="$INSTALL_DIR/logs"
DAYS_TO_KEEP=30

echo "Cleaning logs older than $DAYS_TO_KEEP days..."
find "$LOG_DIR" -name "*.log.*" -type f -mtime +$DAYS_TO_KEEP -delete 2>/dev/null || true
find "$LOG_DIR" -name "*.log" -type f -size +100M -exec gzip {} \; 2>/dev/null || true
echo "Log cleanup completed"
EOF
    
    chmod +x "$INSTALL_DIR/bin/osimager-logclean"
    
    # Create status script
    cat > "$INSTALL_DIR/bin/osimager-status" << 'EOF'
#!/bin/bash
INSTALL_DIR="/opt/osimager"
SERVICE_NAME="osimager"

echo "OSImager System Status Report"
echo "============================="
echo

echo "Service Status:"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "  Status: Running"
else
    echo "  Status: Stopped"
fi
echo

echo "Disk Usage:"
echo "  Installation: $(du -sh $INSTALL_DIR 2>/dev/null | cut -f1)"
echo "  Logs: $(du -sh $INSTALL_DIR/logs 2>/dev/null | cut -f1)"
echo "  Data: $(du -sh $INSTALL_DIR/data 2>/dev/null | cut -f1)"
EOF
    
    chmod +x "$INSTALL_DIR/bin/osimager-status"
    chown root:root "$INSTALL_DIR/bin/osimager-"*
    
    log "Admin scripts created ✓"
}

install_uninstaller() {
    log "Installing uninstaller..."
    
    if [[ -f "./uninstall.sh" ]]; then
        cp "./uninstall.sh" "$INSTALL_DIR/bin/osimager-uninstall"
        chmod +x "$INSTALL_DIR/bin/osimager-uninstall"
        ln -sf "$INSTALL_DIR/bin/osimager-uninstall" "/usr/local/bin/osimager-uninstall"
        log "Uninstaller script installed ✓"
    else
        warn "Uninstaller script not found - skipping"
    fi
}

start_service() {
    log "Starting OSImager service..."
    
    systemctl start "$SERVICE_NAME"
    sleep 5
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "OSImager service started successfully ✓"
        
        SYSTEM_IP=$(ip route get 1 | awk '{print $7; exit}' 2>/dev/null || echo "localhost")
        
        echo
        echo -e "${GREEN}=== Installation Complete ===${NC}"
        echo -e "OSImager has been installed to: ${BLUE}$INSTALL_DIR${NC}"
        echo -e "Web interface available at: ${BLUE}http://$SYSTEM_IP:$WEB_PORT${NC}"
        echo -e "Service status: ${GREEN}$(systemctl is-active $SERVICE_NAME)${NC}"
        echo
        echo "Available CLI commands (accessible via PATH):"
        echo "  mkosimage   - Create OS images"
        echo "  rfosimage   - Retrofit existing images"
        echo "  mkvenv      - Manage virtual environments"
        echo
        echo "Administrative commands:"
        echo "  osimager-admin     - Main administration tool"
        echo "  osimager-status    - Show system status"
        echo "  osimager-logclean  - Clean old log files"
        echo "  osimager-uninstall - Uninstall OSImager"
        echo
        echo "CLI tools are in PATH via: /etc/profile.d/osimager.sh"
        echo
    else
        error "Failed to start OSImager service"
    fi
}

uninstall() {
    log "Uninstalling OSImager..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl stop "$SERVICE_NAME"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        systemctl disable "$SERVICE_NAME"
    fi
    
    rm -f "/etc/systemd/system/$SERVICE_NAME.service"
    systemctl daemon-reload
    
    for script in mkosimage rfosimage mkvenv osimager-admin osimager-uninstall; do
        rm -f "/usr/local/bin/$script"
    done
    
    rm -f "/etc/profile.d/osimager.sh"
    
    if id "$SERVICE_USER" &>/dev/null; then
        userdel "$SERVICE_USER" || true
    fi
    
    if [[ -d "$INSTALL_DIR" ]]; then
        read -p "Remove installation directory $INSTALL_DIR? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            log "Installation directory removed ✓"
        else
            log "Installation directory preserved"
        fi
    fi
    
    log "OSImager uninstalled ✓"
}

show_help() {
    cat << EOF
OSImager Linux Installer

Usage: sudo ./install.sh [OPTIONS]

Options:
  --install-dir DIR    Installation directory (default: /opt/osimager)
  --port PORT         Web interface port (default: 8000)
  --user USER         Service user (default: osimager)
  --uninstall         Uninstall OSImager
  --help              Show this help message

Examples:
  sudo ./install.sh                           # Install with defaults
  sudo ./install.sh --install-dir /usr/local/osimager
  sudo ./install.sh --port 9000
  sudo ./install.sh --uninstall

EOF
}

main() {
    print_banner
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --port)
                WEB_PORT="$2"
                shift 2
                ;;
            --user)
                SERVICE_USER="$2"
                shift 2
                ;;
            --uninstall)
                uninstall
                exit 0
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    log "Starting OSImager installation..."
    log "Installation directory: $INSTALL_DIR"
    log "Web port: $WEB_PORT"
    log "Service user: $SERVICE_USER"
    echo
    
    if [[ -d "$INSTALL_DIR" ]]; then
        warn "Installation directory $INSTALL_DIR already exists"
        read -p "Continue with installation? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Installation cancelled"
            exit 0
        fi
    fi
    
    check_requirements
    create_user
    create_directories
    install_python_package
    install_cli_programs
    install_data
    install_ui
    install_configuration
    create_systemd_service
    setup_logging
    create_admin_script
    install_uninstaller
    start_service
    
    log "Installation completed successfully!"
}

main "$@"
