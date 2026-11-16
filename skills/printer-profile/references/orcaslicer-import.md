# Importing from OrcaSlicer

Offer this first when creating a printer profile. It fills the printer and material basics; calibration values are not in slicer presets and stay at defaults.

## Run it

The plugin root is given in the skill's SKILL.md.

```bash
cad run <plugin root>/scripts/orca_import.py --list
cad run <plugin root>/scripts/orca_import.py --printer "<machine preset>" --process "<process preset>" --filament "<filament preset>" [--filament ...] --out printer-<name>.toml
```

1. `--list` shows the user's printer (machine), process and filament presets. Let the user pick one printer, one process (their usual quality) and each filament they use.
2. Run the import. It resolves each preset's parents, maps the fields below, and writes the profile with the remaining keys commented out.
3. Show the user the result and what couldn't be resolved.

## Where presets live

| OS | Folder |
|---|---|
| Windows | `%APPDATA%\OrcaSlicer\` |
| macOS | `~/Library/Application Support/OrcaSlicer/` |
| Linux | `~/.config/OrcaSlicer/` (Flatpak: `~/.var/app/<app id>/config/OrcaSlicer/`) |

- User presets: `user/<id>/{machine,process,filament}/*.json`. There may be several `<id>` folders (`default`, `Default`, a cloud account id); list all, without duplicates.
- Vendor presets: `system/<Vendor>/...` and the app's `resources/profiles/`.

## Field mapping

| Profile key | Preset | OrcaSlicer key | Note |
|---|---|---|---|
| `[printer].name` | machine | `printer_model`, else preset `name` | |
| `build_volume` X, Y | machine | `printable_area` | Polygon of `"XxY"` points → bounding box |
| `build_volume` Z | machine | `printable_height` | |
| `nozzle` | machine | `nozzle_diameter[0]` | |
| `min_layer_height`, `max_layer_height` | machine | same names, `[0]` | |
| `line_width` | process | `outer_wall_line_width`, else `line_width` | |
| `layer_height` | process | `layer_height` | |
| `first_layer_height` | process | `initial_layer_print_height` | |
| `[slicer]` values | process | `xy_hole_compensation`, `xy_contour_compensation`, `elefant_foot_compensation` (Orca's spelling), `slice_closing_radius`, `wall_loops` | |
| `materials.<name>.type` | filament | `filament_type[0]` | Table name from vendor + type, lowercase |
| `shrinkage_pct` | filament | `filament_shrink[0]` | `"100%"` means none set; only store when it differs |

## Pitfalls

- **User presets have no `"type"` field.** Take the kind from the folder (`machine`, `process`, `filament`).
- **Values are strings or one-element lists** (`["0.4"]`, `"100%"`, `"0.42"`). Parse to numbers; percentages of nozzle size (`"105%"`) mean × nozzle.
- **Parents can be missing.** A user preset's `inherits` may name a preset no longer in any vendor profile. Use the values the user file has, fall back to defaults for the rest, and tell the user which preset couldn't be resolved.
- **Per-extruder lists:** take index 0 unless the user says otherwise.
- Don't read or copy unrelated fields (G-code, print host addresses, API keys).
