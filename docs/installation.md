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

## Legacy Ansible for Older OSes

Some older OS specs (e.g. RHEL 2.x-6.x, CentOS 5.x-6.x) require legacy versions of Ansible that only run under Python 2.7. These specs have a `venv` field pointing to a Python virtual environment containing the correct Ansible version.

### Building Python 2.7

If your system doesn't have Python 2.7 installed, build it from source:

```bash
# Dependencies
apt install libssl-dev zlib1g-dev libffi-dev default-libmysqlclient-dev

cd /usr/src
wget https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz
tar xzf Python-2.7.18.tgz
cd Python-2.7.18
./configure -prefix=/usr --enable-optimizations --with-ensurepip=install
make -j 8 altinstall
python2.7 -m pip install --upgrade pip
```

If pip2 is not installed:

```bash
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
python2.7 get-pip.py
```

### Creating Ansible Virtualenvs

Install virtualenv with pip2:

```bash
pip2 install virtualenv
```

Create a virtualenv for the ansible version you need (e.g. ansible 2.10):

```bash
python2.7 -m virtualenv ~/venvs/ansible-2.10
source ~/venvs/ansible-2.10/bin/activate
pip install 'pyyaml<5.4'
pip install ansible==2.10.7
deactivate
```

For RHEL 5 support, ansible 2.3 is needed:

```bash
python2.7 -m virtualenv ~/venvs/ansible-2.3
source ~/venvs/ansible-2.3/bin/activate
pip install 'pyyaml<5.4'
pip install ansible==2.3
deactivate
```

In your OS spec file, set `"venv": "~/venvs/ansible-2.10"` and osimager will switch to it for the build.

## Legacy VMware Tools

Legacy vmtools can be downloaded directly from Broadcom. Search for "legacy vmtools".

## Verification

```bash
mkosimage --version
```
