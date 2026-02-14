# Installation

## Quick Install

```bash
pip install osimager
```

## Prerequisites

- **Python 3.8+**
- **HashiCorp Packer** -- [install instructions](https://developer.hashicorp.com/packer/install)
- **mkisofs** -- used by Packer to create CD/ISO images containing answer files

Ansible is installed automatically as a dependency of the osimager pip package.

## Packer Plugins

OSImager requires Packer plugins for both the Ansible provisioner and each platform's builder. Install all of them at once:

```bash
mkosimage --init-plugins
```

This reads the `plugin` key from each platform configuration file and runs `packer plugins install` for each one, plus the Ansible provisioner plugin. Plugins that are already installed will be skipped.

## Verification

```bash
mkosimage --version
```
