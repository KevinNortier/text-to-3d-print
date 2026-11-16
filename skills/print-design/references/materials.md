# Materials

`load_printer()` applies per-material defaults automatically from the material `type`. This file covers what changes in the **design**. Slicer settings (temperatures, brims, enclosures) belong to the slicer.

| Material | Design for it | Avoid |
|---|---|---|
| PLA | Forgiving; good bridges and overhangs; stiff | Clips and snap-fits (brittle), heat above ~60 °C, outdoor |
| PETG | Clips, outdoor parts, up to ~80 °C. Oozes: slightly more clearance. Shorter bridges | Long bridges, very tight fits |
| ABS | Tough, heat resistant, solvent-weldable. Shrinks and warps: fillet corners, maximise bed contact, mouse ears on sharp bed corners, avoid long thin parts that curl | Large flat parts without an enclosure |
| ASA | As ABS, UV-stable: the outdoor choice. Bridges worse than ABS | As ABS |
| PC | As ABS, warps more, highest heat resistance | As ABS |
| PA (nylon) | Tough, wear-resistant: hinges, gears, snap-fits. Highest shrinkage | Precise fits without calibration |
| TPU | Flexible parts, gaskets, bumpers. Thicker sections (walls ~1.5–2.5 mm, ~3 mm where it takes impacts). Fits hold by friction. Large print-in-place gaps. Few overhangs, very short bridges. Joined to a rigid plastic: mechanical interlocks, not layer adhesion | Bridges, overhangs, fine details |
| Silk PLA | Decorative parts | Loads, clips, threads (weak layers, brittle) |
| Wood- or metal-filled PLA | Decorative parts; thicker walls | Thin features, clips, loads (weak, brittle) |
| Carbon- or glass-fibre-filled | Stiff, dimensionally stable brackets; little warping | Impacts, snap-fits, loads across layers (brittle, weak layers). Needs a hardened nozzle ≥ 0.4 mm |

## Shrinkage

Materials shrink slightly as they cool (`shrinkage_pct`). Compensate in the **slicer** (scale %), not in the model, so the model keeps nominal sizes. Mention it for ABS, ASA, PC and PA parts with long dimensions, or fits between parts printed in different materials.

## Unknown material

Use PLA defaults and say so. For a new or unusual filament, suggest a calibration print.
