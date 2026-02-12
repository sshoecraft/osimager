
import os
import sys
import json
import hvac
import configparser
import tempfile
import shutil
import argparse
from .utils import *

class OSImager:
    VERSION = "1.0"
    
    def __init__(self, argv=None, which="full", extra_args=None):
        self.init_vars()
        self.args = self.init_settings(argv,which,extra_args)
    
    def version(self):
        """Print version information."""
        print(f"OSImager version {self.VERSION}")
        return self.VERSION

    def init_vars(self):
        self.vault = None
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

        # Default settings
        self.settings = {
            "base_dir": os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../.."),
            "bin_dir": "bin",
            "conf_dir": "etc",
            "data_dir": "data",
            "lib_dir": "lib",
            "packer_cmd": "packer",
            "install_dir": "install",
            "vaultconfig": ".vaultconfig",
            "venv_dir": os.path.expanduser("~")+"/.venv",
            "ansible_playbook": "config.yml",
            "packer_cache_dir": "/tmp",
            "local_only": False,
            "save_index": False
        }
#        print("base_dir: "+self.settings['base_dir'])

        parser = argparse.ArgumentParser(description="OSImager configuration and control tool")

        arg_base_defs = {
            "--config": {"flags": ["-c", "--config"], "kwargs": {"default": "osimager.conf", "help": "Path to osimager.conf file", "dest": "config"}},
            "--list": {"flags": ["-l", "--list"], "kwargs": {"default": False, "action": "store_true", "help": "List available specs", "dest": "list"}},
            "--avail": {"flags": ["-a", "--avail"], "kwargs": {"default": False, "action": "store_true", "help": "Only list specs where an iso is present", "dest": "list"}},
            "--debug": {"flags": ["-d", "--debug"], "kwargs": {"default": False, "action": "store_true", "help": "Enable debug mode", "dest": "debug"}},
            "--verbose": {"flags": ["-v", "--verbose"], "kwargs": {"default": False, "action": "store_true", "help": "Enable verbose output", "dest": "verbose"}},
            "--version": {"flags": ["-V", "--version"], "kwargs": {"default": False, "action": "store_true", "help": "Show version and exit", "dest": "version"}},
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
                "--local-only": {"flags": ["--local-only"], "kwargs": {"default": False, "action": "store_true", "help": "Use local ISO files instead of downloading", "dest": "local_only"}},
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
        self.config_file = os.path.expanduser(args.config) if args.config else "osimager.conf"
        self.list = args.list
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
            self.dry_run = args.dry_run
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

        # Apply command line --local-only override
        if which == "full" and hasattr(args, 'local_only') and args.local_only:
            if self.settings['local_only'] != True:
                self.settings['local_only'] = True
                if self.verbose:
                    print("Overriding setting: local_only = True")
                do_save = True

        if self.debug: print("do_save: "+str(do_save))
        if do_save:
            self.save_settings(self.config_file)
        self.settings['local_only'] = to_bool(self.settings.get('local_only',False))

        self.base_path = self.get_path("base_dir")
        # define all the settings in defs
        self.defs.update(self.settings)
        # Also make base_dir available as base_path for compatibility
        self.defs['base_path'] = self.settings['base_dir']

        return args

    def load_settings(self, config_path):
        # Look for osimager.conf in project or user config
        config_file = None
        
        # Check if path is a specific file
        if config_path.endswith('.conf') or config_path.endswith('.ini'):
            config_file = os.path.expanduser(config_path)
        else:
            # Look for osimager.conf in the specified directory or project locations
            config_dir = os.path.expanduser(config_path)
            possible_configs = [
                os.path.join(config_dir, "osimager.conf"),
                os.path.join(self.settings['base_dir'], self.settings['conf_dir'], "osimager.conf"),
                os.path.join(self.settings['base_dir'], "osimager.conf"),  # fallback for backward compatibility
                os.path.expanduser("~/.config/osimager/osimager.conf")
            ]
            
            for conf in possible_configs:
                if os.path.exists(conf):
                    config_file = conf
                    break
        
        # If no config file found yet, check in conf_dir as fallback
        if not config_file or not os.path.exists(config_file):
            conf_dir_config = os.path.join(self.settings['base_dir'], self.settings['conf_dir'], "osimager.conf")
            if os.path.exists(conf_dir_config):
                config_file = conf_dir_config
            else:
                # Final fallback to root directory for backward compatibility
                fallback_config = os.path.join(self.settings['base_dir'], "osimager.conf")
                if os.path.exists(fallback_config):
                    config_file = fallback_config
        
        if config_file and os.path.exists(config_file):
            if self.verbose:
                print(f"Loading settings from: {config_file}")
            
            config = configparser.ConfigParser()
            config.read(config_file)
            
            # Load osimager section settings
            if 'osimager' in config:
                for key, value in config['osimager'].items():
                    if key in self.settings:
                        # Convert string values to appropriate types
                        if key == 'local_only':
                            self.settings[key] = config.getboolean('osimager', key, fallback=False)
                        elif key == 'base_dir':
                            self.settings[key] = os.path.abspath(value)
                        else:
                            self.settings[key] = value
                        if self.verbose:
                            print(f"   Loaded: {key} = {self.settings[key]}")
        else:
            if self.verbose:
                print(f"No config file found, using defaults.")

    def save_settings(self, config_path=""):
        # Determine config file location
        if config_path and (config_path.endswith('.conf') or config_path.endswith('.ini')):
            config_file = os.path.expanduser(config_path)
        else:
            # Save to conf_dir by default
            conf_dir = os.path.join(self.settings['base_dir'], self.settings['conf_dir'])
            os.makedirs(conf_dir, exist_ok=True)  # Create conf_dir if it doesn't exist
            config_file = os.path.join(conf_dir, "osimager.conf")
        
        # Read existing config
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file)
        
        # Ensure osimager section exists
        if 'osimager' not in config:
            config.add_section('osimager')
        
        # Save only osimager-specific settings (exclude base_dir and venv_dir - they are host-specific)
        osimager_keys = [
            'packer_cmd', 'packer_cache_dir', 'local_only',
            'bin_dir', 'conf_dir', 'data_dir', 'lib_dir', 'install_dir',
            'vaultconfig', 'save_index', 'ansible_playbook'
        ]
        
        for key in osimager_keys:
            if key in self.settings:
                config.set('osimager', key, str(self.settings[key]))
        
        try:
            with open(config_file, 'w') as f:
                config.write(f)
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
        if what in ["base_dir", "bin_dir", "conf_dir", "data_dir", "lib_dir"]:
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

    def load_specific(self, data, debug = False):
#        if debug: print("data: "+json.dumps(data,indent=4))
        specifics = [ "platform", "location", "dist", "version", "arch", "firmware" ]
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
        """Load a file directly using the provided file path."""
        debug = False
        if debug: print("file_path: "+str(file_path))
        if file_path is None:
            return None

        if self.verbose: 
            print("Loading file: " + file_path)

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            print(f"Error loading JSON file '{file_path}': {e}")
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
            file_path = os.path.join(self.get_path("data_dir"), where, what, 'spec.json')
        else:
            file_path = os.path.join(self.get_path("data_dir"), where, what)

        if not file_path.endswith(".json"):
            file_path += ".json"  # Add .json extension if not present
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

    # Load vault config
    def load_vault_config(self):
        config_path = self.get_path("vaultconfig")
        if self.verbose: print("load_vault_config: loading from: "+config_path)
        
        # Check if vault config file exists
        if not os.path.exists(config_path):
            print("error: Vault configuration not found!")
            print(f"Please create {config_path} with the following format:")
            print("addr=http://your-vault-server:8200")
            print("token=your-vault-token")
            print("")
            print("This is required when using vault template functions like {{vault `path` `key`}} in your configurations.")
            return True
        
        vault_addr = vault_token = None
        try:
            with open(config_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key == 'addr':
                            vault_addr = value.strip()
                        elif key == 'token':
                            vault_token = value.strip()
        except IOError as e:
            print(f"error: Unable to read vault config file {config_path}: {e}")
            return True
 
        if self.debug: print("load_vault_config: addr: "+str(vault_addr)+", token: "+str(vault_token))
        if vault_addr and vault_token:
            self.vault = hvac.Client(url=vault_addr,token=vault_token)
            if self.debug: print("isauth: "+str(self.vault.is_authenticated()))
            try:
            	if self.vault.is_authenticated():
                    self.defs['vault_addr'] = vault_addr
                    self.defs['vault_token'] = vault_token
                    return False
            except:
                if self.verbose: print("load_vault_config: Vault authentication failed (sealed?)")
                return True
#                show_caller()
#                sys.exit(1)
#            self.defs['vault_addr'] = vault_addr
#            self.defs['vault_token'] = vault_token
#            return False
        else:
            print("error: Vault configuration incomplete!")
            print(f"Please check {config_path} and ensure it contains:")
            if not vault_addr:
                print("  addr=http://your-vault-server:8200")
            if not vault_token:
                print("  token=your-vault-token")
            return True

    def get_platforms(self,names = None):
        debug = False
        files = find_files(os.path.join(self.get_path("data_dir"), "platforms"),'*.json')
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
        files = find_files(os.path.join(self.get_path("data_dir"), "locations"),'*.json')
        if debug: print("files: "+str(files))
        locations = []
        for file_name in files:
            if debug: print(f"file_name: {file_name}")
            try:
               with open(file_name, 'r') as f:
                    data = json.load(f)
                    f.close()
            except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
                print(f"Error loading JSON file '{file_name}': {e}")
                sys.exit(1)

            data['name'] = os.path.basename(file_name).removesuffix(".json")

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
        files = find_files(os.path.join(self.get_path("data_dir"), "specs"),'*.json')
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
        if isinstance(versions,list):
            version_list = []
            for vstr in versions:
                version_list.extend(explode_string_with_dynamic_range(vstr,debug))
        else:
            version_list = explode_string_with_dynamic_range(versions,debug)
        default_arches = provides.get("arches",None)
        version_specific = data.get("version_specific",[])
        provide_list = []
        for version in version_list:
            if debug: print("version: "+version)
            # check version_specific for arch overrides
            ver_arches = None
            for vs in version_specific:
                vs_ver = vs.get("version","")
                if re.fullmatch(vs_ver, version, re.IGNORECASE):
                    vs_arches = vs.get("arches",None)
                    if vs_arches:
                        ver_arches = vs_arches
            arches = ver_arches if ver_arches else default_arches
            for arch in arches:
                if debug: print("arch: "+arch)
                provide_entry = {
                    "dist": dist,
                    "version": version,
                    "arch": arch
                }
                provide_list.append(provide_entry)

        return provide_list
#        return deduplicate_and_sort_versions(provide_list)

    def resolve_iso_url(self, data, version, arch):
        """Best-effort resolve iso_url from spec data for a given version/arch."""
        parts = version.split('.')
        major = parts[0] if len(parts) > 0 else ""
        minor = parts[1] if len(parts) > 1 else ""
        subs = {
            ">>version<<": version,
            ">>major<<": major,
            ">>minor<<": minor,
            ">>arch<<": arch,
        }
        # check defs for iso_url
        iso_url = data.get("defs", {}).get("iso_url", "")
        # check version_specific overrides
        for vs in data.get("version_specific", []):
            vs_ver = vs.get("version", "")
            if re.fullmatch(vs_ver, version, re.IGNORECASE):
                vs_url = vs.get("defs", {}).get("iso_url", "")
                if vs_url:
                    iso_url = vs_url
        if not iso_url:
            return None
        # basic substitution
        for k, v in subs.items():
            iso_url = iso_url.replace(k, v)
        return iso_url

    def check_iso_local(self, iso_url):
        """Check if an ISO file exists locally (file:// or packer cache)."""
        if not iso_url:
            return False
        if iso_url.startswith("file://"):
            path = iso_url[7:]
            return os.path.isfile(path)
        # for remote URLs, check packer cache
        iso_name = get_filename_from_url(iso_url)
        if iso_name:
            cache_dir = self.settings.get('packer_cache_dir', '/tmp')
            return os.path.isfile(os.path.join(cache_dir, iso_name))
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
        files = find_files(os.path.join(self.get_path("data_dir"), "specs"),'*.json')
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
                arch = entry.get('arch',"")
                if entry.get("arch","") in arches:
                    key = entry['dist'] + "-" + entry['version'] + "-" + entry['arch']
                    iso_url = self.resolve_iso_url(data, entry['version'], entry['arch'])
                    iso_local = self.check_iso_local(iso_url) if iso_url else False
                    index[key] = {
                        "provides": entry,
                        "path": str(file_name),
                        "iso_local": iso_local
                    }

        sorted_index = {k: index[k] for k in sorted(index, key=natural_key)}
        if self.settings.get('save_index',False):
            file_name = os.path.join(self.get_path("data_dir"), "specs", "index.json")
            with open(file_name, 'w') as f:
                json.dump(sorted_index,f,indent=4)
                f.close()
        return sorted_index

    def get_index(self,name = None):
        debug = False
        if debug: print("get_index: name: "+name)
        file_name = os.path.join(self.get_path("data_dir"), "specs", "index.json")
        if debug: print("get_index: file_name: "+str(file_name))
        if os.path.isfile(file_name):
            try:
                with open(file_name, 'r') as f:
                    index = json.load(f)
                    f.close()
            except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
                print(f"Error loading JSON file '{file_name}': {e}")
                show_caller()
                sys.exit(1)
        else:
            index = self.make_index()
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
                iso_path = os.path.dirname(iso_url)+"/"
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

        self.defs['install_path'] = self.get_path("install_dir")

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

#        self.evars["ANSIBLE_ROLES_PATH"] = self.spec_path

        # Set PATH to prioritize venv if specified
        venv = self.spec.get("venv", None)
        if venv:
            venv_bin_path = self.get_path('venv_dir', venv, 'bin')
            current_path = os.environ.get('PATH', '')
            self.evars["PATH"] = f"{venv_bin_path}:{current_path}"

        if "platforms" in self.location and platform_name not in self.location["platforms"]:
            raise Exception(f"location {location_name} does not support platform {platform_name}")
        if "platforms" in self.spec and platform_name not in self.spec["platforms"]:
            raise Exception(f"spec {spec_name} does not support platform {platform_name}")
        if "locations" in self.spec and location_name not in self.spec["locations"]:
            raise Exception(f"spec {spec_name} does not support location {location_name}")
    
        self.config['name'] = spec_name

        # Break out the spec into components
        parts = spec_name.split("-")
        dist = parts[0] or self.spec.get("dist","")
        version = parts[1] or "0.0"
        arch = parts[2] or "unk"
        if self.debug: print(f"dist: {dist}, ver: {version}, arch: {arch}")

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
        
        self.defs.update({
            "base_path": self.settings['base_dir'],
            "data_path": self.base_path,
            "temp_dir": self.temp_dir,
            "tmpdir": self.temp_dir,
            "spec_dir": spec_dir,
            "dist": parts[0],
            "version": parts[1],
            "major": major,
            "minor": minor,
            "arch": parts[2]
        })
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

        # Load the vault config if available - fail if vault functions are used but config missing
        vault_error = self.load_vault_config()
        if vault_error:
            # Check if any configurations use vault template functions
            config_str = json.dumps([self.platform, self.location, self.spec])
            if 'vault `' in config_str:
                print("\nerror: Your configuration uses vault template functions but vault is not properly configured.")
                print("Please create .vaultconfig file with vault_addr and vault_token settings.")
                sys.exit(1)

        # Set platform_type from the platform config type field (after substitutions)
        platform_type = self.config.get('type', platform_name)
        self.defs['platform_type'] = platform_type
        if self.debug: print(f"platform_type set to: {platform_type}")
        
        # do def substitutions
        self.defs = do_sub(self.defs,self) # lol
        self.evars['RES_OPTIONS'] = "nameserver >>dns1<<"
        self.evars = do_sub(self.evars,self)
        self.variables = do_sub(self.variables,self)

        provisioners = []
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

        self.build = {
            "variables": self.variables,
            "provisioners": provisioners,
            "builders": [ self.config ]
        }
#        print(json.dumps(self.build,indent=4))

        if self.dump_defs:
            print(json.dumps(self.defs,indent=4))
            sys.exit(0)

        if self.dump_build:
            print(json.dumps(self.build,indent=4))
            sys.exit(0)

        return self.build

    def gen_files(self):
        files = do_sub(self.files,self)
        if self.debug: print("files: "+json.dumps(files,indent=4))
        s = self.settings
        for file in files:
            if not isinstance(file, dict): continue
            sources = file.get("sources",[])
            data = ""
            files_path = os.path.join(self.get_path("data_dir"), "files")
            if self.debug: print("files_path: "+str(files_path))
            for source_file_spec in sources:
                if self.debug: print("gen_files: source_file_spec: "+source_file_spec)
                source_file = do_substr(source_file_spec,self)
                if self.debug: print("gen_files: source_file: "+source_file)
                # ALWAYS relative to files dir
                source_path = os.path.join(files_path,source_file)
                if self.debug: print("gen_files: source_path: "+source_path)
                if not os.path.exists(source_path):
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

    def run_packer(self):

        # Change to data directory before gen_files so relative paths work correctly
        # This is needed for both mkosimage and rfosimage when running from /opt/osimager/bin
        data_path = self.get_path("data_dir")
        if os.path.exists(data_path) and os.getcwd() != data_path:
            if self.verbose:
                print(f"Changing directory from {os.getcwd()} to {data_path}")
            os.chdir(data_path)

        # generate files
        self.gen_files()

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

        # If a virtual env is specified, activate it during execution
        venv = self.spec.get("venv",None)
        if venv:
                activator = self.get_path("venv_dir",venv,"bin/activate")
                if self.verbose: print("activator: "+activator)
                if not os.path.isfile(activator):
                        print("error: venv doesnt exist: "+venv)
                        sys.exit(1)
                if self.verbose: print("Activating venv: "+venv)
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

        # Stay in data directory when running packer since config.yml is located there
        if not self.dry_run:
            # Ensure we're in the data directory where config.yml exists
            if os.getcwd() != data_path:
                os.chdir(data_path)
            os.system(cmd_str)

        if not self.user_temp_dir and not self.keep:
            shutil.rmtree(self.temp_dir)
