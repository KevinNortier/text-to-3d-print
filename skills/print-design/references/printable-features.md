# Printable features

Rules for geometry that prints without slicer supports. Z is the print direction. Values in `code` are `printer.toml` keys.

## Overhangs

- Faces may lean out up to `max_overhang_deg` from vertical. Beyond that, the underside sags or curls.
- Replace flat overhangs (90°) with a chamfer at `max_overhang_deg` or less, or a bridge.
- Quick check: a shape that opens upward like a **Y** prints; an **H** prints if the crossbar is a short bridge; a **T** needs support or a redesign.
- Stepped bridge: close a large roof with inverted-chamfer steps until the remaining span is short.

## Bridges

- Straight spans only, between two solid supports, no longer than `max_bridge_mm`.
- The underside always sags a little: keep bridge undersides off fit and sealing surfaces, or plan to clean them up.
- A bridge across a ring or curve prints as straight strands; curved bridges don't exist.

## Horizontal holes (axis parallel to the bed)

- Holes at or above `teardrop_min_dia`: `teardrop_hole()`. The top becomes two lines at 45° (or `max_overhang_deg`) meeting at a point. Fine for screws and rods that don't need to be round all the way round.
- Bores that must stay round (bearings, shafts, pins that rotate): print the hole **vertical** instead, or print it undersize and ream.
- Alternative: flat-topped teardrop (point cut off) when the height matters; the flat top is a short bridge.

## Hole on top of a larger cavity (hole-in-hole, floating holes)

For a small hole whose bottom starts on top of a bigger cavity: a counterbore printed face-down, a buried nut, a recess with a through hole. Use `bridged_hole()`. It builds these steps, each `bridge_step_layers` layers tall:

1. The big cavity ends.
2. **Slot:** two bridges across the cavity leave a slot exactly as wide as the small hole (slot edges tangent to the hole). Bridge across the cavity's **shorter** direction.
3. **Square:** the next step bridges at 90°. Its edges are also tangent to the hole and end on the slot's edges. The opening is now a square the size of the hole.
4. **Octagon** (only for larger holes): four edges on the square, four bridging its corners.
5. The round hole continues upward.

Rules:
- Each step's height **must equal the layer height** the part is sliced at. If the user slices with a different layer height, regenerate.
- The bridges make the region slightly weaker: add about 2 layers of material above the cavity.
- Use it when the hole must be clean without post-processing, or when a drill can't reach (a nut blocks it). Otherwise a sacrificial layer is simpler.

## Sacrificial layers

- A membrane `sacrificial_layers` thick closing a hole or cavity that would otherwise start in mid-air. The slicer bridges it; the user drills, cuts or melts it open after printing.
- Typical uses: the top of a captive nut pocket, the start of a vertical hole above a cavity.
- Tell the user it must be removed, and how.

## Support fins (designed-in break-away supports)

Use `support_fin()` when a part must print in an orientation that needs support (usually for strength), and slicer supports would scar a visible face or be hard to remove.

- A fin is a thin wall standing `support_gap_xy` off the part face, with **horizontal tines**: one layer tall, 1–2 line widths wide, fused into the part. The tines hold the part sideways; without them the part falls away from the fin.
- 7–8 tines near the base, spreading out higher up.
- A 1 mm thick elliptical pad on the bed under the fin.
- A ~2 mm chamfer on the part's bottom edge, so a tilted part doesn't start on a single line.
- Rounded fin tops (a sharp tip causes defects).
- Place fins on edges and corners, never in the middle of a visible face. Long parts get two fins on opposite sides.
- Gaps must be at least 2 × the slicer's gap-closing radius (≥ 0.1 mm), or the slicer fuses them.
- Small bores (≲ 6 mm) don't need fins; they bridge.

## Edges

| Edge | Use | Why |
|---|---|---|
| On the bed | Chamfer `elephant_foot_chamfer`, or a fillet no larger than `max_bed_fillet()` | First layers squish outward; a fillet starts as a 90° overhang |
| Vertical (along Z) | Fillet | Smoother motion, less ringing |
| Load-bearing inner corner | Fillet, 2–3 mm | Removes the stress raiser |
| Hole entry, peg tip | Chamfer | Guides assembly; fillets on mating parts collide |
| Overhanging edge | Chamfer within `max_overhang_deg` | Prints without support |
| Top edges | Either | Looks only |

Large fillets along Z stair-step; the bigger the radius, the smaller the layer height it needs.

## Text, labels and small details

- Text and logos as **cuts 0.8 mm deep**; text height at least `min_text_height`; strokes and details at least 0.8 mm (two line widths).
- Features on the bottom face: cuts, not raised.
- Fine text needs a smaller nozzle; layer height doesn't help in XY.
- Use `label()`.

## Mouse ears

On materials that warp (ABS, ASA, PC, PA) and on sharp corners touching the bed, add `mouse_ears()`: thin discs one or two layers tall at the corners, snapped off after printing. Tell the user to remove them.
