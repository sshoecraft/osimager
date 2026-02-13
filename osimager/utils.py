
import sys
import os
import re
import socket
import ipaddress
import dns.resolver
import json
import inspect
import hashlib
import random
import string
import copy
import requests
import subprocess
from pathlib import Path
import urllib.parse
from urllib.parse import urlparse
from typing import List
from itertools import product
from collections import defaultdict

def run_cmd(cmd):
#   print("run_cmd: cmd: "+cmd)
    sub = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
#   print(dir(sub));
    out, err = sub.communicate()
#   print("run_cmd: out: "+out+", err: "+err)
    if sub.returncode != 0 or len(out) < 1: return ""
    return out.split(' ')[-1].replace('\n', '')

def natural_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def checkit(what, msg):
    if not what:
        print(msg)
        sys.exit(1)

def to_bool(s):
    if isinstance(s, bool):
        return s
    if isinstance(s, str):
        s = s.strip().lower()
        return s in ('true', '1', 'yes', 'on')
    return False

def deduplicate_and_sort_versions(new_versions):
    # Step 1: Accumulate unique ISOs by (version, arch)
    version_arch_map = defaultdict(dict)  # version -> arch -> iso

    for entry in new_versions:
        version = entry["version"]
        for iso in entry.get("isos", []):
            arch = iso.get("arch")
            # Only add if not already seen
            if arch not in version_arch_map[version]:
                version_arch_map[version][arch] = iso

    # Step 2: Convert to list of entries
    version_list = []
    for version, arch_map in version_arch_map.items():
        version_list.append({
            "version": version,
            "isos": list(arch_map.values())
        })

    # Step 3: Sort versions numerically, padding as needed
    def version_key(entry):
        parts = [int(p) for p in entry["version"].split(".")]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    return sorted(version_list, key=version_key)

def explode_string_with_dynamic_range(input_string: str, debug: bool = False) -> List[str]:
    if debug: print(f"input_string: {input_string}")

    pattern = re.compile(r'\[([^\[\]]+)\]')
    matches = list(pattern.finditer(input_string))

    if not matches:
        return [input_string]

    parts = []
    for match in matches:
        text = match.group(1)
        if '-' in text and ',' not in text:  # range pattern like 01-03
            start_str, end_str = text.split('-')
            start, end = int(start_str), int(end_str)

            # Only apply zero-padding if either side starts with '0' and has length > 1
            if (start_str.startswith('0') and len(start_str) > 1) or \
               (end_str.startswith('0') and len(end_str) > 1):
                width = max(len(start_str), len(end_str))
                values = [str(i).zfill(width) for i in range(start, end + 1)]
            else:
                values = [str(i) for i in range(start, end + 1)]
        else:  # list pattern like 1,3,7
            values = [x.strip() for x in text.split(',')]
        parts.append(values)
        if debug: print(f"Match: {text} . {values}")

    # Replace bracketed parts with tokens so we can reconstruct
    template = pattern.sub("{}", input_string)
    if debug: print(f"Template: {template}")

    combos = [template.format(*p) for p in product(*parts)]
    if debug: print(f"Result: {combos}")

    return combos

def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
#    print("filename: "+str(filename))
    text = urllib.parse.unquote(filename).replace(' ','-')
#    print("text: "+str(text))
    return text
#    sys.exit(0)


def check_url(url,debug = False):
    if debug: print(f"check_url: url: {url}")
    result = False
    try:
        response = requests.head(url, timeout=5)
        if debug: print("check_url: status_code: "+str(response.status_code))
        if response.status_code < 400:
            result = True
    except requests.RequestException as e:
        pass
    if debug: print("check_url: returning: "+str(result))
    return result

def get_checksum(sum_url, iso_url, debug = False):
    if debug: print(f"get_checksum: sum_url: {sum_url}")
    response = requests.get(sum_url)
    if debug: print("get_checksum: status_code: "+str(response.status_code))
    if response.status_code == 200:
        content = response.text
        if debug: print("get_checksum: content: "+str(content))
        iso_name = get_filename_from_url(iso_url)
        for line in content.splitlines():
            if iso_name in line:
                if debug: print(f"get_checksum: Found: {line}")
                return line.split()[0]
    else:
        if debug: print("get_checksum: Not found!")
        return None
   

def show_caller():
    caller_frame = inspect.stack()[2]
    caller_filename = caller_frame.filename
    caller_lineno = caller_frame.lineno
    caller_function = caller_frame.function
    print(f"Called from {caller_function}() at {caller_filename}:{caller_lineno}")

def isvarname(word):
    return (
        bool(word)
        and all(c.isalnum() or c in "_/,:" for c in word)
        and ' ' not in word
    )

def find_files(root_dir, pattern):
    return list(Path(root_dir).rglob(pattern))

def extract_all(text, start_pat, end_pat):
    matches = []
    lines = text.splitlines()
    for line in lines:
        pattern = re.escape(start_pat) + r'(.*?)' + re.escape(end_pat)
        found = re.findall(pattern, line)
        matches.extend(found)
    return matches

def deep_merge(d1, d2):
#    result = d1.copy()
    result = copy.deepcopy(d1)
    for key, value in d2.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                result[key] = result[key] + value
            else:
                result[key] = value
        else:
            result[key] = value
    return result

def merge_or_replace(d1, d2, method):
#    print("**** D1 *****")
#    print(f"{d1}")
#    print("**** D2 *****")
#    print(f"{d2}")
    if not d2:
        return d1
#    print(f"method: {method}")
    if (method == "merge"):
        return deep_merge(d1, d2)
    else:
        if isinstance(d1, dict):
            d1.update(d2)
        elif isinstance(d1, list):
            d1.extend(d2)
        else:
            for d2_key in d2:
                for d1_key in d1:
                    if d1_key == d2_key:
#                        print(f"replacing: {d1[d1_key]} with: {d2[d2_key]}")
                        d1[d1_key] = d2[d2_key]
        return d1

def prefix_to_netmask(prefix):
    prefix = int(prefix)
    mask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
    return (
        str((0xff000000 & mask) >> 24) + '.' +
        str((0x00ff0000 & mask) >> 16) + '.' +
        str((0x0000ff00 & mask) >> 8) + '.' +
        str((0x000000ff & mask))
    )

def get_ip(name, dns_cfg={}):
    debug = False
    search = dns_cfg.get("search", None)
    if debug: print("get_ip: search: "+str(search))
    servers = dns_cfg.get("servers", None)
    if debug: print("get_ip: servers: "+str(servers))

    resolver = dns.resolver.Resolver()
    if debug: print("get_ip: resolver: "+str(resolver))
    if search:
        resolver.search = [dns.name.from_text(domain) for domain in search]
    if servers:
        resolver.nameservers = servers

    try:
        answer = resolver.resolve(name, 'A')
        if debug: print("get_ip: answer: "+str(answer))
        addr = answer[0].address
    except:
        addr = None
    if debug: print("addr: "+str(addr))
    return addr

def _get_vault(vault, string, verbose=False):
    if not vault:
        print("error getting vault data: no vault defined")
        return ""
#        raise Exception("get_vault: error: inalid vault!")
#        show_caller()
#        sys.exit(1)

    i = string.find(":")
    if i < 0:
        full_path = string
        subkey = None
    else:
        full_path = string[:i]
        subkey = string[i+1:]
    if verbose: print("full_path: " + full_path)
    if verbose and subkey:
        print("subkey: " + subkey)

    parts = full_path.split("/", 1)
    if len(parts) != 2:
        print("get_vault: invalid mount/path: "+str(full_path))
        return ""
#        raise Exception("get_vault: error: invalid path, expected mount/path")
#        show_caller()
#        sys.exit(1)

    mount_point, secret_path = parts

    try:
        response = vault.secrets.kv.v2.read_secret_version(path=secret_path, mount_point=mount_point)
    except:
        print("get_vault: error getting vault secret {secret_path}")
        return ""

    data = response['data']['data']

    if subkey:
        val = data.get(subkey)
        return val
    else:
        return str(data)

def get_vault(vault, string, verbose=False):
    if verbose: print("get_vault: string: " + string)
    val = _get_vault(vault, string)
    if verbose: print("get_vault: returning: " + val)
    return val

def do_sub(item, inst):
    debug = False
    if debug:
        print(f"do_sub: item: {str(item)}, type: {str(type(item))}")
    
    if isinstance(item, dict):
        return {do_sub(key, inst): do_sub(value, inst) for key, value in item.items()}
    elif isinstance(item, list):
        result = []
        for elem in item:
            if isinstance(elem, str) and "[>" in elem and "<]" in elem:
                # Check if this is a pure list expansion (just the token)
                if elem.strip().startswith("[>") and elem.strip().endswith("<]"):
                    # Extract the token
                    token = elem.strip()[2:-2]  # Remove [> and <]
                    # Check if token exists in defs first
                    if token in inst.defs and isinstance(inst.defs[token], list):
                        # Expand the list items directly
                        result.extend(inst.defs[token])
                        continue
                    elif token not in inst.defs:
                        # Token doesn't exist - don't add anything to result
                        continue
            # Normal processing for non-list-expansion items
            result.append(do_sub(elem, inst))
        return result
    elif isinstance(item, tuple):
        return tuple(do_sub(elem, inst) for elem in item)
    elif isinstance(item, set):
        return {do_sub(elem, inst) for elem in item}
    elif isinstance(item, str):
        return do_substr(item, inst)
    else:
        return item

def _md5_crypt(password, salt, prefix='$1$'):
    """Pure Python MD5-crypt implementation compatible with glibc crypt()."""
    salt = salt[:8]
    pwd = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')

    # Start digest B
    b = hashlib.md5(pwd + salt_bytes + pwd).digest()

    # Start digest A
    a = hashlib.md5(pwd + prefix.encode('utf-8') + salt_bytes)

    # Add bytes from B to A
    plen = len(pwd)
    i = plen
    while i > 0:
        a.update(b[:min(16, i)])
        i -= 16

    # Handle password length bits
    i = plen
    while i:
        if i & 1:
            a.update(b'\x00')
        else:
            a.update(pwd[:1])
        i >>= 1

    result = a.digest()

    # 1000 rounds of MD5 stretching
    for i in range(1000):
        c = hashlib.md5()
        if i & 1:
            c.update(pwd)
        else:
            c.update(result)
        if i % 3:
            c.update(salt_bytes)
        if i % 7:
            c.update(pwd)
        if i & 1:
            c.update(result)
        else:
            c.update(pwd)
        result = c.digest()

    # Encode result using crypt base64
    CRYPT64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def _to64(v, n):
        out = ''
        for _ in range(n):
            out += CRYPT64[v & 0x3f]
            v >>= 6
        return out

    rearranged = (
        _to64((result[0] << 16) | (result[6] << 8) | result[12], 4) +
        _to64((result[1] << 16) | (result[7] << 8) | result[13], 4) +
        _to64((result[2] << 16) | (result[8] << 8) | result[14], 4) +
        _to64((result[3] << 16) | (result[9] << 8) | result[15], 4) +
        _to64((result[4] << 16) | (result[10] << 8) | result[5], 4) +
        _to64(result[11], 2)
    )

    return f"{prefix}{salt}${rearranged}"

def _sha_crypt(password, salt, prefix, algo, rounds):
    """Pure Python SHA-256/SHA-512 crypt implementation compatible with glibc crypt()."""
    salt = salt[:16]
    pwd = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    plen = len(pwd)

    hash_fn = hashlib.sha256 if algo == 'sha256' else hashlib.sha512
    hash_len = 32 if algo == 'sha256' else 64

    # Step 1-3: Digest B
    b = hash_fn(pwd + salt_bytes + pwd).digest()

    # Step 4-8: Digest A
    a = hash_fn()
    a.update(pwd)
    a.update(salt_bytes)

    # Step 9-10: Add bytes from B
    i = plen
    while i > hash_len:
        a.update(b)
        i -= hash_len
    a.update(b[:i])

    # Step 11: Process password length bits
    i = plen
    while i:
        if i & 1:
            a.update(b)
        else:
            a.update(pwd)
        i >>= 1

    # Step 12: Finish A
    a_result = a.digest()

    # Step 13-15: Digest DP (password hash)
    dp = hash_fn()
    for _ in range(plen):
        dp.update(pwd)
    dp_result = dp.digest()

    # Step 16: Produce P string
    p = b''
    i = plen
    while i > hash_len:
        p += dp_result
        i -= hash_len
    p += dp_result[:i]

    # Step 17-19: Digest DS (salt hash)
    ds = hash_fn()
    for _ in range(16 + a_result[0]):
        ds.update(salt_bytes)
    ds_result = ds.digest()

    # Step 20: Produce S string
    s = b''
    i = len(salt_bytes)
    while i > hash_len:
        s += ds_result
        i -= hash_len
    s += ds_result[:i]

    # Step 21: Rounds
    result = a_result
    for i in range(rounds):
        c = hash_fn()
        if i & 1:
            c.update(p)
        else:
            c.update(result)
        if i % 3:
            c.update(s)
        if i % 7:
            c.update(p)
        if i & 1:
            c.update(result)
        else:
            c.update(p)
        result = c.digest()

    # Encode using crypt base64
    CRYPT64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def _to64(v, n):
        out = ''
        for _ in range(n):
            out += CRYPT64[v & 0x3f]
            v >>= 6
        return out

    if algo == 'sha256':
        encoded = (
            _to64((result[0] << 16) | (result[10] << 8) | result[20], 4) +
            _to64((result[21] << 16) | (result[1] << 8) | result[11], 4) +
            _to64((result[12] << 16) | (result[22] << 8) | result[2], 4) +
            _to64((result[3] << 16) | (result[13] << 8) | result[23], 4) +
            _to64((result[24] << 16) | (result[4] << 8) | result[14], 4) +
            _to64((result[15] << 16) | (result[25] << 8) | result[5], 4) +
            _to64((result[6] << 16) | (result[16] << 8) | result[26], 4) +
            _to64((result[27] << 16) | (result[7] << 8) | result[17], 4) +
            _to64((result[18] << 16) | (result[28] << 8) | result[8], 4) +
            _to64((result[9] << 16) | (result[19] << 8) | result[29], 4) +
            _to64((result[30] << 8) | result[31], 3)
        )
    else:  # sha512
        encoded = (
            _to64((result[0] << 16) | (result[21] << 8) | result[42], 4) +
            _to64((result[22] << 16) | (result[43] << 8) | result[1], 4) +
            _to64((result[44] << 16) | (result[2] << 8) | result[23], 4) +
            _to64((result[24] << 16) | (result[3] << 8) | result[45], 4) +
            _to64((result[4] << 16) | (result[46] << 8) | result[25], 4) +
            _to64((result[47] << 16) | (result[5] << 8) | result[26], 4) +
            _to64((result[6] << 16) | (result[27] << 8) | result[48], 4) +
            _to64((result[28] << 16) | (result[49] << 8) | result[7], 4) +
            _to64((result[50] << 16) | (result[8] << 8) | result[29], 4) +
            _to64((result[30] << 16) | (result[9] << 8) | result[51], 4) +
            _to64((result[10] << 16) | (result[52] << 8) | result[31], 4) +
            _to64((result[53] << 16) | (result[11] << 8) | result[32], 4) +
            _to64((result[12] << 16) | (result[33] << 8) | result[54], 4) +
            _to64((result[34] << 16) | (result[55] << 8) | result[13], 4) +
            _to64((result[56] << 16) | (result[14] << 8) | result[35], 4) +
            _to64((result[36] << 16) | (result[15] << 8) | result[57], 4) +
            _to64((result[16] << 16) | (result[58] << 8) | result[37], 4) +
            _to64((result[59] << 16) | (result[17] << 8) | result[38], 4) +
            _to64((result[18] << 16) | (result[39] << 8) | result[60], 4) +
            _to64((result[40] << 16) | (result[61] << 8) | result[19], 4) +
            _to64((result[62] << 16) | (result[20] << 8) | result[41], 4) +
            _to64(result[63], 2)
        )

    # Default rounds (5000) are not included in the output
    if rounds == 5000:
        return f"{prefix}{salt}${encoded}"
    else:
        return f"{prefix}rounds={rounds}${salt}${encoded}"

def hash_password(password: str, method: str) -> str:
    """Generate password hash compatible with /etc/shadow format.

    Uses the crypt module on Python < 3.13, falls back to hashlib
    for Python 3.13+ where crypt was removed.
    """
    if method not in ['md5', 'sha256', 'sha512']:
        raise ValueError(f"Unsupported hash method: {method}")

    try:
        import crypt
        crypt_methods = {
            'md5': crypt.METHOD_MD5,
            'sha256': crypt.METHOD_SHA256,
            'sha512': crypt.METHOD_SHA512
        }
        crypt_method = crypt_methods[method]
        salt = crypt.mksalt(crypt_method)
        return crypt.crypt(password, salt)
    except (ImportError, ModuleNotFoundError):
        pass

    # Fallback for Python 3.13+ where crypt was removed
    salt_len = 16
    salt_chars = string.ascii_letters + string.digits + './'
    salt = ''.join(random.choice(salt_chars) for _ in range(salt_len))

    method_map = {
        'md5': ('$1$', 'md5', None),
        'sha256': ('$5$', 'sha256', 5000),
        'sha512': ('$6$', 'sha512', 5000),
    }
    prefix, algo, rounds = method_map[method]

    if algo == 'md5':
        # MD5-crypt ($1$) implementation
        return _md5_crypt(password, salt, prefix)
    else:
        # SHA-256/SHA-512 crypt ($5$/$6$) implementation
        return _sha_crypt(password, salt, prefix, algo, rounds)

def eval_expression_safe(token, imager):
    """Safely evaluate Python expressions with proper variable substitution."""
    # Pre-process the token to substitute any remaining >> << markers
    processed_token = token
    import re
    pattern = r'>>(.*?)<<'
    matches = re.findall(pattern, processed_token)
    for match in matches:
        value = imager.defs.get(match, f"<MISSING:{match}>")
        processed_token = processed_token.replace(f">>{match}<<", str(value))
    
    try:
        return eval(processed_token)
    except Exception as e:
        print(f"Error evaluating expression {repr(processed_token)}: {e}")
        raise

def eval_expression(expr: str, defs: dict) -> str:
#    print("expr: "+expr)
    delimiters = ["+", "-", "*", "/"]
    pattern = '(' + '|'.join(map(re.escape, delimiters)) + ')'

    parts = re.split(pattern, expr)
#    print("parts: "+str(parts))
    new_expr = ""
    # Iterate through parts as (value, delimiter) pairs
    for i in range(0, len(parts) - 1, 2):
        key = parts[i]
        delimiter = parts[i + 1]
#        print(f"key: '{key}', delimiter: '{delimiter}'")
        value = defs.get(key,None)
        if not value:
            print(f"error: invalid key {key} in expression {expr}")
            return ""
        new_expr += str(value)
        if delimiter:
            new_expr += delimiter

    # Handle last value if there's no trailing delimiter
    if len(parts) % 2 == 1:
        key = parts[-1]
#        print(f"key: {key}")
        value = defs.get(key,None)
        if not value:
            print(f"error: invalid key {key} in expression {expr}")
            return ""
        new_expr += str(value)

#    print(f"new_expr: {new_expr}")
    try:
       return int(eval(new_expr))
    except Exception as e:
        return f"<eval-error:{e}>"

def get_env(varname: str) -> str:
    return os.getenv(varname, '')

def insert_list_items(token: str, imager) -> list:
    """Insert list items from defs, returning the actual list items for expansion."""
    debug = getattr(imager, 'debug', False)
    if debug:
        print(f"insert_list_items: token: {token}")
    
    # Check if token exists in defs - if not, return empty list for no output
    if token not in imager.defs:
        if debug:
            print(f"insert_list_items: token '{token}' not found in defs, returning empty list")
        return []
    
    value = imager.defs[token]
    if debug:
        print(f"insert_list_items: value: {value}")
    
    if isinstance(value, list):
        result = value
    elif isinstance(value, str):
        # Split string into list if it contains spaces/commas
        result = [item.strip() for item in value.replace(',', ' ').split() if item.strip()]
    else:
        result = [str(value)]
    
    if debug:
        print(f"insert_list_items: returning: {result}")
    return result

def get_default(defs: dict, key: str, action: int, vault=None) -> str:
    val = defs.get(key, '')
    if action in (1, 2):
        return val
    if action == 3:
        return os.path.basename(val)
    if action == 4:
        return get_ip(val)
    if action == 5:
        return get_vault(vault, key) if vault else ''
    if action == 7:
        return get_env(key)
    return ''

ACTION_HANDLERS = {
    1: lambda token, imager: get_default(imager.defs, token, 1),
    2: lambda token, imager: get_default(imager.defs, token, 2),
    3: lambda token, imager: get_default(imager.defs, token, 3),
    4: lambda token, imager: get_default(imager.defs, token, 4),
    5: lambda token, imager: imager.get_secret(token),
    6: lambda token, imager: eval_expression(token, imager.defs),
    7: lambda token, imager: get_env(token),
    8: lambda token, imager: hash_password(imager.get_secret(token), 'md5'),
    9: lambda token, imager: hash_password(imager.get_secret(token), 'sha256'),
    10: lambda token, imager: hash_password(imager.get_secret(token), 'sha512'),
    11: lambda token, imager: eval_expression_safe(token, imager),
    12: lambda token, imager: insert_list_items(token, imager),
}

ACTIONS = [
    (1, ("%>", "<%")),  # Replace complete value (including quots) with defs variable
    (2, (">>", "<<")),  # Replace marker with defs variable
    (3, ("+>", "<+")),  # Replace marker with basename of defs variable
    (4, ("*>", "<*")),  # Replace marker with ip address (nslookup)
    (5, ("|>", "<|")),  # Replace marker with hashicorp vault value
    (6, ("#>", "<#")),  # Replace marker with numeric eval value (def value +-*/ def value)
    (7, ("$>", "<$")),  # Replace marker with env variable
    (8, ("1>", "<1")),  # Replace marker with md5 password hash
    (9, ("5>", "<5")),  # Replace marker with sha256 password hash
    (10, ("6>", "<6")), # Replace marker with sha512 password hash
    (11, ("E>", "<E")), # Python eval of expression within markers ('X' if value else 'Y')
    (12, ("[>", "<]")), # Insert list items separated by spaces
]

def secure_path_under_data_dir(user_path: str, data_dir: str, debug: bool = False) -> str:
    """
    Securely validate and resolve a path to ensure it stays within data_dir.
    
    Prevents directory traversal attacks by:
    - Resolving all symbolic links and relative paths
    - Ensuring the final path is within data_dir
    - Rejecting paths with '..' components
    - Normalizing path separators
    
    Args:
        user_path (str): The user-provided path to validate
        data_dir (str): The base data directory that paths must stay within
        debug (bool): Enable debug output
        
    Returns:
        str: The validated absolute path within data_dir
        
    Raises:
        ValueError: If the path is invalid or tries to escape data_dir
        FileNotFoundError: If data_dir doesn't exist
    """
    if debug:
        print(f"secure_path_under_data_dir: user_path='{user_path}', data_dir='{data_dir}'")
    
    # Validate inputs
    if not data_dir:
        raise ValueError("Data directory cannot be empty")
    
    # Handle empty path - should resolve to data_dir itself
    if not user_path:
        user_path = '.'
    
    # Ensure data_dir exists and get its absolute path
    data_dir_abs = os.path.abspath(data_dir)
    if not os.path.exists(data_dir_abs):
        raise FileNotFoundError(f"Data directory does not exist: {data_dir_abs}")
    
    if debug:
        print(f"secure_path_under_data_dir: data_dir_abs='{data_dir_abs}'")
    
    # Check for obvious directory traversal attempts
    if ".." in user_path:
        raise ValueError(f"Path contains directory traversal components '..': {user_path}")
    
    # Remove any leading slashes to treat as relative path
    user_path_clean = user_path.lstrip('/')
    
    if debug:
        print(f"secure_path_under_data_dir: user_path_clean='{user_path_clean}'")
    
    # Join with data_dir and resolve to absolute path
    candidate_path = os.path.join(data_dir_abs, user_path_clean)
    resolved_path = os.path.abspath(candidate_path)
    
    if debug:
        print(f"secure_path_under_data_dir: candidate_path='{candidate_path}'")
        print(f"secure_path_under_data_dir: resolved_path='{resolved_path}'")
    
    # Ensure the resolved path is within data_dir
    # Use os.path.commonpath to check if they share the same root
    try:
        common_path = os.path.commonpath([data_dir_abs, resolved_path])
        if debug:
            print(f"secure_path_under_data_dir: common_path='{common_path}'")
        
        # The common path should be exactly the data_dir
        if common_path != data_dir_abs:
            raise ValueError(f"Path attempts to escape data directory: {user_path} -> {resolved_path}")
    except ValueError as e:
        # This can happen if paths are on different drives (Windows)
        raise ValueError(f"Path attempts to escape data directory: {user_path} -> {resolved_path}")
    
    # Additional check: resolved path should start with data_dir
    if not resolved_path.startswith(data_dir_abs + os.sep) and resolved_path != data_dir_abs:
        raise ValueError(f"Path attempts to escape data directory: {user_path} -> {resolved_path}")
    
    if debug:
        print(f"secure_path_under_data_dir: validated path='{resolved_path}'")
    
    return resolved_path


def do_substr(text: str, imager) -> str:
    if ">" not in text and "+" not in text:
        return text

    debug = getattr(imager, 'debug', False)
#    debug = True
    if debug:
        print(f"Input text: {text}")

    result = text
    for action, (start, end) in ACTIONS:
        if debug: print(f"action: {str(action)}, start: {start}, end: {end}")
        tokens = extract_all(result, start, end)
        if debug: print("tokens: "+str(tokens))
        for tok in tokens:
            key = tok if action == 2 or action == 11 else tok.strip('"\'')
            if debug: print(f"tok: {tok}")
            if action != 6 and action != 11 and not isvarname(key):
                continue

            if debug:
                print(f"Action {action} on key '{key}'")

            handler = ACTION_HANDLERS.get(action)
            if debug: print("handler: "+str(handler))
            if not handler:
                continue

            repl = handler(key, imager)
            if debug: print("repl: "+str(repl))
            # Handle None values by converting to empty string for proper substitution
            if repl is None:
                repl = ""
            elif repl is False:
                continue

            full = f"{start}{tok}{end}"
            if debug: print(f"full: {full}")

            if result.strip() == full:
                if debug: print(f"returning: {repl}, type: {str(type(repl))}")
                return repl

            if debug:
                print(f"Replacing {full} with {repl}")
            result = result.replace(full, str(repl))
            if debug: print(f"result: {result}")

    if debug:
        print(f"returning: {result}, type: {str(type(result))}")
    return result

