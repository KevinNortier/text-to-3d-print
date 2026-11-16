# Hardware in printed parts

Values in `code` are `printer.toml` keys.

## Choosing a screw joint

| Method | Reusable | Use |
|---|---|---|
| Heat-set insert | Many cycles, strong | Default for anything taken apart |
| Captive nut | Many cycles | Cheap, no tool; needs space for the nut |
| Self-tapping into plastic | A few cycles | Quick, permanent assemblies (M3: 2.8 mm hole) |
| Printed thread | Poor | Only large, coarse threads (≥ M8-ish), lids and caps |

## Heat-set inserts

Use `heatset_hole()` (and `heatset_boss()` for a standalone boss). It looks the insert up in the insert table and applies:

- **Hole:** the insert's datasheet hole diameter + `heatset_oversize` (printed holes shrink). A calibrated entry in `[heatset]` for that insert wins.
- **Depth:** at least the insert length + 1 mm, for displaced plastic and so the screw doesn't bottom out. Through holes are fine.
- **Wall:** at least the table's minimum wall around the hole; more under load.
- **Entry:** 0.5 mm chamfer to centre the insert.
- **Orientation:** the hole axis vertical (insert pressed in from the top) when possible; it's rounder and easier to install straight.

A hole that's too big loses far more strength than one slightly too small. If unsure, err small.

Ask which inserts the user has (brand, size, length). If unknown, assume the common M3 × 5.7 mm type and say so.

Tell the user how to install: soldering iron 10–20 °C above the print temperature, insert tip if available, let it sink under its own weight with light pressure, stop flush, keep it vertical, let it cool before loading. The insert should sit in the hole with slight resistance before heating.

## Captive nuts

`nut_trap()`:

- Hex (or square) pocket sized across flats + `2 × nut_clearance_per_side`; tighter to press the nut in so it can't fall out.
- **Side slot:** a slot from the side to slide the nut in. Easiest.
- **Buried (pause-at-height):** the pocket's top lands exactly on a layer boundary (round its height up to a multiple of `layer_height`). Tell the user the Z height to pause at, before the first layer that covers it. Close the top with a sacrificial layer or the hole-in-hole bridge (`printable-features.md`).

## Magnets

`magnet_pocket()`:

- Press-fit pocket (`press_fit_per_side`) open to a face, or
- Buried with a pause-at-height (same rules as buried nuts).
- Glue alone doesn't hold magnets reliably.
- Mark polarity for the user when pairs must attract.

## Screw holes and bosses

- Through holes: screw diameter + `hole_oversize` + `2 × clearance_per_side`.
- Enough material around holes: a hole concentrates stress. Thicken around it, or use a boss with a fillet at its base.
- Countersinks and counterbores on the top face print fine; on the bottom face (printed face-down) use the hole-in-hole bridge.
