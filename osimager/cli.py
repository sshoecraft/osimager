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
from .constants import EXIT_SUCCESS, EXIT_GENERAL_ERROR


def main_mkosimage(argv: Optional[List[str]] = None) -> int:
    """Entry point for mkosimage command."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        osimager = OSImager(argv=argv, which="full")

        if osimager.show_config:
            print(f"Config file: {os.path.join(osimager.settings['user_dir'], 'osimager.conf')}")
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
            index = osimager.get_index()
            if not index:
                print("No specs found.")
                return EXIT_SUCCESS

            local = [(k, e.get('iso_url', '')) for k, e in sorted(index.items()) if e.get('iso_local', False)]
            if local:
                for spec_key, iso_url in local:
                    path = iso_url[7:] if iso_url.startswith('file://') else iso_url
                    print(f"  {spec_key:<30} {path}")
                print()
            print(f"{len(local)} local ISOs available ({len(index)} total specs)")
            return EXIT_SUCCESS

        if osimager.avail:
            index = osimager.get_index()
            if not index:
                print("No specs found.")
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
                        local.append((spec_key, iso_url))
                    else:
                        download.append((spec_key, iso_url))

            if local:
                print(f"Local ({len(local)}):")
                for spec_key, path in local:
                    print(f"  {spec_key:<30} {path}")
                print()

            if download:
                print(f"Download ({len(download)}):")
                for spec_key, url in download:
                    print(f"  {spec_key:<30} {url}")
                print()

            avail = len(download) + len(local)
            print(f"{avail} available, {len(missing)} not available ({len(index)} total)")
            return EXIT_SUCCESS

        if osimager.list_platforms:
            platforms = osimager.get_platforms()
            print("Available platforms:")
            for plat in platforms:
                name = plat.get('name', '')
                if name == 'all':
                    continue
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
            platforms = osimager.get_platforms()
            # Collect all defs from all.json and all platforms
            all_defs = {}
            for plat in platforms:
                name = plat.get('name', '')
                plat_defs = plat.get('defs', {})
                for key, val in plat_defs.items():
                    if key not in all_defs:
                        all_defs[key] = {'value': val, 'source': name}
                    elif name == 'all':
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
                'iso_path': 'from location',
                'vms_path': 'from location',
            }

            print("Base defs (from all.json):")
            for key, info in sorted(all_defs.items()):
                if info['source'] == 'all':
                    print(f"  {key:<20} = {info['value']}")

            print("\nPlatform defs:")
            for key, info in sorted(all_defs.items()):
                if info['source'] != 'all':
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
                    provides = entry.get('provides', {})
                    dist = provides.get('dist', 'unknown')
                    version = provides.get('version', 'unknown')
                    arch = provides.get('arch', 'unknown')
                    iso_flag = " *" if entry.get('iso_local', False) else ""
                    print(f"  {spec_key} ({dist} {version} {arch}){iso_flag}")
            else:
                print("No specs found.")
            return EXIT_SUCCESS

        if not osimager.target:
            print("Usage: mkosimage [OPTIONS] PLATFORM/LOCATION/SPEC [NAME] [IP]")
            print("")

            # Check what the user is missing
            user_dir = osimager.settings['user_dir']
            locations = osimager.get_locations()
            cred_source = osimager.settings.get('credential_source', 'vault')

            examples_dir = os.path.join(osimager.settings['base_dir'], 'data', 'examples')

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
                print("Available platforms/locations:")
                platforms = osimager.get_platforms()
                for plat in platforms:
                    plat_name = plat.get('name', '')
                    plat_locations = [l.get('name', '') for l in locations if plat_name in l.get('platforms', [])]
                    if plat_locations:
                        print(f"  {plat_name}: {', '.join(plat_locations)}")
                print("")
                print("Use --list to see available specs.")

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
        return EXIT_SUCCESS

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
        return EXIT_SUCCESS

    except SystemExit as e:
        return e.code if e.code is not None else EXIT_GENERAL_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return EXIT_GENERAL_ERROR
    except Exception as e:
        print(f"Error: {e}")
        return EXIT_GENERAL_ERROR


def main_mkvenv(argv: Optional[List[str]] = None) -> int:
    """Entry point for mkvenv command."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        osimager = OSImager(argv=argv, which="venv")
        return EXIT_SUCCESS

    except SystemExit as e:
        return e.code if e.code is not None else EXIT_GENERAL_ERROR
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return EXIT_GENERAL_ERROR
    except Exception as e:
        print(f"Error: {e}")
        return EXIT_GENERAL_ERROR
