---
name: trap-set-flag-persists-to-user-config
description: mkosimage --set key=val SAVES to ~/.config/osimager/config.json, and a --local in the same run saves local_only=true too. Test with XDG_CONFIG_HOME i…
metadata:
  type: project
tags: [config, set-flag, local_only, testing, iso_path]
---

`--set key=value` is not a runtime override. If the value differs, `do_save` writes it to `$XDG_CONFIG_HOME/osimager/config.json` (default `~/.config/osimager/`). The `--local` override sets `settings['local_only'] = True` BEFORE that save, so `--set ... --local` also persists `local_only: true`. Every later run, including the user's own builds, then behaves as `--local`.

What bit us: testing `--latest --local` with `--set iso_path=<scratch dir>` rewrote the user's config with a scratch `iso_path` and `local_only: true`. The next run looked like a code bug: `--latest` without `--local` resolved to the newest LOCAL version. It was the saved config. The fix was restoring `iso_path` and `local_only: false` from a `--show-config` taken earlier.

To test against a different iso_path or settings, isolate the config dir instead:
```
mkdir -p $S/cfg/osimager; cp -r ~/.config/osimager/{locations,platforms} $S/cfg/osimager/
sed 's#"<old iso_path>"#"<new>"#' ~/.config/osimager/config.json > $S/cfg/osimager/config.json
XDG_CONFIG_HOME=$S/cfg python3 bin/mkosimage ...
```
Run `--show-config` first and compare it against the real config afterwards. Delete the copy afterwards, since `locations/` can hold credentials.
