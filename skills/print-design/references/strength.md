# Strength of printed parts

## Layers are the weak direction

Across layers, a part has roughly half the strength it has along the strands, and it fails suddenly. Orientation is the biggest strength decision (see `orientation-and-splitting.md`). If the orientation can't change:

- tilt the part 45° (layers no longer form one failure plane),
- thicken the section where layers are pulled apart,
- run a metal rod or screw through a channel along the load,
- suggest slicer changes: hotter nozzle, less cooling, wider lines.

## Walls

- Wall thickness in **multiples of `line_width`**: 2 lines minimum, 3 or more for load-bearing walls. Avoid in-between thicknesses that leave a thin gap fill (e.g. 1.0 mm with 0.42 mm lines).
- Perimeters carry the load; infill adds little. Three perimeters is a good default; going from 20% to 100% infill adds little strength for a lot of material.
- A hollow part with thick walls beats a solid part with thin walls.

## Ribs and gussets

- Ribs about 3 × `line_width` thick, filleted into the wall.
- Ribs in the XY plane use continuous strands; vertical ribs are strong in compression, weaker in bending across layers.
- Gussets (triangular ribs) stabilise tall thin walls during printing and in use.
- Ribs under a top surface must be close enough that the top layers can bridge between them.

## Stress raisers

- Sharp inner corners crack first. Fillet load-bearing inner corners, 2–3 mm or as large as the design allows.
- Sudden thickness changes: taper or blend them.
- Holes concentrate stress at their sides: keep material around them, or add a boss.
- Corner reliefs (`tolerances-and-fits.md`) also remove sharp inner corners where a fillet would block a fit.

## Material

PLA is stiff but brittle and softens around 60 °C. For impacts, clips, heat or outdoor use, suggest a tougher material (`materials.md`).
