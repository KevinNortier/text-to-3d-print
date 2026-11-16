---
name: print-design
description: Designs parts for FDM 3D printing with text-to-cad - print orientation and splitting, fits and clearances, teardrop and floating holes, heat-set inserts, nut traps, pins, dovetails, snap-fits and supportless features, sized from the project's printer.toml. Use alongside text-to-cad's cad skill whenever a part being designed or changed will be 3D printed, or the user asks how to make a part print or fit better.
---

# Print design

Make parts that print without fuss and fit the first time. Modeling itself is done with text-to-cad's `cad` skill (build123d); this skill decides *what* to model and supplies helpers. FDM only.

Plugin root: `${CLAUDE_PLUGIN_ROOT}`. References are in `${CLAUDE_PLUGIN_ROOT}/skills/print-design/references/`.

## Setup (once per project)

1. **Printer profile.** Look for `printer.toml` / `printer-*.toml` in the project root. If none, offer to create one with the `printer-profile` skill (OrcaSlicer import takes a minute). If the user declines, continue on defaults: 0.4 mm nozzle, 0.2 mm layers, PLA.
2. **Helpers.** Copy them into the project:
   ```bash
   cad run ${CLAUDE_PLUGIN_ROOT}/scripts/install_lib.py <project dir>
   ```
   They land in `src/lib/print3d/` (or `lib/print3d/` without `src/`). If it reports an older copy, ask before rerunning with `--update`.
3. Tell the user in one line which profile and material are in use, and whether values are calibrated or defaults (`load_printer(path=...).summary()`).

## Workflow

1. **Clarify.** What the part does, its size, loads, what it mates with (screws, inserts, bearings, other printed parts), and the material.
2. **Orientation and splits, before modeling.** Pick the print orientation for load, bed contact, overhangs, accuracy and looks; split if it doesn't fit `build_volume` or no orientation works. State the choice and why in one line. → `orientation-and-splitting.md`
3. **Interfaces.** List every fit and hardware interface and pick its fit class or hardware (insert size, nut, magnet, pin). → `tolerances-and-fits.md`, `hardware.md`, `joints.md`
4. **Model** with the `cad` skill, in print orientation (Z up = build direction), using the helpers and these rules:
   - overhangs within `max_overhang_deg`, bridges within `max_bridge_mm`, horizontal holes as teardrops, holes over cavities bridged or with a sacrificial layer → `printable-features.md`
   - bed edges chamfered, load-bearing inner corners filleted, walls in whole line widths → `printable-features.md`, `strength.md`
   - material-specific limits and warnings → `materials.md`
5. **Check.** Export an STL and run text-to-cad's `dfam-check` with the profile's overhang limit; fix findings in the model.
6. **Offer a test print** of the critical fits before a long print (`test-prints` skill), especially when the profile is uncalibrated.
7. **Hand off** to text-to-cad's `gcode` / `bambu-labs` skills for slicing and printing.

## Model script pattern

```python
import build123d as bd
from cad import model
from lib.print3d import find_profile, load_printer, heatset_hole, teardrop_hole, bed_chamfer

PROFILE = find_profile(root=__file__)   # module level: the server doesn't track folder searches


@model
def bracket():
    p = load_printer(path=PROFILE)      # inside the body: a profile edit rebuilds the model
    body = bd.Box(40, 20, 10, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    body = bed_chamfer(body, profile=p)
    body -= bd.Pos(-10, 0, 10) * heatset_hole("M3", p)
    body -= bd.Pos(10, 0, 5) * teardrop_hole(5.3, 30, "Y", p)
    return body
```

Always pass `profile=p` to helpers. Put the profile's values (fits, insert sizes) into the model's own parameters where the user may want to tune them.

## Helpers (`lib.print3d`)

Cutters are solids to subtract; Z is up. Each function's docstring has details.

| Need | Helpers |
|---|---|
| Profile | `find_profile`, `load_printer` → `p.summary()`, `p.fit(kind)`, `p.wall(t)`, `p.layers(h)`, `p.max_bed_fillet()`, `p.fits_on_bed(size)` |
| Holes and fits | `hole`, `hole_diameter`, `fit`, `teardrop_hole`, `relieved_pocket` (corner reliefs) |
| Printable features | `bridged_hole` (hole-in-hole), `sacrificial_layer`, `bed_chamfer`, `bed_fillet`, `label`, `raised_label`, `mouse_ears`, `bed_corners` |
| Hardware | `heatset_hole`, `heatset_boss`, `heatset_info`, `nut_trap`, `nut_pause_z`, `magnet_pocket` |
| Joints | `split`, `alignment_pins`, `dovetail`, `snap_fit` |
| Supports | `support_fin`, `tine_levels` |

## Tell the user

- the orientation to print in, and any part to flip (split pieces print cut-face down)
- fit classes used, and which values are uncalibrated defaults
- post-processing: sacrificial layers to open, mouse ears or fins to remove, pause heights for buried nuts or magnets, how to install inserts
- material warnings from the profile
