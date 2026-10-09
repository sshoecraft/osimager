# Installation

## Quick Install

```bash
pip install osimager
```

## Prerequisites

- **Python 3.8+**
- **HashiCorp Packer** -- [install instructions](https://developer.hashicorp.com/packer/install)
- **mkisofs** -- used by Packer to create the CD that carries the answer file. OSImager requires it only for builds whose builder uses `cd_files` (the ISO platforms); cloud builds don't need it

Ansible is installed automatically as a dependency of the osimager pip package. Specs that set an `ansible_version` run post-install configuration from a dedicated virtual environment instead; see [Ansible Versions](#ansible-versions).

## Packer Plugins

OSImager requires Packer plugins for both the Ansible provisioner and each platform's builder. Install all of them at once:

```bash
mkosimage --init-plugins
```

This reads the `plugin` key from each platform configuration file and runs `packer plugins install` for each one, plus the Ansible provisioner plugin (`github.com/hashicorp/ansible`). It runs the install for every plugin each time, whether or not it is already installed, and reports any that fail.

## Ansible Versions

A spec's `ansible_version` (e.g. `"2.18"`) names the Ansible its post-install configuration needs. `mkosimage` activates `<venv_dir>/<version>` before running Packer (default `~/.local/share/osimager/venvs/`, override with the `OSIMAGER_VENV_DIR` environment variable), and stops with `error: post-install requires Ansible <version>` if that venv is missing, unless `--skip` is given. Create the venvs with `mkvenv`:

```bash
mkvenv              # show which venvs the specs need and which are installed
mkvenv 2.18         # create one
mkvenv --all        # create every missing venv the specs need
```

For each Ansible version, `ansible.json` gives the package name, the Python version range and any prerequisite packages. `mkvenv` looks for a matching interpreter on your `PATH`, creates the venv (with `virtualenv` for Python 2, installing it with that interpreter's pip if needed), and installs the package.

### Legacy Ansible for Older OSes

Some older OS specs (e.g. RHEL 5 and 6, Fedora 7-20) need Ansible 2.3 or 2.9, which only run under Python 2. `mkvenv` looks for `python2.7`, `python2.6` or `python2` on your `PATH` for these.

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

---

## Legacy VMware Tools

Legacy vmtools can be downloaded directly from Broadcom. Search for "legacy vmtools".

## Verification

```bash
mkosimage --version
```
