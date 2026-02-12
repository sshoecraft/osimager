#!/bin/bash
#
# install-plugins.sh - Install required Packer plugins for OSImager
#
# This script installs all Packer plugins needed by the various
# platforms and provisioners used in OSImager.
#

set -e

echo "Installing Packer plugins for OSImager..."
echo

# Install provisioner plugins
echo "Installing provisioner plugins..."
packer plugins install github.com/hashicorp/ansible

# Install platform plugins
echo
echo "Installing platform builder plugins..."

# VMware
echo "  - vmware"
packer plugins install github.com/hashicorp/vmware

# vSphere
echo "  - vsphere"
packer plugins install github.com/hashicorp/vsphere

# VirtualBox
echo "  - virtualbox"
packer plugins install github.com/hashicorp/virtualbox

# QEMU
echo "  - qemu"
packer plugins install github.com/hashicorp/qemu

# Proxmox
echo "  - proxmox"
packer plugins install github.com/hashicorp/proxmox

# Libvirt (if available - may not be in official HashiCorp registry)
echo "  - libvirt (attempting to install...)"
packer plugins install github.com/thomasklein94/libvirt 2>/dev/null || echo "    Note: libvirt plugin not found in registry, may need manual installation"

echo
echo "✓ Plugin installation complete!"
echo
echo "Installed plugins:"
packer plugins installed
