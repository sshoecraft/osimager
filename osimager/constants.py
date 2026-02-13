# OSImager Constants

"""
Constants and configuration values used throughout OSImager.

This module contains all magic numbers, default values, and
configuration constants to maintain consistency across the codebase.
"""

# Version information
OSIMAGER_VERSION = "1.4.0"
OSIMAGER_NAME = "OSImager"

# Default paths and directories
DEFAULT_DATA_DIR = "data"
DEFAULT_CONFIG_DIR = "~/.config/osimager"
DEFAULT_CACHE_DIR = "/tmp"

# Configuration file names
SETTINGS_FILENAME = "settings.json"
SPEC_FILENAME = "spec.json"
VAULT_CONFIG_FILENAME = "vaultconfig"
ANSIBLE_PLAYBOOK_FILENAME = "config.yml"

# Directory names
PLATFORM_DIR = "platforms"
LOCATION_DIR = "locations"
SPEC_DIR = "specs"
FLAVOR_DIR = "flavors"
COMMUNICATOR_DIR = "communicators"
TASK_DIR = "tasks"
FILE_DIR = "files"
VENV_DIR = "venv"

# Default tool commands
DEFAULT_PACKER_CMD = "packer"

# File size limits
MAX_FILE_LINES = 500  # Maximum lines per file before refactoring

# Network defaults
DEFAULT_DNS_SERVERS = ["8.8.8.8", "8.8.4.4"]
DEFAULT_NTP_SERVERS = ["pool.ntp.org"]

# Timeout values (seconds)
DEFAULT_NETWORK_TIMEOUT = 30
DEFAULT_BUILD_TIMEOUT = 3600  # 1 hour

# Supported platforms
SUPPORTED_PLATFORMS = [
    "vmware",
    "vmware-vmx",
    "virtualbox",
    "qemu",
    "libvirt",
    "proxmox",
    "vsphere",
    "hyperv",
    "xenserver",
    "azure",
    "gcp",
    "aws",
    "none"
]

# Supported operating systems
SUPPORTED_DISTRIBUTIONS = [
    "rhel",
    "centos",
    "alma",
    "rocky",
    "oel",
    "debian",
    "ubuntu",
    "sles",
    "esxi",
    "sysvr4",
    "windows",
    "windows-server"
]

# Supported architectures
SUPPORTED_ARCHITECTURES = [
    "x86_64",
    "amd64", 
    "aarch64",
    "arm64",
    "i386"
]

# Default settings dictionary
DEFAULT_SETTINGS = {
    "packer_cmd": DEFAULT_PACKER_CMD,
    "data_dir": DEFAULT_DATA_DIR,
    "vaultconfig": VAULT_CONFIG_FILENAME,
    "platform_dir": PLATFORM_DIR,
    "location_dir": LOCATION_DIR,
    "spec_dir": SPEC_DIR,
    "spec_filename": SPEC_FILENAME,
    "flavor_dir": FLAVOR_DIR,
    "communicator_dir": COMMUNICATOR_DIR,
    "task_dir": TASK_DIR,
    "file_dir": FILE_DIR,
    "venv_dir": VENV_DIR,
    "ansible_playbook": ANSIBLE_PLAYBOOK_FILENAME,
    "packer_cache_dir": DEFAULT_CACHE_DIR,
    "local_only": False
}

# Environment variables
ANSIBLE_ENV_VARS = {
    "ANSIBLE_RETRY_FILES_ENABLED": "False",
    "ANSIBLE_WARNINGS": "False", 
    "ANSIBLE_NOCOWS": "1"
}

# Error messages
ERROR_MESSAGES = {
    "invalid_target_format": "Target must be in format platform/location/spec",
    "spec_not_found": "Spec '{}' not found in index",
    "platform_not_supported": "Platform '{}' not supported by location '{}'",
    "location_not_supported": "Location '{}' not supported by spec '{}'",
    "missing_vault_config": "Vault configuration missing: {}",
    "invalid_json": "Invalid JSON in file: {}",
    "file_not_found": "Configuration file not found: {}",
    "permission_denied": "Permission denied accessing: {}",
    "invalid_setting_key": "Invalid setting key: {}",
    "missing_provides_section": "Spec file {} missing 'provides' section"
}

# CLI argument defaults
CLI_DEFAULTS = {
    "config": DEFAULT_CONFIG_DIR,
    "verbose": False,
    "debug": False,
    "force": False,
    "keep": False,
    "dry_run": False,
    "timestamp": False,
    "list": False
}

# File extensions
JSON_EXTENSION = ".json"
YAML_EXTENSION = ".yml"
ISO_EXTENSION = ".iso"

# Regular expressions
VERSION_PATTERN = r"^\d+\.\d+(\.\d+)?$"
IP_PATTERN = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
FQDN_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?(?:\.[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?)*$"

# Build phases
BUILD_PHASES = [
    "pre_provisioners",
    "provisioners", 
    "post_provisioners"
]

# Packer on-error behaviors
PACKER_ON_ERROR_OPTIONS = [
    "cleanup",
    "abort",
    "ask"
]

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# HTTP status codes for URL checking
HTTP_SUCCESS_CODES = [200, 301, 302]

# Checksum algorithms
SUPPORTED_CHECKSUM_ALGORITHMS = [
    "md5",
    "sha1", 
    "sha256",
    "sha512"
]

# Default resource limits
DEFAULT_MEMORY_MB = 2048
DEFAULT_CPU_COUNT = 2
DEFAULT_DISK_SIZE_MB = 20480

# Firmware types
FIRMWARE_TYPES = [
    "bios",
    "efi", 
    "uefi"
]

# Guest OS types for common platforms
GUEST_OS_TYPES = {
    "vmware": {
        "rhel8": "rhel8-64",
        "rhel9": "rhel9-64",
        "centos7": "centos7-64",
        "centos8": "centos8-64",
        "debian": "debian10-64",
        "ubuntu": "ubuntu-64",
        "windows": "windows9srv-64"
    },
    "virtualbox": {
        "rhel": "RedHat_64",
        "centos": "RedHat_64", 
        "debian": "Debian_64",
        "ubuntu": "Ubuntu_64",
        "windows": "Windows2019_64"
    }
}

# Template substitution markers
TEMPLATE_START_MARKER = ">>"
TEMPLATE_END_MARKER = "<<"

# Maximum number of retry attempts
MAX_RETRY_ATTEMPTS = 3

# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_MISUSE = 2
EXIT_CONFIG_ERROR = 3
EXIT_NETWORK_ERROR = 4
EXIT_PERMISSION_ERROR = 5
