---
name: compiled-osimager-config-persistence-and-local-only
description: osimager: --set/--local persist to user config (test via XDG_CONFIG_HOME), local_only auto-detect from cached ISO, v1.7.0 two-layer data/XDG layout
metadata:
  type: project
tags: [compiled, osimager, config, local_only, xdg]
---

Topic: how osimager/mkosimage config is persisted and resolved, and how `local_only` gets set. Two raw notes plus a session-log section folded in.

## Config persistence trap
`trap-set-flag-persists-to-user-config`: `--set key=value` is not a runtime override. If the value differs, `do_save` writes `$XDG_CONFIG_HOME/osimager/config.json` (default `~/.config/osimager/`). `--local` sets `settings['local_only'] = True` BEFORE that save, so `--set ... --local` also persists `local_only: true`; every later run, including the user's own builds, behaves as `--local`.
- Failure seen: testing `--latest --local` with `--set iso_path=<scratch dir>` rewrote the user's config with a scratch `iso_path` and `local_only: true`. Next `--latest` (no `--local`) resolved the newest LOCAL version and looked like a code bug; it was the saved config. Fix was restoring `iso_path` and `local_only: false` from an earlier `--show-config`.
- Test safely by isolating the config dir:
```
mkdir -p $S/cfg/osimager; cp -r ~/.config/osimager/{locations,platforms} $S/cfg/osimager/
sed 's#"<old iso_path>"#"<new>"#' ~/.config/osimager/config.json > $S/cfg/osimager/config.json
XDG_CONFIG_HOME=$S/cfg python3 bin/mkosimage ...
```
Run `--show-config` first and compare against the real config afterwards. Delete the copy (locations/ can hold credentials).

## local_only auto-detection
`local-only-not-auto-detected-from-cached-iso`: `local_only` (flips Proxmox/other platform templates from downloading `iso_url` to referencing an existing `iso_file`) was set only by `--local`/`--local-only` or config.json, never inferred from `check_iso_local()`, though `--list`/`--avail` show the same info via `(*)`. A cached ISO (e.g. `/iso/AlmaLinux-9.7-x86_64-dvd.iso`) still needed `--local` on every build, or Packer re-downloaded from `iso_url`, which fails if the upstream URL went stale (related: memory `iso-url-check-ignores-local-cache-bug`, pre-flight HEAD check).
- Fix in `make_build()` (core.py), right after `self.defs = do_sub(self.defs,self)` (~line 1414), before provisioners/config substitution:
```python
if not self.defs.get('local_only') and self.check_iso_local(self.defs.get('iso_url', '')):
    self.defs['local_only'] = True
```
Only turns it on, never overrides an explicit True->False; shares `check_iso_local()` with `--avail`/`--list` so they cannot disagree.
- Verified with `mkosimage -x` (dump defs) and `-u` (dump build json) on `proxmox/pve1/alma-9.7-x86_64`: `local_only` resolves true, Proxmox builder emits `iso_file: "iso:iso/AlmaLinux-9.7-x86_64-dvd.iso"` with no `--local`.
- Caveat: for Proxmox "local" means present in the PVE ISO storage pool (`iso_file: "<storage_pool>:iso/<name>"`), not cached on the mkosimage machine. `/iso` is the same NFS storage as PVE's `iso` pool here, so the local check is a valid proxy; if they diverge, detection must become platform-aware.
- Interaction with the trap above: auto-detection makes a persisted `local_only: true` even harder to notice.

## Data and path layout (v1.7.0)
the 2026-03-21 session log (deleted):
- Engine (`osimager`) and baseline data (`osimager-data`, optional separate package, detected via `import osimager_data`) are split; user overrides live in `~/.config/osimager/` (specs, platforms, files, scripts). Lookups go through `resolve_data_path(*parts)` / `resolve_data_files(subdir, pattern)` in core.py; all 14 `get_path("data_dir")` sites migrated; `data_dir` removed from `save_keys` so it is no longer persisted. Packer CWD is `system_data_dir`.
- `load_specific()` now hoists scalar fields (e.g. `venv`) from matched `*_specific` entries; before, `venv` in `version_specific` was silently dropped. RHEL 2-6 need `venv: "2.10"` (ansible-core 2.10; RHEL 6 has Python 2.6).
- `constants.py` removed; `OSIMAGER_VERSION`, `EXIT_SUCCESS`, `EXIT_ERROR` live in core.py; pyproject version ref updated, package-data section removed, package find is `osimager` only.
- XDG: `user_dir` `$XDG_CONFIG_HOME/osimager`; `venv_dir` `$XDG_DATA_HOME/osimager/venvs`; `packer_cache_dir` `$XDG_CACHE_HOME/osimager`. The XDG_CONFIG_HOME override is what makes the isolated-test technique work.
- Dev bridge: source-tree `osimager_data/__init__.py` points DATA_DIR at `osimager/data/` until the data repo is installed.
- Open at that time: create osimager-data repo and remove `osimager/data/` from engine; `mkvenv` CLI was a stub; `~steve` dir on built VMs; RHEL 6 needs the 2.10 venv.
