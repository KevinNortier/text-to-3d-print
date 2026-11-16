# Joints between printed parts

Values in `code` are `printer.toml` keys. Fits are per side.

## Alignment pins and dowels

`alignment_pins()` places pins and matching holes across a split.

- **Print pins separately.** A pin printed in the same job as its hole fuses to it. Metal dowels or a length of filament also work.
- Printed pins lie down with a flat (**D-shaped**) side on the bed: strong along their length, no overhang.
- Length 2–3 × diameter, split about equally between the two parts.
- At least two pins per joint (one pin lets the parts rotate), spaced as far apart as the face allows.
- Hole diameter = pin diameter + 2 × the fit value:
  - removable: `snug_fit_per_side`
  - glued: `glue_gap_per_side`
  - for pins over 10 mm, or parts over 100 mm, add about 0.05 mm per side.
  - metal dowels also get `hole_oversize` (`metal=True`).
- `alignment_pins(points, d, z=cut_height)` returns `(holes, pin)`: subtract `holes` from both pieces, print one `pin` per point.

## Glue

- Super glue (cyanoacrylate): fast, needs touching surfaces; runs out of gaps. Works on PLA and PETG.
- Two-part epoxy: fills gaps (0.5 mm or more), strongest for structural joints.
- Solvent welding: ABS and ASA with acetone. Not PLA or PETG.

## Dovetails

`dovetail()`:

- Flank angle `dovetail_angle_deg` from the slide direction.
- Clearance on the **sliding flanks only**: `clearance_per_side` for joints that slide apart again, `snug_fit_per_side` for joints that stay assembled. Shoulders and roots stay nominal.
- Take the clearance off the male part.
- Print the dovetail profile lying in the XY plane, so the flanks aren't overhangs and layers don't split under load.
- Chamfer the entry ends.

## Snap-fits

`snap_fit()` makes a cantilever clip:

- **Undercut** (hook depth) 0.5–1.0 mm. Deeper needs a longer arm.
- **Entry angle** 30–45°.
- **Exit angle:** 90° = permanent (breaks before it releases); 45–60° = removable.
- **Arm:** long enough for the deflection; tapered, thicker at the root; **fillet the root**, never a sharp corner.
- **Clearance** `snap_clearance_per_side` between hook and housing.
- **Orientation:** the arm lies flat on the bed, so it bends along the strands. An arm standing up snaps at a layer line.
- **Rest state:** the arm is relaxed when closed; a permanently bent arm creeps and loosens.
- **Material:** PETG, ABS, ASA, PA or TPU. Warn the user that PLA clips are brittle; silk, wood-filled and fibre-filled clips break.
- Recommend a test print of just the clip.

Annular snaps (pen-cap style) are hard to print (360° overhang); prefer cantilevers.

## Print-in-place

See `tolerances-and-fits.md`.
