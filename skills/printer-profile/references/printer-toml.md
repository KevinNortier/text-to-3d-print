# Printer profile (`printer.toml`)

One TOML file per printer and nozzle, in the project root. It holds the printer, its materials, and values proven by test prints.

## Files and lookup

- `printer.toml`: a single printer.
- `printer-<name>.toml`: one per printer when there are several; `<name>` is a short lowercase slug (`printer-p1s.toml`, `printer-mk4s.toml`). A different nozzle on the same printer is its own file (`printer-p1s-0.6.toml`).

Which file to use:

1. The user names a printer → the file whose slug or `[printer].name` matches.
2. Exactly one file exists → that one.
3. Several and nothing says which → ask once; keep using it for the session.
4. None → offer to create one (`orcaslicer-import.md`, or ask). Otherwise continue on the defaults below: generic FDM, 0.4 mm nozzle, 0.2 mm layers, PLA.

Always tell the user which file is in use, and when values are defaults rather than calibrated.

## Schema

```toml
[printer]
name = "Example Printer"
build_volume = [200, 200, 200]    # mm, X Y Z
nozzle = 0.4
line_width = 0.42
layer_height = 0.2
first_layer_height = 0.2
min_layer_height = 0.08           # optional
max_layer_height = 0.3            # optional

[slicer]                          # optional, filled by an import; what the slicer already does
xy_hole_compensation = 0.0
xy_contour_compensation = 0.0
elephant_foot_compensation = 0.0
slice_closing_radius = 0.049
wall_loops = 3

[material]
active = "petg"                   # which [materials.*] table designs use by default

[materials.petg]
type = "PETG"
clearance_per_side = 0.25         # any key from the defaults table

[materials.petg.heatset]          # calibrated holes per insert; override the insert table
"M3x5.7" = { hole = 4.25 }

[materials.petg.calibrated]       # provenance of calibrated values
clearance_per_side = "2026-11-20, fit gauge, 0.10-0.30 tested"
```

Every key is optional. Material tables may be named freely (`petg`, `petg-brand-x`); `type` sets the material defaults.

## Defaults

Fits are **per side**; holes and inserts **on diameter**. All mm unless noted.

| Key | Default | Meaning |
|---|---|---|
| `nozzle` | 0.4 | Nozzle diameter |
| `line_width` | 1.05 × nozzle | Extrusion width; walls are multiples of it |
| `layer_height` | 0.2 | |
| `first_layer_height` | = layer_height | |
| `type` | PLA | Selects the material column below |
| `max_overhang_deg` | 45 | Steepest overhang from vertical (°) |
| `max_bridge_mm` | 15 | Longest bridge |
| `teardrop_min_dia` | 5 | Horizontal holes from this size get a teardrop |
| `hole_oversize` | 0.3 | Added to small vertical hole diameters |
| `press_fit_per_side` | 0.0 | |
| `snug_fit_per_side` | 0.1 | |
| `clearance_per_side` | 0.2 | Sliding / rotating |
| `glue_gap_per_side` | 0.2 | |
| `nut_clearance_per_side` | 0.15 | |
| `snap_clearance_per_side` | 0.25 | |
| `pip_gap_xy` | 0.3 | Print-in-place, sideways |
| `pip_gap_z` | 2 × layer_height | Print-in-place, vertical |
| `heatset_oversize` | 0.2 | Added to the insert's datasheet hole |
| `elephant_foot_chamfer` | 0.4 | Bed-edge chamfer |
| `corner_relief_dia` | 2 × line_width | Dog-bone / T-bone |
| `corner_slot` | [1.0, 0.1] | Corner slot depth, width |
| `support_gap_xy` | 0.2 | Support fin standoff |
| `support_gap_z` | 1 × layer_height | |
| `sacrificial_layers` | 1 | Layers |
| `bridge_step_layers` | 1 | Layers per hole-in-hole step |
| `dovetail_angle_deg` | 15 | ° |
| `min_text_height` | 4 | |
| `shrinkage_pct` | per material | % (compensate in the slicer) |

Derived, not stored: minimum wall = 2 × line_width; rib = 3 × line_width; tine height = layer_height; `max_bed_fillet()` from layer height and line width.

### Material adjustments to the defaults

Applied to **defaults only**, never to values the user set or calibrated. "Fits +x" means `snug_fit_per_side`, `clearance_per_side`, `nut_clearance_per_side`, `snap_clearance_per_side` and `glue_gap_per_side` each get +x.

| `type` | Adjustments | `shrinkage_pct` |
|---|---|---|
| PLA | – | 0.3 |
| PETG | fits +0.05; `max_bridge_mm` 10 | 0.4 |
| ABS | fits +0.05; `snap_clearance_per_side` 0.35 | 0.8 |
| ASA | as ABS; `max_bridge_mm` 10 | 0.7 |
| PC | as ABS | 0.7 |
| PA | as ABS | 1.5 |
| TPU | `clearance_per_side` 0.3; `pip_gap_xy` 0.5; `max_overhang_deg` 35; `max_bridge_mm` 5 | 0.6 |
| Silk PLA, wood-filled, metal-filled | as PLA (warn: decorative) | 0.3 |
| `*-CF`, `*-GF` | as the base material (warn: brittle, abrasive) | base material's |

### Imported slicer compensation

If `[slicer]` has non-zero `xy_hole_compensation`, reduce `hole_oversize` and `heatset_oversize` by it (the slicer already enlarges holes). If `elephant_foot_compensation` is non-zero, the bed-edge chamfer may be smaller. Gaps meant to stay open (corner slots, fin gaps) must be at least 2 × `slice_closing_radius`.

## Editing rules

- Ask before writing. Show the change (old → new) and the file.
- A value from a test print gets a `[materials.<name>.calibrated]` entry: date, which test, range tested.
- Don't overwrite a calibrated value with a default or a guess. Only a newer test print or the user replaces it.
- Keep comments and unknown keys the user added.
- When creating a file, write the known values and list the other keys commented out with their defaults, so the user can see what can be calibrated (start from the template in `templates/printer.toml`).
