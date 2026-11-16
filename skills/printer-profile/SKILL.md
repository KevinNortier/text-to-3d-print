---
name: printer-profile
description: Creates, imports and updates the project's FDM printer profile (printer.toml or printer-<name>.toml) - printer, nozzle, layer height, build volume, materials and calibrated fit values - including importing from OrcaSlicer presets. Use when the user sets up a printer for 3D-printing designs, adds a printer, nozzle or material, asks what their profile contains, or reports a test-print result to save.
---

# Printer profile

One TOML file per printer and nozzle in the project root. The `print-design` and `test-prints` skills read it; this skill writes it. Schema, every default, material adjustments, file lookup and editing rules: `${CLAUDE_PLUGIN_ROOT}/skills/printer-profile/references/printer-toml.md`.

## Tasks

**Show.** Run
```bash
cad run -c "import sys; sys.path.insert(0, r'${CLAUDE_PLUGIN_ROOT}/lib'); from print3d import load_printer; print(load_printer(root=r'<project dir>').summary())"
```
and explain anything the user asks about. Point out uncalibrated values when fits matter.

**Create.**
1. Offer the OrcaSlicer import first (details: `references/orcaslicer-import.md`):
   ```bash
   cad run ${CLAUDE_PLUGIN_ROOT}/scripts/orca_import.py --list
   cad run ${CLAUDE_PLUGIN_ROOT}/scripts/orca_import.py --printer "<machine>" --process "<process>" --filament "<filament>" [--filament ...] --out <project dir>/printer.toml
   ```
   Let the user pick their printer, their usual process and the filaments they use. Report the notes it prints (missing parent presets, values not found).
2. Without OrcaSlicer, or if the user prefers: ask for printer name, build volume, nozzle, usual layer height and materials, and write the file from `${CLAUDE_PLUGIN_ROOT}/templates/printer.toml`.
3. File name: `printer.toml` for a single printer; `printer-<short-name>.toml` when there are or will be several. A second nozzle on the same printer is a separate file.

**Update.**
- Test-print results: set the value in the material's table and add a `[materials.<name>.calibrated]` entry (date, which test, range tested).
- New material: add a `[materials.<name>]` table with `type`; switch `[material].active` if the user wants it as the default.
- New printer or nozzle: a new file (import or ask), not a table in the existing one.

## Rules

- Ask before writing; show old → new and the file name.
- Never replace a calibrated value with a default or a guess; only a newer test print or the user replaces it.
- Keep the user's comments and any keys you don't know.
- Don't copy unrelated slicer data (G-code, print host addresses, API keys) into the profile.
