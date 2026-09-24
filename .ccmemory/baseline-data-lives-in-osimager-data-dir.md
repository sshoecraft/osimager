---
name: baseline-data-lives-in-osimager-data-dir
description: Baseline data is osimager/data/ inside the engine (v1.9.0+); osimager-data is retired. Engine install is a COPY — bin/mkosimage runs source, mkosimag…
metadata:
  type: project
---

Specs, platforms, files, tasks, scripts, ansible.json and examples live in `/src/osimager/osimager/data/` and ship as package data (`pyproject.toml` package-data `data/**/*`, bytecode excluded). `core.py` sets `system_data_dir` to `data/` beside itself; nothing imports `osimager_data`.

**Why:** the user decided two packages were more pain than one — the separate release cadence that motivated the v1.7.0 split never mattered.

**Two ways to run, two different trees:**
- `bin/mkosimage` (dev wrapper) runs the source tree → sees `/src/osimager/osimager/data` edits immediately.
- `mkosimage` on PATH (`~/.local/bin`) runs the **copied** user install in `~/.local/lib/python3.12/site-packages/osimager/` — NOT editable (`direct_url.json` has empty `dir_info`). Data/engine edits reach it only after `python3 -m pip install --user --break-system-packages --no-deps /src/osimager`. When the user says "install the data package", this is what they mean now. Earlier memories claiming the engine is an editable install are wrong.

**Leftovers:** `/src/osimager-data` and the pip-installed `osimager_data` still exist and are dead weight; editing them changes nothing.

Package-data by extension previously dropped extensionless/unusual files (alpine `answerfile`, openbsd `install.conf`, `*.ign`); after packaging changes, verify a wheel with a `comm` diff of `find osimager/data -type f` vs `python3 -m zipfile -l`.
