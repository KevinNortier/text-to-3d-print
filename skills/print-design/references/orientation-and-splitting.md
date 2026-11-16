# Orientation and splitting

Decide the print orientation **before modeling**. It decides which features need teardrops, chamfers, bridges or fins, and where the part is weak.

Values in `code` are `printer.toml` keys; read them through `load_printer()`.

## Choosing the orientation

Check, in this order:

1. **Load.** Layers bond at roughly half the strength of the strands along them. Orient so the main load runs along the layers or presses them together, never pulls or levers them apart.
   - A hook or L-bracket printed standing up breaks at the corner along a layer line. Lay it on its side.
   - A bolt through a **vertical** hole clamps the layers (good). Through a **horizontal** hole it wedges them apart (bad).
   - A boss or pin standing up snaps at its base under side load. Lying down it's strong but less round.
   - Snap-fit arms and living hinges lie flat, so they bend along the strands.
2. **Bed contact.** Largest flat face on the bed: better adhesion, fewer supports.
3. **Overhangs and bridges.** Minimise faces steeper than `max_overhang_deg` and spans longer than `max_bridge_mm`. Rotating 90° or 180° often removes most of them.
4. **Accuracy.** Holes and bores that must be round print **vertical**. Horizontal holes need teardrops and come out less exact.
5. **Looks.** Visible faces up or vertical; supports and the bed side on hidden faces. Shallow slopes stair-step visibly, so don't leave a cosmetic slope nearly flat to the bed.
6. **Stability.** Tall, thin parts wobble: lay them down, widen the base, or add fins or gussets.

When load and looks conflict, load wins for functional parts. A 45° tilt can compromise between loads from several directions (usually needs supports or fins).

State the chosen orientation and the reason in one line before modeling, and model in that orientation (Z up = print direction) so the rules below apply directly.

## When to split

Split the part when:

- it doesn't fit `build_volume` (leave a few mm margin for brim and skirt),
- no orientation avoids large unsupported overhangs or bridges,
- different regions need different orientations for strength (e.g. a bracket arm and a mounting plate), or
- a region must print vertical for roundness while the rest must lie flat.

## Where to cut

- On flat faces, so each piece has a large flat face on the bed.
- Away from fits, thin walls, snap-fits and load paths. A glued seam is weaker than the material beside it only if it's poorly placed; under load, put it where it's compressed, not peeled.
- At hidden or natural lines (edges, grooves) on visible parts.
- Each piece should then pass the orientation check above on its own.

## Joining the pieces

| Method | When | See |
|---|---|---|
| Alignment pins + glue | Permanent, most common | `joints.md` |
| Dovetail | Slides together; self-aligning; can be glued | `joints.md` |
| Screws into heat-set inserts | Must come apart; strong | `hardware.md` |
| Magnets | Covers and access panels | `hardware.md` |
| Snap-fits | Toolless, repeated assembly | `joints.md` |
| None | Pieces that simply rest on each other | – |

Model the split in CAD with `split()` and `alignment_pins()`, so the joint is parametric and sized from `printer.toml`.

For an existing mesh, OrcaSlicer's and PrusaSlicer's cut tool can split and add connectors. Their default connector tolerance is 0, so tell the user to set the size tolerance to `2 × snug_fit_per_side` (or `2 × glue_gap_per_side` for glued plugs).
