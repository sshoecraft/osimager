# Template Engine

OSImager includes a template substitution engine that processes all configuration data before the final Packer build JSON is generated. The engine replaces marker tokens with computed values, supporting variable interpolation, secret retrieval, expression evaluation, password hashing, and list expansion. All substitution logic resides in `utils.py`.

## Processing Flow

Template substitution is driven by two functions working together:

### do_sub(item, imager)

**Location:** `utils.py`, lines 301-334.

`do_sub()` is the top-level recursive walker. It traverses any Python data structure (dict, list, tuple, set, str) and applies `do_substr()` to every string it encounters.

- **dict**: Recurses into both keys and values. Returns a new dict.
- **list**: Recurses into each element. Has special handling for `[>token<]` list expansion markers (see Action 12 below).
- **tuple/set**: Recurses into each element. Returns new tuple/set.
- **str**: Delegates to `do_substr()`.
- **other types** (int, bool, None, etc.): Returned unchanged.

The list handling for Action 12 is done inline in `do_sub()` rather than in `do_substr()`. When a list element is a string of the form `[>token<]` (where the entire string is the marker), `do_sub()` checks if the token references a list in `imager.defs`. If so, it expands the list items directly into the parent list via `result.extend()`. If the token does not exist in defs, the element is silently dropped.

### do_substr(text, imager)

**Location:** `utils.py`, lines 796-846.

`do_substr()` processes a single string through all 12 actions in order. For each action:

1. Calls `extract_all()` to find all marker tokens in the string.
2. For each token found, validates it with `isvarname()` (except Actions 6 and 11 which allow expressions).
3. Calls the action's handler from `ACTION_HANDLERS`.
4. **Type preservation**: If the entire string (stripped) equals the full marker, the raw handler return value is returned directly -- preserving non-string types (int, bool, list, dict). This is critical for Action 1.
5. **Inline substitution**: Otherwise, `str(repl)` replaces the marker text within the string.

### extract_all(text, start_pat, end_pat)

**Location:** `utils.py`, lines 172-179.

Finds all tokens between the given delimiters. Operates line by line using `re.findall()` with escaped delimiter patterns. Returns a list of the inner token strings (without delimiters).

---

## The ACTIONS List

**Location:** `utils.py`, lines 698-711.

Actions are processed sequentially from 1 through 12. The order matters: earlier actions may produce values that later actions consume (e.g., Action 2 substitutions within Action 11 expressions).

```python
ACTIONS = [
    (1, ("%>", "<%")),   # Complete value replacement
    (2, (">>", "<<")),   # Inline string substitution
    (3, ("+>", "<+")),   # Basename substitution
    (4, ("*>", "<*")),   # DNS lookup
    (5, ("|>", "<|")),   # Secret retrieval
    (6, ("#>", "<#")),   # Numeric expression evaluation
    (7, ("$>", "<$")),   # Environment variable
    (8, ("1>", "<1")),   # MD5 password hash
    (9, ("5>", "<5")),   # SHA-256 password hash
    (10, ("6>", "<6")),  # SHA-512 password hash
    (11, ("E>", "<E")),  # Python eval expression
    (12, ("[>", "<]")),  # List item expansion
]
```

## ACTION_HANDLERS

**Location:** `utils.py`, lines 683-696.

Each handler is a lambda that takes `(token, imager)` and returns the replacement value.

---

## Action Reference

### Action 1: Complete Value Replacement

| | |
|---|---|
| **Delimiters** | `%>token<%` |
| **Handler** | `get_default(imager.defs, token, 1)` |
| **Returns** | Raw value from `imager.defs[token]` |

Retrieves the value of `token` from `imager.defs` and returns it with full type preservation. When the entire string is `%>token<%`, the return value can be any type: bool, int, list, dict, or string. This is the only action that intentionally preserves non-string types.

**Use case:** Passing structured data like lists or booleans directly into the Packer config without stringification.

**Example:**
```json
"cd_files": "%>cd_files<%"
```
If `defs["cd_files"]` is a string, it replaces the value. If it is a list, the JSON value becomes that list.

```json
"disk_thin_provisioned": "%>thin_disk<%"
```
If `defs["thin_disk"]` is `false` (Python bool), the JSON value becomes `false`, not the string `"false"`.

---

### Action 2: Inline String Substitution

| | |
|---|---|
| **Delimiters** | `>>token<<` |
| **Handler** | `get_default(imager.defs, token, 2)` |
| **Returns** | Value from `imager.defs[token]`, converted to string if used inline |

The workhorse substitution. Replaces the marker with the string representation of the defs value. If the entire string is only the marker, type preservation applies (same as Action 1). When the marker is embedded within a larger string, the value is converted to string via `str()`.

**Use case:** Building paths, URLs, filenames, and any templated string.

**Example:**
```json
"iso_url": "https://vault.almalinux.org/>>version<</isos/>>arch<</AlmaLinux->>version<<->>arch<<-dvd.iso"
```

---

### Action 3: Basename Substitution

| | |
|---|---|
| **Delimiters** | `+>token<+` |
| **Handler** | `get_default(imager.defs, token, 3)` |
| **Returns** | `os.path.basename()` of the defs value |

Retrieves the value from defs and returns only the filename component (stripping any directory path).

**Use case:** Extracting just the filename from a full path stored in defs.

**Example:**
```json
"iso_name": "+>iso_file<+"
```
If `defs["iso_file"]` is `/iso/RedHat/rhel-9.3-x86_64-dvd.iso`, the result is `rhel-9.3-x86_64-dvd.iso`.

---

### Action 4: DNS Lookup

| | |
|---|---|
| **Delimiters** | `*>token<*` |
| **Handler** | `get_default(imager.defs, token, 4)` |
| **Returns** | IPv4 address string from DNS A record lookup via `get_ip()` |

Retrieves the hostname from `imager.defs[token]`, then performs a DNS A record lookup using `get_ip()`. Returns the resolved IP address as a string.

**Use case:** Resolving hostnames to IP addresses at build time.

**Example:**
```json
"ip_address": "*>fqdn<*"
```

---

### Action 5: Secret Retrieval

| | |
|---|---|
| **Delimiters** | `\|>token<\|` |
| **Handler** | `imager.get_secret(token)` |
| **Returns** | Secret value string |

Retrieves a secret using `imager.get_secret()`, which dispatches to either HashiCorp Vault or the local secrets file based on the `credential_source` setting. The token format is `path:key` where `path` is the secret path and `key` is the specific field within the secret.

**Use case:** Injecting passwords, API keys, or other sensitive values into configurations.

**Example:**
```json
"root_password": "|>images/linux:password<|"
```

---

### Action 6: Numeric Expression Evaluation

| | |
|---|---|
| **Delimiters** | `#>expr<#` |
| **Handler** | `eval_expression(token, imager.defs)` |
| **Returns** | Integer result of arithmetic evaluation |

Evaluates arithmetic expressions where operands are defs variable names. The expression is split on `+`, `-`, `*`, `/` operators. Each operand is looked up in `imager.defs`, then the resulting numeric expression is evaluated with Python `eval()` and cast to `int()`.

**Use case:** Computing derived numeric values from defs at build time.

**Example:**
```json
"CPUs": "#>cpu_sockets*cpu_cores<#"
```
If `defs["cpu_sockets"]` is `1` and `defs["cpu_cores"]` is `2`, the result is `2`.

```json
"RAM": "#>memory<#"
```
Single-variable expressions also work -- the value is looked up and returned as int.

---

### Action 7: Environment Variable

| | |
|---|---|
| **Delimiters** | `$>token<$` |
| **Handler** | `get_env(token)` |
| **Returns** | Value of `os.environ[token]`, or empty string if not set |

Reads a system environment variable by name.

**Use case:** Incorporating host environment values into the build configuration.

**Example:**
```json
"http_proxy": "$>HTTP_PROXY<$"
```

---

### Action 8: MD5 Password Hash

| | |
|---|---|
| **Delimiters** | `1>token<1` |
| **Handler** | `hash_password(imager.get_secret(token), 'md5')` |
| **Returns** | MD5-crypt hash string (prefix `$1$`) |

Retrieves the secret identified by `token`, then generates an MD5-crypt hash compatible with `/etc/shadow` format. The hash uses the `$1$` prefix.

**Use case:** Generating hashed passwords for legacy OS kickstart files that require MD5-crypt format.

**Example:**
```json
"rootpw": "1>images/linux:password<1"
```

---

### Action 9: SHA-256 Password Hash

| | |
|---|---|
| **Delimiters** | `5>token<5` |
| **Handler** | `hash_password(imager.get_secret(token), 'sha256')` |
| **Returns** | SHA-256-crypt hash string (prefix `$5$`) |

Retrieves the secret and generates a SHA-256-crypt hash compatible with `/etc/shadow`.

**Use case:** Generating hashed passwords for kickstart files on modern RHEL-family systems.

**Example:**
```json
"rootpw": "5>images/linux:password<5"
```

---

### Action 10: SHA-512 Password Hash

| | |
|---|---|
| **Delimiters** | `6>token<6` |
| **Handler** | `hash_password(imager.get_secret(token), 'sha512')` |
| **Returns** | SHA-512-crypt hash string (prefix `$6$`) |

Retrieves the secret and generates a SHA-512-crypt hash compatible with `/etc/shadow`.

**Use case:** The most common hash format for modern Linux kickstart root passwords.

**Example:**
```json
"rootpw": "6>images/linux:password<6"
```

---

### Action 11: Python Eval Expression

| | |
|---|---|
| **Delimiters** | `E>expr<E` |
| **Handler** | `eval_expression_safe(token, imager)` |
| **Returns** | Result of Python `eval()` on the processed expression |

Two-phase evaluation:

1. **Phase 1**: All `>>var<<` markers (Action 2 syntax) within the expression are substituted with their defs values. This happens inside `eval_expression_safe()` using a regex replacement, not via the normal Action 2 pipeline.
2. **Phase 2**: The resulting string is passed to Python `eval()`.

This allows arbitrary Python expressions that reference defs variables.

**Use case:** Conditional logic, string manipulation, and computed values that go beyond simple arithmetic.

**Examples:**
```json
"iso_url": "E>'>>iso_path<</>>iso_name<<' if >>local_only<< else '>>iso_url<<'<E"
```
This produces a different ISO URL depending on whether `local_only` is true or false.

```json
"guest_os_type": "RedHat6E>'_64' if '>>arch<<' == 'x86_64' else ''<E"
```
Appends `_64` to the guest OS type only when the architecture is x86_64.

```json
"iso_paths": ["[] /vmimages/tools-isoimages/E>'windows' if '>>spec_name<<'.startswith('win') else 'linux'<E.iso"]
```
Selects between Windows and Linux VMware Tools ISO based on the spec name.

---

### Action 12: List Item Expansion

| | |
|---|---|
| **Delimiters** | `[>token<]` |
| **Handler** | `insert_list_items(token, imager)` (in handler table) / inline in `do_sub()` |
| **Returns** | List of items, or empty list |

Expands a single list element into multiple elements. When a list contains an element `"[>token<]"`, the token is looked up in `imager.defs`:

- If the value is a **list**, all items are inserted into the parent list.
- If the value is a **string**, it is split on commas and whitespace into multiple items.
- If the token **does not exist** in defs, the element is silently removed (no output).

The primary expansion logic is in `do_sub()` (lines 311-323), not in `do_substr()`. The `do_sub()` function detects pure list expansion markers in list elements before delegating to the normal substitution pipeline.

**Use case:** Dynamically injecting variable-length argument lists into provisioner configurations.

**Example:**
```json
"extra_arguments": [
    "[>ansible_extra_args<]",
    "--extra-vars",
    "platform={{user `platform-name`}}"
]
```
If `defs["ansible_extra_args"]` is `["--scp-extra-args='-O'", "-e", "ansible_scp_extra_args='-O'"]`, the resulting list is:
```json
["--scp-extra-args='-O'", "-e", "ansible_scp_extra_args='-O'", "--extra-vars", "platform={{user `platform-name`}}"]
```

---

## Key Behaviors

### Action Processing Order

Actions are always processed in order 1 through 12 on every string. A single string can contain markers from multiple actions. Earlier actions run first, so their results are visible to later actions.

The one exception is Action 11 (`E>...<E`), which performs its own internal `>>var<<` substitution (Action 2 syntax) before `eval()`. This two-phase design means Action 2 markers inside Action 11 expressions are resolved even though Action 2 has already been processed at the outer level.

### Type Preservation (Action 1)

When the **entire string** (after stripping) matches a single marker, `do_substr()` returns the handler's raw value directly (line 835-837):

```python
if result.strip() == full:
    return repl
```

This is what allows `%>thin_disk<%` to produce a JSON boolean `false` instead of the string `"False"`, or `%>cd_files<%` to produce a list instead of a string.

This behavior applies to all actions, not just Action 1. If a string consists of nothing but a single `>>token<<` marker and the defs value is an integer, the integer is returned.

### Secret-Dependent Actions

Actions 5, 8, 9, and 10 all use `imager.get_secret()` to retrieve sensitive values. The `get_secret()` method dispatches based on the `credential_source` setting:

- **`vault`**: Uses the HashiCorp Vault client (`hvac`) to read from Vault's KV v2 secrets engine.
- **`config`**: Reads from `~/.config/osimager/secrets`, a local file with format `path key=val key=val`.

The token format for all secret actions is `path:key` (e.g., `images/linux:password`).

### None and False Handling

- If a handler returns `None`, it is converted to an empty string `""` for substitution (line 828).
- If a handler returns `False`, the substitution is skipped entirely -- the marker remains in the string (line 830).

---

## Supporting Functions

### explode_string_with_dynamic_range()

**Location:** `utils.py`, lines 78-113.

Expands version range expressions in spec `provides.versions` strings. Supports two bracket syntaxes:

- **Range**: `[start-end]` -- generates all integers from start to end inclusive. Preserves zero-padding when the original values have leading zeros.
- **List**: `[a,b,c]` -- generates the explicit list of values.

Multiple bracket groups in a single string produce the Cartesian product of all groups.

**Examples:**
- `"8.[3-10]"` -> `["8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "8.10"]`
- `"5.[1,9,10,11]"` -> `["5.1", "5.9", "5.10", "5.11"]`
- `"12.[01-05]"` -> `["12.01", "12.02", "12.03", "12.04", "12.05"]` (zero-padded)

Note: Mixed range-and-list syntax within a single bracket group (e.g., `[0-3,5-7]`) is not supported. Use separate version strings instead.

### hash_password()

**Location:** `utils.py`, lines 543-582.

Generates crypt-compatible password hashes for `/etc/shadow` format. Supports three methods:

| Method | Prefix | Function |
|--------|--------|----------|
| `md5` | `$1$` | `_md5_crypt()` |
| `sha256` | `$5$` | `_sha_crypt()` with 5000 rounds |
| `sha512` | `$6$` | `_sha_crypt()` with 5000 rounds |

On Python < 3.13, the function uses the stdlib `crypt` module. On Python 3.13+, where `crypt` was removed, it falls back to pure-Python implementations (`_md5_crypt()` at line 336, `_sha_crypt()` at line 404) that produce identical output to glibc's `crypt()`.

### prefix_to_netmask()

**Location:** `utils.py`, lines 219-227.

Converts a CIDR prefix length to a dotted-decimal netmask string.

**Example:** `prefix_to_netmask("24")` -> `"255.255.255.0"`

### get_ip()

**Location:** `utils.py`, lines 229-250.

Performs a DNS A record lookup for a hostname. Uses `dns.resolver.Resolver` with optional custom search domains and nameservers (from the location's DNS configuration). Returns the IP address string, or `None` if resolution fails.

### natural_key()

**Location:** `utils.py`, lines 32-34.

Produces sort keys for version-aware natural ordering. Splits a string on digit boundaries and converts numeric segments to integers, enabling proper sorting where `"9.10"` sorts after `"9.9"` rather than between `"9.1"` and `"9.2"`.

Used by `make_index()` in `core.py` (line 864) to sort the spec index by version number.

### eval_expression()

**Location:** `utils.py`, lines 601-636.

Evaluates arithmetic expressions for Action 6. Splits the expression on `+`, `-`, `*`, `/` operators, looks up each operand in `imager.defs`, reconstructs a numeric expression string, and evaluates it with `eval()`. Returns the result as `int`.

### eval_expression_safe()

**Location:** `utils.py`, lines 584-599.

Evaluates arbitrary Python expressions for Action 11. First performs `>>var<<` substitution using a regex scan, then passes the result to `eval()`. Returns whatever `eval()` produces (string, int, bool, etc.).

### get_default()

**Location:** `utils.py`, lines 669-681.

Central dispatcher for Actions 1-4 and 7. Takes the defs dict, a key, and an action number. Returns the appropriate transformation:

| Action | Transformation |
|--------|---------------|
| 1, 2 | Raw defs value |
| 3 | `os.path.basename()` of defs value |
| 4 | `get_ip()` DNS lookup on defs value |
| 7 | `get_env()` environment variable lookup on key |

### isvarname()

**Location:** `utils.py`, lines 162-167.

Validates that a token looks like a variable name or path. Allows alphanumeric characters, underscores, forward slashes, commas, and colons. Rejects tokens containing spaces. Used by `do_substr()` to skip tokens that are not valid variable references (except for Actions 6 and 11 which accept expressions).

### insert_list_items()

**Location:** `utils.py`, lines 641-667.

Implements the handler side of Action 12. Looks up the token in `imager.defs`:
- If the value is already a list, returns it directly.
- If the value is a string, splits on commas and whitespace into a list.
- If the token does not exist, returns an empty list.
