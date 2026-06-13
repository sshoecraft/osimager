"""
OSImager CLI entry points.

Console script functions for pip-installed entry points.
"""

import os
import sys
import shutil
import subprocess
from typing import List, Optional

from .core import OSImager
from .core import EXIT_SUCCESS, EXIT_ERROR as EXIT_GENERAL_ERROR
from .utils import get_filename_from_url


def main_mkosimage(argv: Optional[List[str]] = None) -> int:
    """Entry point for mkosimage command."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        osimager = OSImager(argv=argv, which="full")

        if osimager.show_config:
            print(f"Config file: {os.path.join(osimager.settings['user_dir'], 'config.json')}")
            print("")
            for key, val in sorted(osimager.settings.items()):
                if key in ('base_dir', 'user_dir'):
                    continue
                print(f"  {key:<20} = {val}")
            return EXIT_SUCCESS

        if osimager.check_urls:
            osimager.check_all_urls()
            return EXIT_SUCCESS

        if osimager.local_only and not osimager.target:
            osimager.avail = True

        if osimager.avail:
            index = osimager.get_index()
            if not index:
                print("No specs found. Have you installed osimager-data?")
                print(f"  pip install osimager-data")
                print(f"  Or create your own: {osimager.settings['user_dir']}/specs/")
                return EXIT_SUCCESS

            download = []
            local = []
            missing = []

            for spec_key in sorted(index.keys()):
                entry = index[spec_key]
                iso_url = entry.get('iso_url', '')
                iso_local = entry.get('iso_local', False)

                if not iso_url:
                    missing.append((spec_key, '(no iso_url defined)'))
                elif iso_url.startswith('file://'):
                    path = iso_url[7:]
                    if iso_local:
                        local.append((spec_key, path))
                    else:
                        missing.append((spec_key, path))
                else:
                    if iso_local:
                        iso_name = get_filename_from_url(iso_url)
                        iso_path = osimager.settings.get('iso_path', '/iso')
                        local.append((spec_key, os.path.join(iso_path, iso_name)))
                    else:
                        download.append((spec_key, iso_url))

            local_only = osimager.settings.get('local_only', False)

            if local:
                print(f"Local ({len(local)}):")
                for spec_key, path in local:
                    print(f"  {spec_key:<30} {path}")
                print()

            if not local_only and download:
                print(f"Download ({len(download)}):")
                for spec_key, url in download:
                    print(f"  {spec_key:<30} {url}")
                print()

            if local_only:
                print(f"{len(local)} local ISOs ({len(index)} total specs)")
            else:
                avail = len(download) + len(local)
                print(f"{avail} available, {len(missing)} not available ({len(index)} total)")
            return EXIT_SUCCESS

        if osimager.list_platforms:
            platforms = osimager.get_platforms()
            print("Available platforms:")
            for plat in platforms:
                name = plat.get('name', '')
                config = plat.get('config', {})
                builder_type = config.get('type', 'unknown')
                arches = plat.get('arches', [])
                arches_str = ', '.join(arches) if arches else 'any'
                print(f"  {name:<14} {builder_type:<20} ({arches_str})")
            return EXIT_SUCCESS

        if osimager.init_plugins:
            packer_cmd = osimager.settings.get('packer_cmd', 'packer')
            if not shutil.which(packer_cmd):
                print(f"error: '{packer_cmd}' not found in PATH")
                print("")
                print("  Packer is required. Install instructions:")
                print("    https://developer.hashicorp.com/packer/install")
                return EXIT_GENERAL_ERROR

            # Ansible provisioner plugin — always needed
            plugins = ['github.com/hashicorp/ansible']

            # Collect plugins from platform files
            platforms = osimager.get_platforms()
            seen = set()
            for plat in platforms:
                plugin = plat.get('plugin')
                if plugin and plugin not in seen:
                    plugins.append(plugin)
                    seen.add(plugin)

            print(f"Installing {len(plugins)} Packer plugins...")
            failed = []
            for plugin in plugins:
                print(f"  {plugin}")
                result = subprocess.run(
                    [packer_cmd, 'plugins', 'install', plugin],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    print(f"    FAILED: {result.stderr.strip()}")
                    failed.append(plugin)

            if failed:
                print(f"\n{len(failed)} plugin(s) failed to install:")
                for p in failed:
                    print(f"  {p}")
                return EXIT_GENERAL_ERROR

            print("Done.")
            return EXIT_SUCCESS

        if osimager.list_defs:
            # Show configuration defaults (from config.json / built-in defaults)
            config_defs = {
                'cpu_sockets': osimager.settings.get('cpu_sockets', 1),
                'cpu_cores': osimager.settings.get('cpu_cores', 2),
                'memory': osimager.settings.get('memory', 2048),
                'boot_disk_size': osimager.settings.get('boot_disk_size', 16384),
            }

            platforms = osimager.get_platforms()
            # Collect all defs from platforms
            all_defs = {}
            for plat in platforms:
                name = plat.get('name', '')
                plat_defs = plat.get('defs', {})
                for key, val in plat_defs.items():
                    if key not in all_defs:
                        all_defs[key] = {'value': val, 'source': name}

            # Add computed defs
            computed = {
                'name': 'hostname or spec name',
                'fqdn': 'name + domain',
                'ip': 'CLI arg or DNS lookup',
                'platform': 'from target',
                'location': 'from target',
                'dist': 'from spec provides',
                'version': 'from spec provides',
                'major': 'major version number',
                'minor': 'minor version number',
                'arch': 'from spec provides',
                'subnet': 'from CIDR',
                'prefix': 'from CIDR',
                'netmask': 'from CIDR prefix',
                'gateway': 'from location or CIDR',
                'domain': 'from location',
                'dns1': 'from location dns.servers',
                'dns_search': 'from location dns.search',
                'ntp1': 'from location ntp.servers',
                'iso_url': 'from spec',
                'iso_path': 'from settings (default: /iso)',
                'vms_path': 'from location',
            }

            print("Configuration defaults (~/.config/osimager/config.json):")
            for key, val in sorted(config_defs.items()):
                print(f"  {key:<20} = {val}")

            print("\nPlatform defs:")
            for key, info in sorted(all_defs.items()):
                val_str = str(info['value'])
                if len(val_str) > 50:
                    val_str = val_str[:47] + '...'
                print(f"  {key:<20} = {val_str:<50}  ({info['source']})")

            print("\nComputed defs:")
            for key, desc in sorted(computed.items()):
                if key not in all_defs:
                    print(f"  {key:<20}   {desc}")

            print("\nUse -D KEY=VALUE to override any def at build time.")
            print("Use -x PLATFORM/LOCATION/SPEC to see all resolved defs for a specific build.")
            return EXIT_SUCCESS

        if osimager.list:
            index = osimager.get_index()
            if index:
                print("Available specs:")
                for spec_key in sorted(index.keys()):
                    entry = index[spec_key]
                    iso_flag = " (*)" if entry.get('iso_local', False) else ""
                    print(f"  {spec_key}{iso_flag}")
            else:
                print("No specs found. Have you installed osimager-data?")
                print(f"  pip install osimager-data")
                print(f"  Or create your own: {osimager.settings['user_dir']}/specs/")
            return EXIT_SUCCESS

        if not osimager.target:
            print("Usage: mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]")
            print("")

            # Check what the user is missing
            user_dir = osimager.settings['user_dir']
            locations = osimager.get_locations()
            cred_source = osimager.settings.get('credential_source', 'vault')

            examples_dir = osimager.resolve_data_path('examples') or os.path.join(osimager.settings['user_dir'], 'examples')

            docs_url = "https://sshoecraft.github.io/osimager"
            need_docs = False

            if not locations:
                print("No locations configured.")
                print(f"  Create a location file in {os.path.join(user_dir, 'locations/')}")
                print(f"  Supports .toml and .json formats (e.g. lab.toml or lab.json)")
                print("")
                print("  Quick start (VirtualBox):")
                print(f"    cp {os.path.join(examples_dir, 'quickstart-location.toml')} \\")
                print(f"       {os.path.join(user_dir, 'locations', 'local.toml')}")
                print("")
                need_docs = True

            if cred_source == "vault":
                vault_addr = osimager.settings.get('vault_addr', '')
                vault_token = osimager.settings.get('vault_token', '')
                if not vault_addr or not vault_token:
                    print("No credentials configured.")
                    print("  Option 1 - Local secrets file (simplest):")
                    print("    mkosimage --set credential_source=config")
                    print(f"    cp {os.path.join(examples_dir, 'example-secrets')} \\")
                    print(f"       {os.path.join(user_dir, 'secrets')}")
                    print("    Then edit ~/.config/osimager/secrets with your passwords.")
                    print("")
                    print("  Option 2 - HashiCorp Vault:")
                    print("    mkosimage --set vault_addr=http://your-vault:8200")
                    print("    mkosimage --set vault_token=your-token")
                    print("")
                    need_docs = True
            elif cred_source == "config":
                secrets_path = os.path.join(user_dir, 'secrets')
                if not os.path.exists(secrets_path):
                    print("No secrets file found.")
                    print(f"  cp {os.path.join(examples_dir, 'example-secrets')} \\")
                    print(f"     {secrets_path}")
                    print("  Then edit the file with your passwords.")
                    print("")
                    need_docs = True

            if need_docs:
                print(f"  Full documentation: {docs_url}")
                print("")

            if locations:
                platforms = osimager.get_platforms()
                if platforms:
                    print("Available platforms/locations:")
                    for plat in platforms:
                        plat_name = plat.get('name', '')
                        plat_locations = [l.get('name', '') for l in locations if plat_name in l.get('platforms', [])]
                        if plat_locations:
                            print(f"  {plat_name}: {', '.join(plat_locations)}")
                    print("")
                    print("Use --list to see available specs.")
                else:
                    print("No platforms found. Have you installed osimager-data?")
                    print(f"  pip install osimager-data")
                    print(f"  Or create your own: {osimager.settings['user_dir']}/platforms/")

            print("Use --help for all options.")
            return EXIT_SUCCESS

        build_config = osimager.make_build(
            osimager.target,
            name=osimager.name,
            ip=osimager.ip or ""
        )

        if osimager.dump_defs or osimager.dump_build:
            return EXIT_SUCCESS

        osimager.run_packer()
        return osimager.exit_code if hasattr(osimager, 'exit_code') and osimager.exit_code else EXIT_SUCCESS

    except SystemExit as e:
        return e.code if e.code is not None else EXIT_GENERAL_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return EXIT_GENERAL_ERROR
    except Exception as e:
        print(f"Error: {e}")
        return EXIT_GENERAL_ERROR


def main_rfosimage(argv: Optional[List[str]] = None) -> int:
    """Entry point for rfosimage command."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        extra_args = {
            "plan": {"flags": [], "kwargs": {"help": "platform/location/spec", "dest": "plan"}},
            "name": {"flags": [], "kwargs": {"help": "hostname", "dest": "name", "nargs": "?", "default": None}},
            "ip": {"flags": [], "kwargs": {"help": "ip", "dest": "ip", "nargs": "?", "default": None}},
        }
        img = OSImager(argv, "full", extra_args)
        plan = img.args.plan
        name = img.args.name
        ip = img.args.ip

        non_flag_args = [arg for arg in argv if not arg.startswith('-')]
        if len(non_flag_args) >= 2 and not name:
            name = non_flag_args[1]
        if len(non_flag_args) >= 3 and not ip:
            ip = non_flag_args[2]

        build = img.make_build(plan, name, ip)
        if not build:
            return EXIT_GENERAL_ERROR
        defs = img.defs

        if 'files' in img.spec:
            del img.spec['files']

        builders = build['builders']
        config = builders[0]
        comm = config.get('communicator', None)
        if not comm:
            print("error: build does not have a communicator defined")
            return EXIT_GENERAL_ERROR

        new_config = {
            "name": defs.get("spec_name", "name"),
            "type": "null"
        }
        for key in config:
            if key.startswith(comm):
                new_config[key] = config[key]

        del builders[0]
        builders.append(new_config)
        build['builders'] = builders

        img.run_packer()
        return img.exit_code if hasattr(img, 'exit_code') and img.exit_code else EXIT_SUCCESS

    except SystemExit as e:
        return e.code if e.code is not None else EXIT_GENERAL_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return EXIT_GENERAL_ERROR
    except Exception as e:
        print(f"Error: {e}")
        return EXIT_GENERAL_ERROR


def _get_python_version(python_path):
    """Get the major.minor version tuple from a Python interpreter."""
    rc = subprocess.run([python_path, "--version"], capture_output=True, text=True)
    ver_str = rc.stdout.strip() or rc.stderr.strip()
    try:
        return tuple(int(x) for x in ver_str.split()[1].split(".")[:2])
    except (IndexError, ValueError):
        return None


def _find_python(min_version, max_version=None):
    """Find a Python interpreter >= min_version and <= max_version.
    Versions are strings like '3.10' or '2.7'. max_version=None means no upper limit.
    Returns the path to the interpreter, or None."""
    min_parts = tuple(int(x) for x in min_version.split("."))
    max_parts = tuple(int(x) for x in max_version.split(".")) if max_version else None
    is_py2 = min_parts[0] == 2

    if is_py2:
        candidates = ["python2.7", "python2.6", "python2"]
    else:
        # Try versioned interpreters from high to low, then generic
        candidates = [f"python3.{m}" for m in range(20, min_parts[1] - 1, -1)]
        candidates.append("python3")

    for cmd in candidates:
        path = shutil.which(cmd)
        if not path:
            continue
        ver = _get_python_version(path)
        if not ver:
            continue
        if ver < min_parts:
            continue
        if max_parts and ver > max_parts:
            continue
        return path

    return None


def _create_venv(venv_path, python_path):
    """Create a virtualenv using the appropriate method for the Python version."""
    ver = _get_python_version(python_path)
    is_python2 = ver and ver[0] == 2

    if is_python2:
        # Check if virtualenv is available under this Python
        rc = subprocess.run([python_path, "-m", "virtualenv", "--version"], capture_output=True)
        if rc.returncode != 0:
            print(f"Installing virtualenv for {python_path}...")
            rc = subprocess.run([python_path, "-m", "pip", "install", "virtualenv"], capture_output=True)
            if rc.returncode != 0:
                print(f"error: virtualenv is required for {python_path} and could not be installed")
                sys.exit(1)
        rc = subprocess.run([python_path, "-m", "virtualenv", venv_path])
    else:
        rc = subprocess.run([python_path, "-m", "venv", venv_path])

    return rc.returncode == 0


def _load_ansible_versions(osimager):
    """Load ansible version definitions from ansible.json via two-layer resolution.
    Returns dict keyed by version string."""
    import json

    # Try user dir first, then system data dir
    for base in [osimager.settings['user_dir'], osimager.system_data_dir]:
        if not base:
            continue
        path = os.path.join(base, "ansible.json")
        if os.path.isfile(path):
            with open(path, 'r') as f:
                data = json.load(f)
            return {entry["version"]: entry for entry in data.get("versions", [])}

    return {}


def _scan_specs_for_venvs(osimager):
    """Scan all specs for unique ansible_version values.
    Returns a set of version strings."""
    import json
    required = set()
    specs = osimager.resolve_data_files("specs", "*.json")
    for spec_file in specs:
        try:
            with open(spec_file, 'r') as f:
                data = json.load(f)
        except Exception:
            continue

        def collect(entry):
            av = entry.get("ansible_version")
            if av:
                required.add(av)

        collect(data)
        for entry in data.get("version_specific", []):
            collect(entry)
            for arch_entry in entry.get("arch_specific", []):
                collect(arch_entry)
        for entry in data.get("arch_specific", []):
            collect(entry)

    return required


def main_mkvenv(argv: Optional[List[str]] = None) -> int:
    """Entry point for mkvenv command."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        extra_args = {
            "--all": {"flags": ["--all"], "kwargs": {"default": False, "action": "store_true", "help": "Create all missing venvs", "dest": "all"}},
            "ansible_version": {"flags": ["ansible_version"], "kwargs": {"nargs": "?", "default": None, "help": "Ansible version to create venv for (e.g. 2.16)"}},
        }
        osimager = OSImager(argv=argv, which="venv", extra_args=extra_args)
        args = osimager.args
        venv_dir = osimager.settings['venv_dir']

        # Load ansible version definitions from ansible.json
        ansible_defs = _load_ansible_versions(osimager)
        if not ansible_defs:
            print("error: ansible.json not found")
            print("  Install osimager-data or create ~/.config/osimager/ansible.json")
            return EXIT_GENERAL_ERROR

        # Scan all specs for required ansible versions
        required = _scan_specs_for_venvs(osimager)

        version = args.ansible_version
        create_all = args.all

        # No args: list status
        if not version and not create_all:
            print(f"Venv directory: {venv_dir}")
            print()
            if not required:
                print("No venvs required by any specs.")
                return EXIT_SUCCESS
            print("Required ansible venvs:")
            for ver in sorted(required):
                venv_path = os.path.join(venv_dir, ver)
                exists = os.path.isfile(os.path.join(venv_path, "bin", "activate"))
                adef = ansible_defs.get(ver)
                if exists:
                    status = "installed"
                elif not adef:
                    status = f"missing (ansible {ver} not defined in ansible.json)"
                else:
                    min_py = adef.get("python_min")
                    max_py = adef.get("python_max")
                    pkg = adef.get("pkg", "ansible-core")
                    python_path = _find_python(min_py, max_py)
                    if python_path:
                        status = f"missing ({pkg}, python: {python_path})"
                    else:
                        req = f">= {min_py}"
                        if max_py:
                            req += f" and <= {max_py}"
                        status = f"missing ({pkg}, requires python {req} - NOT FOUND)"
                print(f"  {ver:10s} {status}")
            return EXIT_SUCCESS

        # Build list of versions to create
        if create_all:
            versions = sorted(required)
        else:
            versions = [version]

        # Create each venv
        for ver in versions:
            venv_path = os.path.join(venv_dir, ver)
            activator = os.path.join(venv_path, "bin", "activate")

            if os.path.isfile(activator):
                print(f"Venv {ver} already exists at {venv_path}")
                continue

            adef = ansible_defs.get(ver)
            if not adef:
                print(f"error: ansible {ver} not defined in ansible.json")
                print(f"  Known versions: {', '.join(sorted(ansible_defs.keys()))}")
                return EXIT_GENERAL_ERROR

            min_py = adef.get("python_min")
            max_py = adef.get("python_max")
            pkg = adef.get("pkg", "ansible-core")

            python_path = _find_python(min_py, max_py)
            if not python_path:
                req = f">= {min_py}"
                if max_py:
                    req += f" and <= {max_py}"
                print(f"error: no Python {req} found for ansible {ver}")
                print(f"  Install a compatible Python version and ensure it is in your PATH")
                return EXIT_GENERAL_ERROR

            pkg_spec = f"{pkg}=={ver}.*"
            print(f"Creating venv for {pkg} {ver} (using {python_path})...")
            os.makedirs(venv_dir, exist_ok=True)

            if not _create_venv(venv_path, python_path):
                print(f"error: failed to create venv at {venv_path}")
                return EXIT_GENERAL_ERROR

            pip = os.path.join(venv_path, "bin", "pip")

            # Install pre-requirements from ansible.json before the ansible package
            requirements = adef.get("requirements", [])
            for req in requirements:
                print(f"Installing prerequisite: {req}...")
                rc = subprocess.run([pip, "install", req])
                if rc.returncode != 0:
                    print(f"error: failed to install {req} into {venv_path}")
                    shutil.rmtree(venv_path, ignore_errors=True)
                    return EXIT_GENERAL_ERROR

            print(f"Installing {pkg_spec}...")
            rc = subprocess.run([pip, "install", pkg_spec])
            if rc.returncode != 0:
                print(f"error: failed to install {pkg_spec} into {venv_path}")
                shutil.rmtree(venv_path, ignore_errors=True)
                return EXIT_GENERAL_ERROR

            print(f"Venv {ver} created at {venv_path}")

        return EXIT_SUCCESS

    except SystemExit as e:
        return e.code if e.code is not None else EXIT_GENERAL_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return EXIT_GENERAL_ERROR
    except Exception as e:
        print(f"Error: {e}")
        return EXIT_GENERAL_ERROR
