# Plan: Move User Configs Outside Package

## Context

When osimager is pip-installed, all data lives inside `site-packages/osimager/data/`. This means:
- Users must dig into site-packages to create location configs
- `.vaultconfig` lives inside the package directory
- Any `pip install --upgrade` wipes user-created files
- Writing index.json into site-packages is fragile

The fix: separate **package data** (read-only, shipped) from **user data** (site-specific, user-managed).

## Design

**Package data** stays at `osimager/data/` (read-only):
- `specs/` — distro specifications
- `files/` — kickstart/preseed/autoyast templates
- `tasks/` — ansible playbooks
- `platforms/` — platform definitions
- `ansible.cfg`, `config.yml`

**User data** moves to `~/.config/osimager/` (user-managed):
- `locations/` — site-specific environment configs
- `vaultconfig` — vault credentials
- `osimager.conf` — already there from earlier work

## Implementation

### 1. Add `user_dir` concept to core.py

In `init_settings()` (~line 42), add to self.settings:
```python
"user_dir": os.path.expanduser("~/.config/osimager"),
```

In `init_settings()` after settings are loaded (~line 185), create the user locations dir if it doesn't exist:
```python
os.makedirs(os.path.join(self.settings['user_dir'], 'locations'), exist_ok=True)
```

### 2. Change `get_locations()` to use user_dir

File: `osimager/core.py` (~line 572)

Change from:
```python
files = find_files(os.path.join(self.get_path("data_dir"), "locations"), '*.json')
```
To:
```python
files = find_files(os.path.join(self.settings['user_dir'], "locations"), '*.json')
```

### 3. Change `load_data_file()` for locations

File: `osimager/core.py` (~line 429)

When `where == "locations"`, construct path from `user_dir` instead of `data_dir`:
```python
if where == "locations":
    file_path = os.path.join(self.settings['user_dir'], "locations", what)
```

### 4. Change `load_vault_config()` to use user_dir

File: `osimager/core.py` (~line 484)

Change vault config lookup to check `~/.config/osimager/vaultconfig` instead of `{base_dir}/.vaultconfig`. Update the error message to tell users where to create it.

### 5. Fix index.json writes

File: `osimager/core.py` (~line 764)

If `save_index` is True, write to `{user_dir}/specs/index.json` instead of inside the package. On read, check user_dir first, fall back to regenerating.

### 6. Move example.json out of locations/

Move `osimager/data/locations/example.json` to `doc/example-location.json` as a reference. The package ships with NO locations — they are always user-created.

### 7. Update `load_settings()` / `save_settings()`

Already uses `~/.config/osimager/osimager.conf` — no change needed. Just ensure `user_dir` is also saveable via `--set`.

### 8. Add `user_dir` to defs

In `make_build()` (~line 1028), add `user_dir` to self.defs so it's available for template substitution if needed.

## Files to modify

- `osimager/core.py` — main changes (get_locations, load_data_file, load_vault_config, make_index/get_index, init_settings)
- `osimager/data/locations/example.json` — move to `doc/example-location.json`
- `pyproject.toml` — remove `data/**/*.example` pattern (no more example in package locations)

## Verification

1. `python3 bin/mkosimage --list` — should still find all 330 specs
2. `ls ~/.config/osimager/locations/` — directory should be auto-created
3. Copy a location file to `~/.config/osimager/locations/lab.json` and run a dry build
4. Rebuild wheel, install on test machine, verify locations load from `~/.config/osimager/`
5. Verify vault config error message points to `~/.config/osimager/vaultconfig`

## Status: IMPLEMENTED (v1.1.0)

All steps above have been implemented:
- `user_dir` added to settings, defaults to `~/.config/osimager/`
- `~/.config/osimager/locations/` auto-created on startup
- `get_locations()` reads from `user_dir/locations/`
- `load_data_file()` routes location loads to `user_dir`
- `index.json` writes/reads from `user_dir/specs/`
- `example.json` moved to `doc/example-location.json`
- `osimager/data/locations/` removed from package
- `pyproject.toml` cleaned up (removed `*.example` pattern)
- Version bumped to 1.1.0
- Wheel builds cleanly, 330 specs verified

### Credential Source System (also v1.1.0)

Replaced separate vaultconfig file with `credential_source` setting:

**Settings added to osimager.conf:**
- `credential_source` — "vault" (default) or "config"
- `vault_addr` — Vault server URL (when credential_source=vault)
- `vault_token` — Vault auth token (when credential_source=vault)

**Config mode (`credential_source=config`):**
- Secrets file: `~/.config/osimager/secrets`
- Format: `path key1=value1 key2=value2 ...`
- Example: `images/linux username=root password=T3mp@dm1n!`
- Resolves both osimager markers (`|>...<|`, `6>...<6`) and Packer `{{vault ...}}` refs

**Vault mode (`credential_source=vault`):**
- Uses vault_addr/vault_token from osimager.conf (set via `--set`)
- No more separate vaultconfig file

**Setup commands:**
```bash
# For vault:
mkosimage --set credential_source=vault
mkosimage --set vault_addr=http://vault:8200
mkosimage --set vault_token=s.xxxx

# For config:
mkosimage --set credential_source=config
# Then create ~/.config/osimager/secrets
```

**Code changes:**
- `core.py`: `load_credentials()` replaces `load_vault_config()`, adds `load_secrets()`, `get_secret()`, `resolve_packer_vault_refs()`
- `utils.py`: ACTION_HANDLERS 5,8,9,10 now call `imager.get_secret()` instead of `get_vault(imager.vault, ...)`
