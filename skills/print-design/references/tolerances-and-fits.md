# Tolerances and fits

Printed parts are not CAD-exact: outer dimensions vary by about ±0.1–0.2 mm, and holes come out smaller. Every interface between two parts needs an intentional gap.

**Convention:** fit values are **per side** (offset each mating face by the value). Holes are specified **by diameter**. Values in `code` are `printer.toml` keys.

## Fit classes

| Fit | Key | Use |
|---|---|---|
| Press | `press_fit_per_side` | Bearings, permanent pins; needs force or a vice |
| Snug | `snug_fit_per_side` | Assembles by hand, doesn't fall apart; locating features, lids that stay on |
| Sliding / rotating | `clearance_per_side` | Box lids, hinge pins, sliders, moving parts |
| Glued | `glue_gap_per_side` | Room for adhesive |

Pick a class for **every** interface, state it, and use `fit()` to apply it. Apply the clearance to the part that's easier to reprint (usually the smaller, male one), not to both.

Two kinds of interface:

- **Printed to printed** (pin in a printed hole, lid on a box): gap = fit per side. Both parts' printing errors are already in the calibrated fit values.
- **Printed to metal or a bought part** (screw, rod, bearing, magnet): hole = part diameter + `hole_oversize` + 2 × fit. `hole_oversize` corrects the printed hole against an exact part. `hole()` and `hole_diameter()` do this (`metal=True`, the default).

## Holes

- Small vertical holes shrink: add `hole_oversize` to the diameter (`hole()` does this). A screw clearance hole is the screw's diameter + `hole_oversize` + `2 × clearance_per_side`.
- Holes that must be precise: print slightly undersize and ream or drill to size.
- Horizontal holes: see teardrops in `printable-features.md`.
- Chamfer hole entries and peg tips.

## Slicer compensation

If the profile shows non-zero slicer compensation (`xy_hole_compensation`, `xy_contour_compensation`, `elefant_foot_compensation` in OrcaSlicer), the slicer already corrects those sizes. Subtract it from the model's oversize, don't add both. `load_printer()` reports these when the profile was imported.

Don't send a model with FDM compensations baked in to another process (CNC, injection molding) without saying so.

## Corner reliefs (square parts in pockets)

Printed inner corners round off and bulge, so a square peg won't seat fully in a square pocket. Cut a relief into each inner corner of the **pocket**; `relieved_pocket(width, length, depth, kind=...)` makes the pocket with its reliefs:

| Kind | Shape | Use |
|---|---|---|
| `dogbone` | Circle `corner_relief_dia` placed to clear the corner diagonally | Default; also removes the stress-raising sharp corner |
| `tbone` | Same circle, offset along one wall | When one side is visible or the other wall is thin |
| `slot` | Thin slot `corner_slot` (depth × width) running diagonally out of the corner | Sharpest corner; the nozzle stops and seams in the slot. Check the slicer preview: gaps under ~0.1 mm get closed |

Reliefs remove some cross-section; check thin walls around the pocket.

## Print-in-place mechanisms

Hinges, chains and gears printed assembled:

- Sideways gap `pip_gap_xy`; vertical gap `pip_gap_z` (at least one to two layers).
- Chamfer the bottom of moving parts that touch the bed, or elephant's foot welds them.
- No moving surface may rest on a bridge or a sacrificial layer.

## Scaling

Scaling a model scales its clearances too. Regenerate from parameters instead of scaling an exported mesh.
