# Model test prints

Small prints broken out of the user's own model, to check that one critical feature works before printing the whole part. Results go back into **that model's** parameters.

## 1. Find the critical features

List what can fail in this model, and ask the user which to test:

- fits between parts: lid on box, pin in hole, part in pocket, sliding parts
- heat-set insert holes, nut traps, magnet pockets
- snap-fits and clips (both fit and feel)
- print-in-place gaps
- dovetails and other joints
- bridges, overhangs or hole-in-hole regions at or past the profile's limits

Skip features already proven: same geometry and same printer, material and calibrated value.

## 2. Break them out

Use `breakout()` to cut a small region around each feature from the real model, plus its mating counterpart:

- Keep the real geometry, **the real print orientation** and enough surrounding wall (a few mm, or the full wall thickness) that the feature behaves as in the full part.
- Cut the region as small as possible: minutes, not hours, to print.
- Give each piece a flat face on the bed; add a thin base plate if needed.
- For a lid on a box: a short section of the rim and the matching section of the lid, not the whole box.

## 3. Vary the critical dimension

Use `variants(make, values)` to make variants of the one parameter that matters, centred on the current value. `make` is a function that builds the broken-out piece from that one value (with a text-to-cad model: call its part helper with the value):

| Feature | Parameter | Typical steps |
|---|---|---|
| Sliding / snug / press fit | the fit's `*_per_side` value | current −0.1 … +0.1 in 0.05 |
| Heat-set insert hole | hole diameter | −0.1 … +0.2 in 0.1 |
| Snap-fit | undercut, or clearance | 0.25 mm steps / 0.05 mm steps |
| Print-in-place | `pip_gap_xy` | 0.2 … 0.5 in 0.1 |

Three to five variants is usually enough. Vary one parameter at a time.

## 4. Label and lay out

- Label each variant with its value: `tab_label(piece, value_text(v))` adds a small labelled tab on the bed beside the piece (never on a mating face). `value_text(0.15)` gives `15` (hundredths of a mm); say so to the user.
- Lay out all variants and counterparts on one plate with `layout()`, in the orientation they'll have in the full print. Orientation changes the result.
- Export one file for the plate.

## 5. Print and report

Tell the user what to print, roughly how long it takes, and what to check:

- fits: which variant goes together as intended (by hand, with force, slides freely)
- inserts: which one seats with slight resistance and holds when screwed
- clips: which one clicks and holds without breaking

## 6. Feed back

- Write the winning value into the model's parameter and rebuild.
- If the result is a general property of the printer and material (a fit class, an insert size), offer to save it to the printer profile with the `printer-profile` skill, marked as calibrated.
- If none worked, extend the range in the direction of the best result and repeat.
