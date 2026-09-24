
import os
import sys
import json
import glob
import hvac
import tempfile
import shutil
import subprocess
import argparse
import importlib.util
import uuid
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from .utils import *
OSIMAGER_VERSION = "1.9.0"
EXIT_SUCCESS = 0
EXIT_ERROR = 1

class OSImager:
    VERSION = OSIMAGER_VERSION
    
    def __init__(self, argv=None, which="full", extra_args=None):
        self.init_vars()
        self.args = self.init_settings(argv,which,extra_args)
    
    def version(self):
        """Print version information."""
        print(f"OSImager version {self.VERSION}")
        return self.VERSION

    def init_vars(self):
        self.vault = None
        self.secrets = {}
        self.platform = {}
        self.location = {}
        self.spec = {}
        self.defs = {}
        self.evars = {}
        self.variables = {}
        self.pre_provisioners = []
        self.provisioners = []
        self.post_provisioners = []
        self.config = {}
        self.files = []
        self.fqdn = ""

    def init_settings(self, argv, which, extra_args):

        # XDG base directories
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        xdg_cache = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))

        # Default settings
        self.settings = {
            "base_dir": os.path.dirname(os.path.abspath(__file__)),
            "user_dir": os.path.join(xdg_config, "osimager"),
            "data_dir": os.path.join(xdg_data, "osimager"),
            "packer_cmd": "packer",
            "venv_dir": os.environ.get("OSIMAGER_VENV_DIR", os.environ.get("VENV_DIR", os.path.join(xdg_data, "osimager", "venvs"))),
            "ansible_playbook": "config.yml",
            "packer_cache_dir": os.path.join(xdg_cache, "osimager"),
            "iso_path": "/iso",
            "local_only": False,
            "cpu_sockets": 1,
            "cpu_cores": 2,
            "memory": 2048,
            "boot_disk_size": 16384,
            "credential_source": "vault",
            "vault_addr": "",
            "vault_token": ""
        }
#        print("base_dir: "+self.settings['base_dir'])

        parser = argparse.ArgumentParser(description="OSImager configuration and control tool")

        arg_base_defs = {
            "--config": {"flags": ["-c", "--config"], "kwargs": {"default": "config.json", "help": "Path to config.json file", "dest": "config"}},
            "--list": {"flags": ["-l", "--list"], "kwargs": {"default": False, "action": "store_true", "help": "List available specs", "dest": "list"}},
            "--avail": {"flags": ["-a", "--avail"], "kwargs": {"default": False, "action": "store_true", "help": "Show ISO availability for all specs", "dest": "avail"}},
            "--list-platforms": {"flags": ["--list-platforms"], "kwargs": {"default": False, "action": "store_true", "help": "List available platforms", "dest": "list_platforms"}},
            "--list-defs": {"flags": ["--list-defs"], "kwargs": {"default": False, "action": "store_true", "help": "List available defs and their defaults", "dest": "list_defs"}},
            "--init-plugins": {"flags": ["--init-plugins"], "kwargs": {"default": False, "action": "store_true", "help": "Install required Packer plugins for all platforms", "dest": "init_plugins"}},
            "--check-urls": {"flags": ["--check-urls"], "kwargs": {"default": False, "action": "store_true", "help": "Check all ISO download URLs for accessibility", "dest": "check_urls"}},
            "--show-config": {"flags": ["--show-config"], "kwargs": {"default": False, "action": "store_true", "help": "Show current configuration settings", "dest": "show_config"}},
            "--debug": {"flags": ["-d", "--debug"], "kwargs": {"default": False, "action": "store_true", "help": "Enable debug mode", "dest": "debug"}},
            "--verbose": {"flags": ["-v", "--verbose"], "kwargs": {"default": False, "action": "store_true", "help": "Enable verbose output", "dest": "verbose"}},
            "--version": {"flags": ["-V", "--version"], "kwargs": {"default": False, "action": "store_true", "help": "Show version and exit", "dest": "version"}},
            "--arch": {"flags": ["--arch"], "kwargs": {"default": None, "help": "Filter output by architecture (e.g. x86_64, i386, aarch64)", "dest": "arch"}},
            "--set": {"flags": ["--set"], "kwargs": {"action": "append", "help": "Set a setting value (key=value)", "dest": "settings_override"}},
        }

        arg_defs = arg_base_defs
        if which == "full":
            arg_full_defs = {
                "--on_error": {"flags": ["-e", "--on_error"], "kwargs": {"help": "Specify on-error behavior", "dest": "on_error", "default": None}},
                "--log": {"flags": ["-L"], "kwargs": {"default": False, "action": "store_true", "help": "Enable logging", "dest": "log"}},
                "--logfile": {"flags": ["-N", "--logfile"], "kwargs": {"help": "Log file name", "dest": "logfile"}},
                "--force": {"flags": ["-f"], "kwargs": {"default": False, "action": "store_true", "help": "Force mode", "dest": "force"}},
                "--keep": {"flags": ["-k"], "kwargs": {"default": False, "action": "store_true", "help": "Keep files/vms", "dest": "keep"}},
                "--timestamp": {"flags": ["-t"], "kwargs": {"action": "store_true", "help": "Enable timestamping", "dest": "timestamp"}},
                "--fqdn": {"flags": ["-F", "--fqdn"], "kwargs": {"default": None, "help": "Define variables", "dest": "fqdn"}},
                "--define": {"flags": ["-D", "--define"], "kwargs": {"default": None, "help": "Define variables", "dest": "defines"}},
                "--dump-defs": {"flags": ["-x", "--defs"], "kwargs": {"default": False, "action": "store_true", "help": "Dump defs and exit", "dest": "dump_defs"}},
                "--dump-config": {"flags": ["-u", "--dump"], "kwargs": {"default": False, "action": "store_true", "help": "Dump build and exit", "dest": "dump_build"}},
                "--temp": {"flags": ["-m", "--temp"], "kwargs": {"help": "Specify temp directory", "dest": "temp_dir"}},
                "--local-only": {"flags": ["--local", "--local-only"], "kwargs": {"default": False, "action": "store_true", "help": "Use local ISO files instead of downloading", "dest": "local_only"}},
                "--dispatcher": {"flags": ["--dispatcher"], "kwargs": {"default": False, "action": "store_true", "help": "Enable dispatcher progress output (PROGRESS=, ERROR=, RESULT=)", "dest": "dispatcher"}},
                "--skip": {"flags": ["--skip"], "kwargs": {"default": False, "action": "store_true", "help": "Skip post-install configuration", "dest": "skip"}},
                "n": {"flags": ["-n","--dry"], "kwargs": {"default": False, "action": "store_true", "help": "Dry run", "dest": "dry_run"}},
            }
            arg_defs.update(arg_full_defs)

        if extra_args:
            arg_defs.update(extra_args)

        for arg in arg_defs.values():
            parser.add_argument(*arg["flags"], **arg["kwargs"])

        # Add positional argument for target (platform/location/spec)
        if which == "full":
            parser.add_argument('target', nargs='?', help='Target in format platform/location/spec')
            parser.add_argument('name', nargs='?', help='Optional instance name')
            parser.add_argument('ip', nargs='?', help='Optional IP address')

        args = parser.parse_args(argv)

        if args.version:
            self.version()
            sys.exit(0)

        # Set the attributes on the object based on the parsed arguments
        self.config_file = os.path.expanduser(args.config) if args.config else "config.json"
        self.list = args.list
        self.avail = args.avail
        self.list_platforms = args.list_platforms
        self.list_defs = args.list_defs
        self.init_plugins = args.init_plugins
        self.check_urls = args.check_urls
        self.show_config = args.show_config
        self.arch = args.arch
        self.verbose = args.verbose
        self.debug = args.debug
        
        # Store positional arguments if available
        if which == "full" and hasattr(args, 'target'):
            self.target = args.target
            self.name = args.name
            self.ip = args.ip
        else:
            self.target = None
            self.name = None
            self.ip = None
            
        if which == "full":
            self.on_error = args.on_error
            self.log = args.log  # Corrected line: use args.log instead of args.l
            self.logfile = args.logfile
            self.force = args.force
            self.keep = args.keep
            self.timestamp = args.timestamp
            self.dump_defs = args.dump_defs
            self.dump_build = args.dump_build
            self.user_temp_dir = args.temp_dir
            self.local_only = args.local_only
            self.dispatcher = args.dispatcher
            self.dry_run = args.dry_run
            self.skip = args.skip
            self.user_defines = args.defines
            self.fqdn = args.fqdn
        else:
            self.on_error = None
            self.log = False
            self.filename = None
            self.force = False
            self.keep = False
            self.timestamp = False
            self.dump_defs = False
            self.user_temp_dir = None
            self.dry_run = False
            self.skip = False
            self.user_defines = None

        # Load settings from the config file
        self.load_settings(self.config_file)
#        print("settings: "+json.dumps(self.settings,indent=4))

        # Apply settings overrides
        do_save = False
        if args.settings_override:
            for item in args.settings_override:
                if "=" not in item:
                    print(f"Invalid --set format (missing '='): {item}")
                    sys.exit(1)
                key, value = item.split("=", 1)
                if key not in self.settings:
                    print(f"error: invalid setting key: {key}")
                    sys.exit(1)
                new_key = key.strip()
                new_val = value.strip()
                if self.debug: print(f"current_val: {self.settings[new_key]}, new val: {new_val}")
                if self.settings[new_key] != new_val:
                    self.settings[new_key] = new_val
                    if self.verbose:
                        print(f"Overriding setting: {new_key} = {new_val}")
                    do_save = True

        # Apply command line --local-only override (runtime only, not saved)
        if which == "full" and hasattr(args, 'local_only') and args.local_only:
            self.settings['local_only'] = True
            if self.verbose:
                print("Overriding setting: local_only = True (runtime only)")

        if self.debug: print("do_save: "+str(do_save))
        if do_save:
            self.save_settings(self.config_file)
        self.settings['local_only'] = to_bool(self.settings.get('local_only',False))

        self.base_path = self.get_path("base_dir")

        # Baseline data ships inside the package; user_dir overrides it
        self.system_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

        # Ensure user config directories exist
        os.makedirs(os.path.join(self.settings['user_dir'], 'locations'), exist_ok=True)
        # define all the settings in defs
        self.defs.update(self.settings)
        # resolve relative path defs to home directory
        for path_key in ("iso_path", "vms_path"):
            val = self.defs.get(path_key, "")
            if isinstance(val, str) and val and not os.path.isabs(val):
                self.defs[path_key] = os.path.join(os.path.expanduser("~"), val)
        # Also make base_dir available as base_path for compatibility
        self.defs['base_path'] = self.settings['base_dir']

        return args

    def load_settings(self, config_path):
        config_file = os.path.join(self.settings['user_dir'], "config.json")

        if not os.path.exists(config_file):
            if self.verbose:
                print(f"No config file found, using defaults.")
            return

        if self.verbose:
            print(f"Loading settings from: {config_file}")

        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading config file: {e}")
            return

        for key, value in data.items():
            if key in self.settings:
                if key == 'local_only':
                    self.settings[key] = to_bool(value)
                elif key == 'base_dir':
                    self.settings[key] = os.path.abspath(value)
                else:
                    self.settings[key] = value
                if self.verbose:
                    print(f"   Loaded: {key} = {self.settings[key]}")

    def save_settings(self, config_path=""):
        config_dir = self.settings['user_dir']
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.json")

        save_keys = [
            'packer_cmd', 'packer_cache_dir', 'iso_path', 'local_only',
            'cpu_sockets', 'cpu_cores', 'memory', 'boot_disk_size',
            'ansible_playbook',
            'credential_source', 'vault_addr', 'vault_token'
        ]

        data = {}
        for key in save_keys:
            if key in self.settings:
                data[key] = self.settings[key]

        try:
            with open(config_file, 'w') as f:
                json.dump(data, f, indent=4)
                f.write('\n')
            if self.verbose:
                print(f"Settings saved to: {config_file}")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get_path(self, what, *paths):
        if not isinstance(what, str):
            return None

        if self.debug: print("get_path: what: "+what)
        what_dir = self.settings[what]
        if self.debug: print("get_path: what_dir: "+what_dir)
        
        # Handle special directory cases - these are all relative to base_dir unless absolute
        if what in ["base_dir", "data_dir"]:
            if what == "base_dir":
                what_path = what_dir  # base_dir is always absolute
            else:
                # For other directory settings, check if absolute or relative to base_path
                if what_dir.startswith("/"):
                    what_path = what_dir
                else:
                    what_path = os.path.join(self.base_path, what_dir)
        else:
            # For other paths, check if it's absolute or relative to base_path
            if what_dir.startswith("/"):
                what_path = what_dir
            else:
                what_path = os.path.join(self.base_path, what_dir)
        
        if self.debug: print("get_path: what_path: "+what_path)

        path = os.path.join(what_path, *paths)
        if self.debug: print("get_path: returning: "+path)
        return path

    def resolve_data_path(self, *parts):
        """Resolve a data file path with two-layer lookup.

        Checks user_dir first (overrides), then osimager_data package (baseline).
        Returns the first path that exists, or None.
        """
        # Layer 1: user override
        user_path = os.path.join(self.settings['user_dir'], *parts)
        if os.path.exists(user_path):
            return user_path

        # Layer 2: osimager_data package
        if self.system_data_dir:
            system_path = os.path.join(self.system_data_dir, *parts)
            if os.path.exists(system_path):
                return system_path

        return None

    def resolve_data_files(self, subdir, pattern="*.json"):
        """Scan both user dir and system data dir, merging results.

        User dir files take precedence over system files with the same name.
        For specs (which are subdirectories), keys by the directory name.
        Returns list of file paths.
        """
        seen = {}

        # Layer 1: user overrides (take precedence)
        user_dir = os.path.join(self.settings['user_dir'], subdir)
        if os.path.isdir(user_dir):
            for f in find_files(user_dir, pattern):
                # Key by relative path from the subdir (handles nested specs)
                rel = os.path.relpath(f, user_dir)
                seen[rel] = f

        # Layer 2: system baseline (fills in missing)
        if self.system_data_dir:
            system_dir = os.path.join(self.system_data_dir, subdir)
            if os.path.isdir(system_dir):
                for f in find_files(system_dir, pattern):
                    rel = os.path.relpath(f, system_dir)
                    if rel not in seen:
                        seen[rel] = f

        return list(seen.values())

    def load_specific(self, data, debug = False):
#        if debug: print("data: "+json.dumps(data,indent=4))
        specifics = [ "platform", "location", "dist", "version", "arch", "firmware" ]
        sections = {"files", "evars", "defs", "variables", "pre_provisioners", "provisioners", "post_provisioners", "config", "method", "merge"}
        specific_keys = {s + "_specific" for s in specifics}
        for section in specifics:
            if debug: print(f"section: {section}")
            name_key = section
            if debug: print(f"name_key: {name_key}")
            name = self.defs.get(name_key,None)
            if debug: print(f"name: {str(name)}")
            if name:
                data_key = section + "_specific"
                if debug: print(f"data_key: {data_key}")
                specific_data = data.get(data_key, [])
                if debug: print("specific_data: "+json.dumps(specific_data,indent=4))
                for entry in specific_data:
                    specific_data_name = entry.pop(section,"")
                    if debug: print(f"specific_data_name: {specific_data_name}")
                    if re.fullmatch(specific_data_name, name, re.IGNORECASE):
                        if debug: print("====> loading!")
                        self.load_data(entry,False)
                        # Hoist scalar fields (e.g. ansible_version) onto parent data so they
                        # survive into self.spec. Known sections and *_specific keys
                        # are already handled by load_data/load_specific recursion.
                        for key, val in entry.items():
                            if key not in sections and key not in specific_keys:
                                data[key] = val

    def load_data(self, data, debug = False):

        # List of sections to process
        sections = ["files", "evars", "defs", "variables", "pre_provisioners", "provisioners", "post_provisioners", "config"]

        if debug:
            print("********************************************************************************")
            print("**** DATA ****")
            print("data: "+json.dumps(data,indent=4))
            print("**** BEFORE ****")
            for section in sections:
                attr = getattr(self, section, None)
                print(f"{section}: ")
                print(json.dumps(attr,indent=4))
                print("")

        method = data.pop('method',"merge")
        for section in sections:
            new_val = data.get(section, None)
            if new_val is None:
                continue  # Skip if no new value for the section

            # Retrieve the current attribute value dynamically
            attr = getattr(self, section, None)

            # Protect platform_defs keys from being overwritten
            if section == "defs":
                protected = getattr(self, 'platform_defs', {})
                if protected and isinstance(new_val, dict):
                    new_val = {k: v for k, v in new_val.items() if k not in protected}

            if isinstance(new_val,dict):
#                merge_or_replace(attr,new_val,method)
                merge = new_val.pop("merge",[])
                for key in merge:
                    key_val = new_val.pop(key,None)
                    if key_val:
                        if key in attr:
                            if isinstance(attr[key],dict):
                                attr[key].update(key_val)
                            elif isinstance(attr[key], list):
                                attr[key].extend(key_val)
                            else:
                                attr[key] = key_val
                        else:
                            attr[key] = key_val

            # If it's a dictionary, merge or replace its contents
            if isinstance(attr, dict):
                 attr.update(new_val)  # Merge data into the current dictionary

            # If it's a list, update or replace it
            elif isinstance(attr, list):
                if method != "merge":
                    attr[:] = []  # Clear the existing list first
                attr.extend(new_val)  # Append new data to the list

            # Optionally, handle other types if needed (e.g., strings, integers)
            else:
                setattr(self, section, new_val)  # Set the new value directly

        if debug:
            print("**** AFTER ****")
            for section in sections:
                attr = getattr(self, section, None)
                print(f"{section}: ")
                print(json.dumps(attr,indent=4))
                print("")

        self.load_specific(data,debug)

    def read_data(self, file_path):
        """Load a JSON or TOML file based on extension."""
        debug = False
        if debug: print("file_path: "+str(file_path))
        if file_path is None:
            return None

        if self.verbose:
            print("Loading file: " + str(file_path))

        try:
            if str(file_path).endswith('.toml'):
                with open(file_path, 'rb') as f:
                    data = tomllib.load(f)
            else:
                with open(file_path, 'r') as f:
                    data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError, tomllib.TOMLDecodeError) as e:
            print(f"Error loading file '{file_path}': {e}")
            show_caller()
            sys.exit(1)

        return data

    def load_inc(self, where, what, data):
        debug = False

        if debug: print(f"load_inc: where: {where}, what: {what}")
        if what is None:
            return None

        if debug: print("load_inc: calling load_data_file...")
        inc_data = self.load_data_file(where, what)
        if debug: print("load_inc: loading data...")
        self.load_data(data);
        if debug: print("load_inc: updating inc_data...")
        inc_data.update(data)

        if debug: print("load_inc: returning inc_data...")
        return inc_data

    def load_file(self, where, file_path):
        debug = False

        if debug: print(f"load_file: where: {where}, file_path: {file_path}")
        data = self.read_data(file_path)
#        print("data: "+json.dumps(data,indent=4))

        # recursively load includes before this data
        incs = data.pop("include",None)
        if debug: print("load_file: incs: "+str(incs))
        if incs:
            if debug: print("load_file: incs type: "+str(type(incs)))
            if isinstance(incs,list):
                for inc in incs:
                    data = self.load_inc(where, inc, data)
            elif isinstance(incs,str):
                data = self.load_inc(where, incs, data)

        else:
            self.load_data(data)

        return data

    def load_data_file(self, where, what):
        debug = False

        if debug: print(f"load_data_file: where: {where}, what: {what}")
        if what is None:
            return None

        if where == 'specs':
            file_path = self.resolve_data_path(where, what, 'spec.json')
            if not file_path:
                print(f"error: spec '{what}' not found")
                print(f"  Install baseline data: pip install osimager-data")
                print(f"  Or create your own:    {self.settings['user_dir']}/specs/")
                sys.exit(1)
        elif where == 'locations':
            # Locations support .json and .toml — JSON takes priority
            loc_dir = os.path.join(self.settings['user_dir'], "locations")
            if not what.endswith(('.json', '.toml')):
                json_path = os.path.join(loc_dir, what + ".json")
                toml_path = os.path.join(loc_dir, what + ".toml")
                file_path = json_path if os.path.exists(json_path) else toml_path
            else:
                file_path = os.path.join(loc_dir, what)
        else:
            what_file = what if what.endswith(".json") else what + ".json"
            file_path = self.resolve_data_path(where, what_file)
            if not file_path:
                print(f"error: {where} '{what}' not found")
                print(f"  Install baseline data: pip install osimager-data")
                print(f"  Or create your own:    {self.settings['user_dir']}/{where}/")
                sys.exit(1)
        if debug: print("load_data_file: file_path: "+str(file_path))

        return self.load_file(where,file_path)

    def old_load_file(self, where, what):
        debug = False
        if what is None:
            return None

        if debug: print(f"where: {where}, what: {what}")
        if not what.endswith(".json"):
            what += ".json"  # Add .json extension if not present

        file_name = self.get_path(where, what)
        if self.verbose: 
            print("Loading file: " + file_name)

        try:
            with open(file_name, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            print(f"Error loading JSON file '{file_name}': {e}")
            show_caller()
            sys.exit(1)

        # recursively load includes before this data
        inc = data.pop("include",None)
        if inc:
            print(f"including: {where}/{inc}")
            inc_data = self.load_file(where, inc)
            if debug: print("inc_data: "+str(inc_data))
            self.load_data(data)
            if debug: print("data: "+str(data))
            inc_data.update(data)
            data = inc_data
        else:
            self.load_data(data)

        return data

    def load_secrets(self):
        """Load secrets from ~/.config/osimager/secrets file.

        Format: path key1=value1 key2=value2 ...
        Example: images/linux username=root password=T3mp@dm1n!
        Lines starting with # are comments.
        """
        secrets_path = os.path.join(self.settings['user_dir'], "secrets")
        if self.verbose: print("load_secrets: loading from: "+secrets_path)

        if not os.path.exists(secrets_path):
            print("error: Secrets file not found!")
            print(f"Please create {secrets_path} with the following format:")
            print("  images/linux username=root password=YourPassword")
            print("  images/windows username=Administrator password=YourPassword")
            print("  vsphere/lab server=vcenter.local username=admin password=YourPassword")
            return True

        try:
            with open(secrets_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    path = parts[0]
                    self.secrets[path] = {}
                    for pair in parts[1:]:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            self.secrets[path][key] = value
        except IOError as e:
            print(f"error: Unable to read secrets file {secrets_path}: {e}")
            return True

        if self.debug: print("load_secrets: loaded "+str(len(self.secrets))+" entries")
        return False

    def load_credentials(self):
        """Load credentials based on credential_source setting."""
        source = self.settings.get('credential_source', 'vault')
        if self.verbose: print("load_credentials: source: "+source)

        if source == "config":
            return self.load_secrets()

        # credential_source == "vault"
        vault_addr = self.settings.get('vault_addr', '')
        vault_token = self.settings.get('vault_token', '')

        if not vault_addr or not vault_token:
            print("error: Vault credentials not configured!")
            print("Set them with:")
            print("  mkosimage --set vault_addr=http://your-vault-server:8200")
            print("  mkosimage --set vault_token=your-vault-token")
            print("")
            print("Or switch to config-based secrets:")
            print("  mkosimage --set credential_source=config")
            print(f"  Then create {os.path.join(self.settings['user_dir'], 'secrets')}")
            return True

        if self.debug: print("load_credentials: addr: "+vault_addr)
        self.vault = hvac.Client(url=vault_addr, token=vault_token)
        try:
            if self.vault.is_authenticated():
                self.defs['vault_addr'] = vault_addr
                self.defs['vault_token'] = vault_token
                return False
        except:
            if self.verbose: print("load_credentials: Vault authentication failed (sealed?)")
            return True

        print("error: Vault authentication failed!")
        print(f"Check vault_addr ({vault_addr}) and vault_token settings.")
        return True

    def get_secret(self, string, verbose=False):
        """Get a secret value. Dispatches to vault or local secrets based on credential_source."""
        if verbose: print("get_secret: string: "+string)

        i = string.find(":")
        if i < 0:
            full_path = string
            subkey = None
        else:
            full_path = string[:i]
            subkey = string[i+1:]

        if self.secrets:
            entry = self.secrets.get(full_path, {})
            if subkey:
                val = entry.get(subkey, "")
            else:
                val = str(entry)
            if verbose: print("get_secret: returning: "+str(val))
            return val

        if self.vault:
            return get_vault(self.vault, string, verbose)

        print(f"error: no credential source available for: {string}")
        return ""

    def resolve_packer_vault_refs(self, data):
        """Replace Packer {{vault `path` `key`}} references with values from secrets."""
        if not self.secrets:
            return data

        pattern = re.compile(r'\{\{vault\s+`([^`]+)`\s+`([^`]+)`\}\}')

        if isinstance(data, dict):
            return {k: self.resolve_packer_vault_refs(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.resolve_packer_vault_refs(item) for item in data]
        elif isinstance(data, str):
            def replacer(match):
                path = match.group(1)
                key = match.group(2)
                entry = self.secrets.get(path, {})
                val = entry.get(key, "")
                if not val:
                    print(f"warning: secret not found: {path}/{key}")
                return val
            return pattern.sub(replacer, data)
        else:
            return data

    def get_platforms(self,names = None):
        debug = False
        files = self.resolve_data_files("platforms", "*.json")
        if debug: print("files: "+str(files))
        platforms = []
        for file_name in files:
            if debug: print(f"file_name: {file_name}")
            try:
               with open(file_name, 'r') as f:
                    data = json.load(f)
                    f.close()
            except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
                print(f"Error loading JSON file '{file_name}': {e}")
                sys.exit(1)

            name = os.path.basename(file_name).removesuffix(".json")
            if debug: print(f"name: {name}, names: {str(names)}")
            if names:
                match = False
                for re_name in names:
                   if re.search(re_name, name, re.IGNORECASE):
                    match = True
            else:
                match = True
#            if not names or name in names:
            if match:
                if debug: print(f"get_platforms: adding: {name}")
                data['name'] = name
                platforms.append(data)

        return sorted(platforms, key=lambda x: x["name"])

    def get_locations(self, platform_names = None):
        debug = False
        if debug: print(f"platform_names: {str(platform_names)}")
        loc_dir = os.path.join(self.settings['user_dir'], "locations")
        # Find both JSON and TOML files; JSON takes priority over TOML
        json_files = find_files(loc_dir, '*.json')
        toml_files = find_files(loc_dir, '*.toml')
        # Build a dict keyed by base name — JSON first so it wins
        seen = {}
        for f in json_files:
            name = os.path.basename(f).removesuffix(".json")
            seen[name] = f
        for f in toml_files:
            name = os.path.basename(f).removesuffix(".toml")
            if name not in seen:
                seen[name] = f
        if debug: print("files: "+str(seen))
        locations = []
        for name, file_name in seen.items():
            if debug: print(f"file_name: {file_name}")
            data = self.read_data(file_name)

            data['name'] = name

            location_platforms = data.get('platforms',None)
            if platform_names and location_platforms:
                # If platform_names specified, only include locations that support those platforms
                for plat in location_platforms:
                    if plat in platform_names:
                        locations.append(data)
                        break
            else:
                # If no platform_names specified, include all locations
                locations.append(data)

        return sorted(locations, key=lambda x: x["name"])

    def get_specs(self,search_string = '.*'):
        debug = False

        if not search_string or search_string == "all":
            search_string = ".*"
        files = self.resolve_data_files("specs", "*.json")
        if debug: print("get_specs: files: "+str(files))
        specs = []
        for file_name in files:
            if debug: print(f"get_specs: file_name: {file_name}")
            try:
               with open(file_name, 'r') as f:
                    data = json.load(f)
                    f.close()
            except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
                print(f"Error loading JSON file '{file_name}': {e}")
                sys.exit(1)
            spec_dir = os.path.dirname(file_name)
            spec_name = os.path.basename(spec_dir)
            if re.search(search_string, spec_name, re.IGNORECASE):
                data['name'] = spec_name
                specs.append(data)

        return sorted(specs, key=lambda x: x["name"])

    def spec_get_provides(self, file_name, data):
        debug = False
        provides = data.get("provides",None)
        if debug: print("provides: "+json.dumps(provides,indent=4))
        if not provides:
            return []
#        checkit(provides, f"error: spec file {file_name} provides section has no dist!")
        dist = provides.get("dist",None)
        checkit(dist, f"error: spec file {file_name} provides section has no dist!")
        versions = provides.get("versions",None)
        checkit(versions, f"error: spec file {file_name} provides section has no versions!")
        default_arches = provides.get("arches",None)
        if isinstance(versions,list):
            version_list = []
            for vstr in versions:
                version_list.extend(explode_string_with_dynamic_range(vstr,debug))
        else:
            version_list = explode_string_with_dynamic_range(versions,debug)
        provide_list = []
        for version in version_list:
            if debug: print("version: "+version)
            # Determine arches for this version: check version_specific overrides first
            version_arches = default_arches
            for vs in data.get("version_specific", []):
                vs_ver = vs.get("version", "")
                if re.fullmatch(vs_ver, version, re.IGNORECASE):
                    if "arches" in vs:
                        version_arches = vs["arches"]
            provide_entry = {
                "dist": dist,
                "version": version
            }
            if version_arches:
                provide_entry["arches"] = version_arches
            provide_list.append(provide_entry)

        return provide_list

    def resolve_url_field(self, data, version, arch, field):
        """Resolve a URL-valued spec field (iso_url, disk_image_url, ...) for a
        given version/arch. Applies arch_specific and version_specific overrides
        (version_specific arch_specific wins last) and >>var<< / E>...<E
        substitution. Returns the resolved string, or None if unset/blank."""
        parts = version.split('.')
        major = parts[0] if len(parts) > 0 else ""
        minor = parts[1] if len(parts) > 1 else ""
        subs = {
            ">>version<<": version,
            ">>major<<": major,
            ">>minor<<": minor,
            ">>arch<<": arch,
        }
        # check defs for the field
        url = data.get("defs", {}).get(field, "")
        # check top-level arch_specific overrides
        for a_s in data.get("arch_specific", []):
            if a_s.get("arch", "") == arch:
                a_s_defs = a_s.get("defs", {})
                if field in a_s_defs:
                    url = a_s_defs[field]
        # check version_specific overrides
        for vs in data.get("version_specific", []):
            vs_ver = vs.get("version", "")
            if re.fullmatch(vs_ver, version, re.IGNORECASE):
                vs_defs = vs.get("defs", {})
                if field in vs_defs:
                    url = vs_defs[field]
                # check arch_specific within version_specific
                for a_s in vs.get("arch_specific", []):
                    if a_s.get("arch", "") == arch:
                        a_s_defs = a_s.get("defs", {})
                        if field in a_s_defs:
                            url = a_s_defs[field]
        if not url:
            return None
        # basic substitution (per-iteration values not in self.defs)
        for k, v in subs.items():
            url = url.replace(k, v)
        # resolve remaining >>var<< markers from spec defs, then self.defs as fallback
        spec_defs = data.get("defs", {})
        remaining = re.findall(r'>>(.*?)<<', url)
        for var in remaining:
            val = spec_defs.get(var, self.defs.get(var, ""))
            if val:
                val = str(val)
                for k, v in subs.items():
                    val = val.replace(k, v)
                # evaluate E>...<E expressions in the def value
                while 'E>' in val and '<E' in val:
                    s = val.index('E>')
                    e = val.index('<E') + 2
                    try:
                        val = val[:s] + str(eval(val[s+2:e-2])) + val[e:]
                    except Exception:
                        break
                url = url.replace(f">>{var}<<", val)
        # evaluate E>...<E expressions in the URL itself
        while 'E>' in url and '<E' in url:
            start = url.index('E>')
            end = url.index('<E') + 2
            expr = url[start+2:end-2]
            try:
                result = str(eval(expr))
                url = url[:start] + result + url[end:]
            except Exception:
                break
        return url

    def resolve_iso_url(self, data, version, arch):
        """Best-effort resolve iso_url from spec data for a given version/arch."""
        return self.resolve_url_field(data, version, arch, "iso_url")

    def resolve_disk_image_url(self, data, version, arch):
        """Resolve disk_image_url (qcow2/vmdk/ova) for image-import builds -- the
        disk-image analogue of resolve_iso_url. Appliances that ship a prebuilt
        image instead of an installer ISO declare disk_image_url; the import
        builder consumes it as input rather than booting an installer."""
        return self.resolve_url_field(data, version, arch, "disk_image_url")

    def check_iso_local(self, iso_url):
        """Check if an ISO file exists locally (file:// path, iso_path setting, or packer cache)."""
        if not iso_url:
            return False
        if iso_url.startswith("file://"):
            path = iso_url[7:]
            return os.path.isfile(path)
        # for remote URLs, extract filename and search known locations
        iso_name = get_filename_from_url(iso_url)
        if not iso_name:
            return False
        # check iso_path from settings (already resolved to absolute in __init__)
        iso_path = self.defs.get('iso_path', '/iso')
        if iso_path and os.path.isfile(os.path.join(iso_path, iso_name)):
            return True
        # check packer cache
        cache_dir = self.settings.get('packer_cache_dir', '/tmp')
        if os.path.isfile(os.path.join(cache_dir, iso_name)):
            return True
        return False

    def make_index(self):
        debug = False
        arches = []
        platforms = self.get_platforms()
        for plat in platforms:
            plat_arches = plat.get('arches',[])
            for arch in plat_arches:
                if not arch in arches:
                    arches.append(arch)
                if arch == 'x86_64':
                    if not 'amd64' in arches:
                        arches.append('amd64')
        locations = self.get_locations()
        for loc in locations:
            loc_arches = loc.get('arches',[])
            for arch in loc_arches:
                if not arch in arches:
                    arches.append(arch)
                if arch == 'x86_64':
                    if not 'amd64' in arches:
                        arches.append('amd64')
        if debug: print("arches: "+str(arches))
        index = {}
#        specs = self.get_specs()
#        print("specs: "+str(specs))
        files = self.resolve_data_files("specs", "*.json")
        for file_name in files:
            try:
               with open(file_name, 'r') as f:
                    data = json.load(f)
                    f.close()
            except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
                print(f"Error loading JSON file '{file_name}': {e}")
                show_caller()
                sys.exit(1)

            spec_provides = self.spec_get_provides(str(file_name), data)
            if debug: print("spec_provides: "+json.dumps(spec_provides,indent=4))
            for entry in spec_provides:
                dist = entry.get('dist',"")
                version = entry.get('version',"")
                # Use per-spec arches intersected with global (environment) arches
                spec_arches = entry.get('arches', None)
                if spec_arches:
                    # Add amd64 alias when x86_64 is present
                    spec_arches = list(spec_arches)
                    if 'x86_64' in spec_arches and 'amd64' not in spec_arches:
                        spec_arches.append('amd64')
                    entry_arches = [a for a in spec_arches if a in arches]
                else:
                    entry_arches = arches
                for arch in entry_arches:
                    iso_url = self.resolve_iso_url(data, version, arch)
                    disk_image_url = self.resolve_disk_image_url(data, version, arch)
                    # A spec/version/arch is buildable if it provides either an
                    # installer ISO or a prebuilt disk image to import.
                    if not iso_url and not disk_image_url:
                        continue
                    key = dist + "-" + version + "-" + arch
                    entry = {
                        "provides": {
                            "dist": dist,
                            "version": version,
                            "arch": arch
                        },
                        "path": str(file_name),
                        "iso_url": iso_url or "",
                        "iso_local": self.check_iso_local(iso_url) if iso_url else False
                    }
                    if disk_image_url:
                        entry["disk_image_url"] = disk_image_url
                        entry["disk_image_local"] = self.check_iso_local(disk_image_url)
                        entry["image_import"] = True
                    index[key] = entry

        sorted_index = {k: index[k] for k in sorted(index, key=natural_key)}
        return sorted_index

    def get_index(self,name = None):
        index = self.make_index()
        if self.arch and not name:
            index = {k: v for k, v in index.items() if v.get('provides', {}).get('arch') == self.arch}
        return index.get(name,None) if name else index

    def get_iso_file(self,urls):
        debug = False
        if debug: print("get_iso_file: urls: "+str(urls))
        if not isinstance(urls,list):
            print("get_iso_file: spec error: urls is not a list")
            sys.exit(1)
        
        # Only do the 1st entry
        for entry in urls:
            if debug: print("get_iso_file: url: "+str(entry))
            iso_url = entry.get('url',None)
            if not iso_url: continue
            if debug: print("get_iso_file: iso_url: "+iso_url)
            if iso_url.startswith("/"):
                iso_name = os.path.basename(iso_url)
                self.defs['iso_name'] = iso_name
                iso_path = os.path.dirname(iso_url)
                self.defs['iso_path'] = iso_path
            else:
                iso_name = get_filename_from_url(iso_url)
                iso_path = os.path.join(self.settings.get('packer_cache_dir',"/tmp"), iso_name)
            if debug: print(f"get_iso_file: iso_name: {iso_name}, iso_path: {iso_path}")

            self.config.pop('iso_urls',None)
            self.defs['iso_file'] = iso_path
            self.defs['iso_name'] = iso_name
            self.defs['iso_checksum'] = 'none'
            return True

        return False

    def check_iso_urls(self,urls):
        debug = False
        if debug: print("urls: "+str(urls))
        if not isinstance(urls,list):
            print("spec error: urls is not a list")
            sys.exit(1)
        
        for entry in urls:
            if debug: print("url: "+str(entry))
            iso_url = entry.get('url',None)
            if not iso_url: continue
            if debug: print("iso_url: "+iso_url)
            if check_url(iso_url,debug):
                iso_name = get_filename_from_url(iso_url)
                if debug: print("iso_name: "+iso_name)
                cache_path = self.settings.get('packer_cache_dir',None) or "/tmp"
                if debug: print("cache_path: "+str(cache_path))
                iso_path = os.path.join(self.settings.get('packer_cache_dir',"/tmp"), iso_name)
                if debug: print("iso_path: "+iso_path)
                # iso_url is working, check the checksum
                sum_url = entry.get('checksum',None)
                if debug: print("sum_url: "+str(sum_url))
                checksum = None
                if sum_url:
                    if debug: print("checking: "+sum_url)
                    if not check_url(sum_url,debug):
                        continue
                    checksum = get_checksum(sum_url,iso_url,debug)
                if debug: print("checksum: "+str(checksum))
                if not checksum:
                    checksum = "none"

                if checksum:
                   self.defs['iso_name'] = iso_name
                   self.defs['iso_url'] = iso_url
                   self.defs['iso_checksum'] = checksum
                   return True

        # Not found
        return False

    def make_build(self, target, name=None, ip=""):
        debug = False

        settings = self.settings

        tuple = target.split('/')
        if len(tuple) < 3:
            raise ValueError("Target must be in format platform/location/spec")
    
        platform_name = tuple[0]
        platform_file = self.resolve_data_path("platforms", platform_name + ".json")
        if not platform_file:
            valid = [os.path.basename(f).removesuffix(".json")
                     for f in sorted(self.resolve_data_files("platforms", "*.json"))
                     if os.path.basename(f).removesuffix(".json") not in ("none",)]
            print(f"error: unknown platform '{platform_name}'")
            if valid:
                print(f"valid platforms: {', '.join(valid)}")
            else:
                print(f"  No platforms found. Install baseline data: pip install osimager-data")
            sys.exit(1)
        self.defs['platform'] = platform_name
        location_name = tuple[1]
        self.defs['location'] = location_name
        spec_name = tuple[2]

        # This has to be done early
        index_entry = self.get_index(spec_name)
        if not index_entry:
            print(f"spec {spec_name} not found")
            sys.exit(1)
        spec_provides = index_entry.get('provides',{})
        dist = spec_provides.get('dist',"")
        self.defs['dist'] = dist
        version = spec_provides.get('version',"")
        self.defs['version'] = version
        arch = spec_provides.get('arch',"")
        self.defs['arch'] = arch
        if debug: print(f"dist: {dist}, version: {version}, arch: {arch}")

        instance_name = name or spec_name

        if self.verbose:
            print("instance_name: "+instance_name)
    
        # pre-define some standard environment variables
        self.evars = {
            "ANSIBLE_RETRY_FILES_ENABLED": "False",
            "ANSIBLE_WARNINGS": "False",
            "ANSIBLE_NOCOWS": "1",
            "ANSIBLE_DISPLAY_SKIPPED_HOSTS": "False",
            "ANSIBLE_STDOUT_CALLBACK": "minimal"
        }

        self.defs['install_path'] = os.path.join(self.settings['user_dir'], "install")

        # Need to create the default provisioner here (in case of replacement by any files)
        self.provisioners = [
            {
                "type": "ansible",
                "playbook_file": ">>ansible_playbook<<",
                "extra_arguments": [
                    "[>ansible_extra_args<]",
                    "--extra-vars",
                    "platform={{user `platform-name`}} location_name={{user `location-name`}} spec_name={{user `spec-name`}} spec_config={{user `spec-config`}} install_dir=\">>install_path<<\" {{user `ansible-opts`}} >>ansible_extra_vars<<"
                ]
            }
        ]
        self.defs['ansible_playbook'] = self.settings['ansible_playbook']

        # In order for "dist/version/arch_specific" to work they have to be defined before load

        # Platform
        self.platform = self.load_data_file("platforms", platform_name)
        self.defs['platform_name'] = platform_name

        # Save and apply platform_defs (these cannot be overridden by specs)
        self.platform_defs = self.platform.get("platform_defs", {})
        if self.platform_defs:
            self.defs.update(self.platform_defs)
        
        # Set platform_type from the platform config type field
        platform_type = self.config.get('type', platform_name)
        self.defs['platform_type'] = platform_type
        if self.debug: print(f"platform_type set to: {platform_type}")

        # Location
        self.location = self.load_data_file("locations", location_name)
        self.defs['location_name'] = location_name

        # Spec
        spec_path = index_entry.get('path',{})
        if self.debug: print("spec_path: "+str(spec_path))
        self.spec = self.load_file('specs',spec_path)
        self.defs['spec_name'] = spec_name

        # A spec can opt out of post-install configuration (e.g. Proxmox VE, an
        # appliance that configures itself from its answer file and ships no
        # sudo). Honor it exactly like the --skip flag.
        if self.spec.get('skip_config') and not self.skip:
            self.skip = True
            if self.verbose:
                print(f"spec '{spec_name}' requests skip_config: skipping post-install configuration")

#        self.evars["ANSIBLE_ROLES_PATH"] = self.spec_path

        # Set PATH to prioritize ansible venv if specified
        ansible_version = self.spec.get("ansible_version", None)
        if ansible_version and not self.skip:
            venv_bin_path = self.get_path('venv_dir', ansible_version, 'bin')
            current_path = os.environ.get('PATH', '')
            self.evars["PATH"] = f"{venv_bin_path}:{current_path}"

        if "platforms" in self.location and platform_name not in self.location["platforms"]:
            raise Exception(f"location {location_name} does not support platform {platform_name}")
        if "platforms" in self.spec and platform_name not in self.spec["platforms"]:
            raise Exception(f"spec {spec_name} does not support platform {platform_name}")
        if "locations" in self.spec and location_name not in self.spec["locations"]:
            raise Exception(f"spec {spec_name} does not support location {location_name}")
    
        self.config['name'] = spec_name

        # Break out version and major.minor
        vparts = version.split(".")
        major = vparts[0]
        if len(vparts) > 1:
            minor = vparts[1]
        else:
            minor = ""
        if self.debug: print(f"major: {major}, minor: {minor}")

        if not self.defs.get("boot", True):
            self.config.pop("boot_command", None)
            self.config.pop("boot_wait", None)
        if not self.defs.get("shutcmd", True):
            self.config.pop("shutdown_command", None)
    
        if self.user_temp_dir:
            self.temp_dir = self.user_temp_dir
        else:
            self.temp_dir = tempfile.mkdtemp()
        if self.verbose: print("temp_dir: "+self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
    
        # Add spec_dir definition - directory containing the spec file
        spec_dir = os.path.dirname(spec_path)
        
        self.build_id = "packer-" + uuid.uuid4().hex[:12]
        self.defs.update({
            "base_path": self.settings['base_dir'],
            "data_path": self.system_data_dir or self.get_path("data_dir"),
            "user_dir": self.settings['user_dir'],
            "temp_dir": self.temp_dir,
            "tmpdir": self.temp_dir,
            "spec_dir": spec_dir,
            "build_id": self.build_id,
            "dist": dist,
            "version": version,
            "major": major,
            "minor": minor,
            "arch": arch
        })

        # Normalize path defs - resolve relative paths to home directory (location may override settings)
        for path_key in ("iso_path", "vms_path"):
            val = self.defs.get(path_key, "")
            if isinstance(val, str) and val:
                if not os.path.isabs(val):
                    val = os.path.join(os.path.expanduser("~"), val)
                self.defs[path_key] = val.rstrip("/")

        self.variables.update({
            "platform-name": platform_name,
            "location-name": location_name,
            "spec-name": spec_name,
            "spec-config": self.defs.get("spec_config","tasks/spec.yml"),
        })
    
        dns = self.defs.get("dns", {})
        self.defs["dns_search"] = ' '.join(dns.get("search", []))
        for i, dns_server in enumerate(dns.get("servers", []), 1):
            self.defs[f"dns{i}"] = dns_server
    
        ntp = self.defs.get("ntp", {})
        for i, ntp_server in enumerate(ntp.get("servers", []), 1):
            self.defs[f"ntp{i}"] = ntp_server
    
        self.defs["name"] = instance_name
        if self.fqdn:
            fqdn = self.fqdn
        elif name and '.' in name:
            fqdn = name
        else:
            fqdn = instance_name + "." + self.defs.get('domain',"")
        self.defs["fqdn"] = fqdn

        self.variables.update({
            "name": instance_name,
            "fqdn": fqdn
        })

        cidr = self.defs.get("cidr", "/")
        if "/" in cidr:
            subnet, prefix = cidr.split("/")
            self.defs["subnet"] = subnet
            self.defs["prefix"] = prefix
        else:
            subnet = prefix = ""
    
        gateway = self.defs.get("gateway", "")
        if not gateway and subnet and prefix:
            gateway = str(ipaddress.IPv4Network(f"{subnet}/{prefix}")[-2])
        self.defs["gateway"] = self.defs["gw"] = gateway
    
        netmask = self.defs.get("netmask")
        if not netmask and prefix:
            self.defs["netmask"] = prefix_to_netmask(prefix)

        if not ip:
            ip = get_ip(fqdn, self.location.get("defs",{}).get("dns",{}))
            if ip is None:
                 ip = ""
        self.defs["ip"] = ip
    
        # process user_defines, if any
        if self.debug: print("user_defines: "+str(self.user_defines))
        if self.user_defines:
            deflist = self.user_defines.split(",")
            for pair in deflist:
                key, value = pair.split("=", 1)
                if not len(key) or not len(value):
                    print(f"invalid define key/value pair: {key}={value}")
                    sys.exit(1)
                new_key = key.strip()
                new_val = value.strip()
                self.defs[new_key] = new_val

        if self.verbose:
           print(f"platform: {platform_name}, location: {location_name}, spec: {spec_name}, fqdn: {fqdn}, ip: {ip}")

        # Check if a urls definition exists (array of dict)
        urls = self.defs.get("urls",[])
        if debug: print(f"urls: {str(urls)}")
        local = self.defs.get('local_only',True)
        if local:
            self.get_iso_file(do_sub(urls,self))
        else:
            self.check_iso_urls(do_sub(urls,self))

        # If iso_url is defined and iso_name isnt defined in defs, fix that
        iso_url = self.defs.get("iso_url",None)
        if iso_url and not self.defs.get("iso_name",None):
            if iso_url.startswith("/"):
                iso_name = os.path.basename(iso_url)
                self.defs['iso_name'] = iso_name
            else:
                iso_name = get_filename_from_url(iso_url)
            if debug: print(f"get_iso_file: iso_name: {iso_name}, iso_path: {iso_path}")
            self.defs['iso_name'] = iso_name

        # Image-import builds: derive disk_image_name and flag the build so the
        # platform builder can branch (boot a prebuilt image instead of an ISO).
        disk_image_url = self.defs.get("disk_image_url", None)
        if disk_image_url and not self.defs.get("disk_image_name", None):
            if disk_image_url.startswith("/"):
                self.defs['disk_image_name'] = os.path.basename(disk_image_url)
            else:
                self.defs['disk_image_name'] = get_filename_from_url(disk_image_url)
        self.defs['image_import'] = "true" if disk_image_url else ""

        # Load credentials - fail if vault/secret references exist but credentials missing
        cred_error = self.load_credentials()
        if cred_error:
            # Check if any configurations use vault template functions
            config_str = json.dumps([self.platform, self.location, self.spec])
            if 'vault `' in config_str or '|>' in config_str or '6>' in config_str or '5>' in config_str:
                source = self.settings.get('credential_source', 'vault')
                print(f"\nerror: Your configuration uses secret references but credential_source '{source}' is not configured.")
                if source == "vault":
                    print("Run: mkosimage --set vault_addr=http://your-vault:8200 --set vault_token=your-token")
                else:
                    print(f"Create: {os.path.join(self.settings['user_dir'], 'secrets')}")
                sys.exit(1)

        # Set platform_type from the platform config type field (after substitutions)
        platform_type = self.config.get('type', platform_name)
        self.defs['platform_type'] = platform_type
        if self.debug: print(f"platform_type set to: {platform_type}")
        
        # do def substitutions
        self.defs = do_sub(self.defs,self) # lol

        # Auto-detect a locally-cached ISO: if the resolved iso_url already
        # exists on disk (iso_path or packer_cache_dir), build from the local
        # copy instead of forcing platforms to download it again.
        if not self.defs.get('local_only') and self.check_iso_local(self.defs.get('iso_url', '')):
            self.defs['local_only'] = True

        self.evars['RES_OPTIONS'] = "nameserver >>dns1<<"
        self.evars = do_sub(self.evars,self)
        self.variables = do_sub(self.variables,self)

        provisioners = []
        if self.skip:
            if self.verbose: print("Skipping post-install configuration (--skip)")
        else:
            if self.debug: print(f"pre_provisioners: {self.pre_provisioners}")
            provisioners.extend(do_sub(self.pre_provisioners,self))
            if self.debug: print(f"provisioners: {self.provisioners}")
            provisioners.extend(do_sub(self.provisioners,self))
            if self.debug: print(f"post_provisioners: {self.post_provisioners}")
            provisioners.extend(do_sub(self.post_provisioners,self))

        self.spec['files'] = do_sub(self.spec.get("files",[]),self)
        self.config = do_sub(self.config,self)

        # go through each key in the builder and remove empty values
        if 1:
            for key in list(self.config):
                    if isinstance(self.config[key],str):
                            if self.debug: print("key: "+key+", value: "+self.config[key])
                            if len(self.config[key]) < 1:
                                    print("warning: removing empty value for: "+str(key))
                                    del self.config[key]

        # Give each bridged qemu build a unique NIC MAC so packer's SSH-address
        # DISCOVERY is unambiguous. This is NOT about parallel DHCP collisions
        # (dispatcher proved shared-MAC parallel builds are fine — well-behaved
        # distros send unique DHCP client-ids). It's that with the shared default
        # 52:54:00:12:34:56, packer's bridge discovery matches a STALE ARP entry
        # from an old build and connects to a dead IP (seen: real VM on .158,
        # packer hung on stale .159). A unique MAC = one clean bridge address.
        # Proxmox specifically needs it: it's static during the build, so its
        # ssh_host uses packer discovery rather than a resolvable FQDN.
        if (self.config.get('type') == 'qemu'
                and self.config.get('net_bridge')
                and 'qemuargs' not in self.config):
            h = uuid.uuid4().hex
            nic_mac = "52:54:00:%s:%s:%s" % (h[0:2], h[2:4], h[4:6])
            net_device = self.config.get('net_device', 'virtio-net')
            self.config['qemuargs'] = [
                ["-netdev", "bridge,id=user.0,br=%s" % self.config['net_bridge']],
                ["-device", "%s,netdev=user.0,mac=%s" % (net_device, nic_mac)],
            ]

        self.build = {
            "variables": self.variables,
            "provisioners": provisioners,
            "builders": [ self.config ]
        }

        # When using config-based secrets, resolve Packer {{vault ...}} references
        if self.secrets:
            self.build = self.resolve_packer_vault_refs(self.build)

        if self.dump_defs:
            print(json.dumps(self.defs,indent=4))
            sys.exit(0)

        if self.dump_build:
            print(json.dumps(self.build,indent=4))
            sys.exit(0)

        return self.build

    def check_required_files(self):
        """Check if all required_files from the spec are present."""
        required = self.spec.get("required_files", [])
        if not required:
            return True

        missing = False
        for entry in required:
            entry = do_sub(entry, self) if isinstance(entry, dict) else entry
            filepath = entry.get("file", "")
            filepath = do_substr(filepath, self)
            full_path = self.resolve_data_path("files", filepath)
            if not full_path:
                missing = True
                desc = entry.get("description", filepath)
                print(f"\nerror: required file not found: {filepath}")
                print(f"  Description: {desc}")
                url = entry.get("url", "")
                if url:
                    print(f"  Download from: {url}")
                location = entry.get("location", "")
                if location:
                    print(f"  Place it in: {os.path.join(self.settings['user_dir'], 'files', location)}")
                print()

        if missing:
            print("Build cannot proceed without the required files listed above.")
            sys.exit(1)

        return True

    def check_all_urls(self):
        """Check all ISO download URLs across all specs."""
        import urllib.request
        import urllib.error
        from concurrent.futures import ThreadPoolExecutor, as_completed

        index = self.get_index()
        if not index:
            print("No specs found. Have you installed osimager-data?")
            print(f"  pip install osimager-data")
            print(f"  Or create your own: {self.settings['user_dir']}/specs/")
            return

        # Resolve iso_url for each spec using a dummy location
        user_dir = self.settings['user_dir']
        loc_dir = os.path.join(user_dir, 'locations')
        dummy_loc = os.path.join(loc_dir, '_urlcheck.json')
        os.makedirs(loc_dir, exist_ok=True)

        # Create a minimal dummy location
        import json as _json
        with open(dummy_loc, 'w') as f:
            _json.dump({
                "platforms": ["virtualbox"],
                "defs": {
                    "domain": "check.local", "cidr": "10.0.0.0/24",
                    "gateway": "10.0.0.1", "vms_path": "/tmp/vms",
                    "iso_path": "/tmp/iso",
                    "dns": {"servers": ["10.0.0.1"]},
                    "ntp": {"servers": ["pool.ntp.org"]}
                }
            }, f)

        try:
            # Resolve URLs
            urls = {}  # url -> [spec_names]
            skipped = []
            for spec_key in sorted(index.keys()):
                target = f"virtualbox/_urlcheck/{spec_key}"
                try:
                    old_stdout = sys.stdout
                    sys.stdout = open(os.devnull, 'w')
                    o = OSImager(argv=['-x', target], which='full')
                    o.make_build(target, name='urlcheck', ip='10.0.0.99')
                    sys.stdout.close()
                    sys.stdout = old_stdout

                    url = o.defs.get('iso_url', '')
                    if not url or url.startswith('file://'):
                        skipped.append(spec_key)
                        continue
                    if url not in urls:
                        urls[url] = []
                    urls[url].append(spec_key)
                except SystemExit:
                    if sys.stdout != old_stdout:
                        sys.stdout.close()
                        sys.stdout = old_stdout
                    # -x flag exits normally
                    url = o.defs.get('iso_url', '')
                    if not url or url.startswith('file://'):
                        skipped.append(spec_key)
                        continue
                    if url not in urls:
                        urls[url] = []
                    urls[url].append(spec_key)
                except Exception:
                    if sys.stdout != old_stdout:
                        sys.stdout.close()
                        sys.stdout = old_stdout
                    skipped.append(spec_key)

            total_specs = len(index)
            print(f"Checking {len(urls)} unique URLs across {total_specs - len(skipped)} specs ({len(skipped)} local-only)...")
            print()

            def _check_url(url):
                try:
                    req = urllib.request.Request(url, method='HEAD')
                    req.add_header('User-Agent', 'OSImager/' + OSIMAGER_VERSION)
                    resp = urllib.request.urlopen(req, timeout=15)
                    return (url, resp.status)
                except urllib.error.HTTPError as e:
                    return (url, e.code)
                except Exception as e:
                    return (url, str(e)[:60])

            ok = 0
            failed = []
            with ThreadPoolExecutor(max_workers=10) as pool:
                futures = {pool.submit(_check_url, url): (url, specs) for url, specs in urls.items()}
                for f in as_completed(futures):
                    url, specs = futures[f]
                    checked_url, status = f.result()
                    if isinstance(status, int) and status in (200, 301, 302):
                        ok += 1
                    else:
                        failed.append((specs, url, status))

            if failed:
                for specs, url, status in sorted(failed, key=lambda x: x[0][0]):
                    print(f"  FAIL ({status}): {specs[0]}")
                    if len(specs) > 1:
                        print(f"    also: {', '.join(specs[1:])}")
                    print(f"    {url}")
                print()

            print(f"Results: {ok} OK, {len(failed)} FAILED, {len(skipped)} local-only")

        finally:
            if os.path.exists(dummy_loc):
                os.remove(dummy_loc)

    def check_iso_url(self):
        """Check that the ISO URL is accessible before starting the build."""
        iso_url = self.defs.get("iso_url", "")
        if not iso_url:
            return

        if iso_url.startswith("file://"):
            path = iso_url[7:]  # strip file://
            if not os.path.exists(path):
                print(f"\nerror: ISO file not found: {path}")
                print(f"  Spec: {self.defs.get('spec_name', 'unknown')}")
                print(f"  The ISO for this version is not available for download.")
                print(f"  You must obtain the ISO and place it at: {path}")
                print()
                sys.exit(1)
        elif iso_url.startswith("http://") or iso_url.startswith("https://"):
            if self.check_iso_local(iso_url):
                return
            import urllib.request
            import urllib.error
            try:
                req = urllib.request.Request(iso_url, method='HEAD')
                req.add_header('User-Agent', 'OSImager/' + self.VERSION)
                urllib.request.urlopen(req, timeout=15)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print(f"\nerror: ISO URL returned 404 (not found): {iso_url}")
                    print(f"  Spec: {self.defs.get('spec_name', 'unknown')}")
                    print(f"  The ISO may have been moved or removed from this location.")
                    print()
                    sys.exit(1)
            except Exception:
                pass  # network errors shouldn't block the build — packer will retry

    def gen_files(self):
        files = do_sub(self.files,self)
        if self.debug: print("files: "+json.dumps(files,indent=4))
        s = self.settings
        for file in files:
            if not isinstance(file, dict): continue
            sources = file.get("sources",[])
            data = ""
            for source_file_spec in sources:
                if self.debug: print("gen_files: source_file_spec: "+source_file_spec)
                source_file = do_substr(source_file_spec,self)
                if self.debug: print("gen_files: source_file: "+source_file)
                source_path = self.resolve_data_path("files", source_file)
                if self.debug: print("gen_files: source_path: "+str(source_path))
                if not source_path:
                    print("error: unable to find source file: "+source_file)
                    sys.exit(1)
                if self.debug: print("gen_files: appending source...")
                with open(source_path, 'r') as f:
                    data += f.read()
                    f.close()
            data = do_substr(data,self)
            if not data: return
            dest_file_spec = file.get("dest",None)
            if dest_file_spec:
                dest_file = do_substr(dest_file_spec,self)
                if self.debug: print("gen_files: dest_file: "+dest_file)
                dest_path = os.path.join(self.defs.get('temp_dir',"/tmp"),dest_file)
                if self.debug: print("gen_files: dest_path: "+dest_path)
                with open(dest_path, 'w') as f:
                    f.write(data)
                    f.close()

    def run_build_script(self, script_path):
        """Load and execute a Python build script from the data directory."""
        path = self.resolve_data_path(script_path)
        if not path:
            print(f"warning: build script not found: {script_path}")
            return
        if self.verbose:
            print(f"Running build script: {path}")
        try:
            spec = importlib.util.spec_from_file_location("build_script", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'run'):
                module.run(self)
            else:
                print(f"warning: build script {path} has no run() function")
        except Exception as e:
            print(f"error: build script {path} failed: {e}")

    def run_build_hooks(self, hook_name):
        """Run pre_build/post_build hooks declared by the spec and the platform.
        Spec hooks run first, then the platform's. A pre_build hook can mutate
        the ISO before Packer consumes it (e.g. coreos-installer iso customize to
        bake an Ignition config in) and may adjust self.config/self.defs, since
        pre_build runs before the build JSON is written."""
        scripts = []
        spec_hook = self.spec.get(hook_name)
        if spec_hook:
            scripts.append(spec_hook)
        plat_hook = self.platform.get(hook_name)
        if plat_hook:
            scripts.append(plat_hook)
        for script in scripts:
            self.run_build_script(script)

    def run_packer(self):

        # Check prerequisites
        packer_cmd = self.settings['packer_cmd']
        if not shutil.which(packer_cmd):
            print(f"error: '{packer_cmd}' not found in PATH")
            print("")
            print("  Packer is required. Install instructions:")
            print("    https://developer.hashicorp.com/packer/install")
            print("")
            print("  After installing Packer, install the required plugins:")
            print("    mkosimage --init-plugins")
            sys.exit(1)

        if not shutil.which('mkisofs'):
            print("error: 'mkisofs' not found in PATH")
            print("")
            print("  mkisofs is required by Packer to create CD/ISO images.")
            sys.exit(1)

        # Change to system data directory (osimager-data package) for Packer/Ansible
        # config.yml and tasks/ are referenced with relative paths from this directory
        data_path = self.system_data_dir or self.get_path("data_dir")
        if os.path.exists(data_path) and os.getcwd() != data_path:
            if self.verbose:
                print(f"Changing directory from {os.getcwd()} to {data_path}")
            os.chdir(data_path)

        # Check for required files before proceeding
        self.check_required_files()
        if self.dispatcher: print("PROGRESS=5", flush=True)

        # Check ISO URL accessibility
        self.check_iso_url()

        # generate files
        self.gen_files()
        if self.dispatcher: print("PROGRESS=10", flush=True)

        # Run pre_build hooks (spec then platform) before writing the build JSON
        # so a hook may transform the ISO/disk image and adjust self.config.
        self.run_build_hooks("pre_build")

        # Create output file
        output_file = os.path.join(self.defs.get("tmpdir","/tmp"), self.defs.get("name","build") + ".json")
        if self.verbose: print(f"writing output file: {output_file}")
        with open(output_file, 'w') as fp:
                json.dump(self.build, fp, indent=4)

        # define envionment vars
        for evar in self.evars:
            val = self.evars[evar]
            if self.verbose: print(f"setting environment variable: {evar} = {val}")
            os.environ[evar] = val

        # If vault addr/token set, define as env vars too
        token = self.defs.get('vault_token',None)
        if token:
                os.environ['VAULT_TOKEN'] = token
                os.environ['VAULT_ADDR'] = self.defs.get('vault_addr',None)
        if self.log:
                os.environ['PACKER_LOG'] = "1"
        if self.logfile:
                os.environ['PACKER_LOG_PATH'] = self.logfile

        # packer command starts here
        cmd = []

        # If ansible_version is specified, activate its venv during execution
        ansible_version = self.spec.get("ansible_version",None)
        if ansible_version and not self.skip:
                activator = self.get_path("venv_dir",ansible_version,"bin/activate")
                if self.verbose: print("activator: "+activator)
                if not os.path.isfile(activator):
                        print(f"error: post-install requires Ansible {ansible_version}")
                        print(f"  Create the venv with: mkvenv {ansible_version}")
                        print(f"  Or skip post-install with: --skip")
                        sys.exit(1)
                if self.verbose: print("Activating venv: "+ansible_version)
                cmd.append(".")
                cmd.append(activator)
                cmd.append("&&")

        cmd.append(self.settings['packer_cmd'])
        cmd.append("build")
        if self.timestamp:
            cmd.append("-timestamp-ui")
        if self.on_error:
            cmd.append("-on-error="+self.on_error)
        elif self.keep:
            cmd.append("-on-error=abort")
        if self.force:
            cmd.append("-force")
        if self.debug:
            cmd.append("-debug")
        cmd.append(output_file)

        cmd_str = ' '.join(cmd)
        print(cmd_str)
        if self.dispatcher: print("PROGRESS=15", flush=True)

        # Stay in data directory when running packer since config.yml is located there
        if not self.dry_run:
            # Ensure we're in the data directory where config.yml exists
            if os.getcwd() != data_path:
                os.chdir(data_path)
            rc = os.system(cmd_str)
            # os.system returns the wait status; extract the actual exit code
            self.exit_code = os.waitstatus_to_exitcode(rc) if hasattr(os, 'waitstatus_to_exitcode') else (rc >> 8)

            if self.dispatcher:
                spec_name = self.defs.get('spec_name', '')
                name = self.defs.get('name', '')
                if self.exit_code == 0:
                    print("PROGRESS=100", flush=True)
                    print(f'RESULT={{"spec": "{spec_name}", "name": "{name}", "status": "success"}}', flush=True)
                else:
                    print(f'ERROR={{"message": "packer build failed with exit code {self.exit_code}", "spec": "{spec_name}", "name": "{name}"}}', flush=True)

            # Run post_build hooks (spec then platform)
            if self.exit_code == 0:
                self.run_build_hooks("post_build")

        if not self.user_temp_dir and not self.keep:
            shutil.rmtree(self.temp_dir)
