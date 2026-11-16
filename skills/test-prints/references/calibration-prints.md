# Calibration prints

Generic coupons that measure what a printer + material combination needs. Results go into the printer profile, so every later design uses them. Print once per printer, nozzle and material, and again after hardware changes.

## The coupon set

Generate coupons with `coupons(profile, which=[...], insert="M3", ref_d=3.0)`. It returns `{name: [parts]}`; `layout()` puts them on one plate. They're sized from the active printer profile (nozzle, line width, layer height), each value is labelled on the coupon (fractions of a mm in hundredths: `15` = 0.15 mm, insert steps in hundredths too), and each prints in the orientation the feature is used in. The user can print one coupon or all.

Names: `fit`, `hole`, `heatset`, `overhang`, `bridge`, `corner`, `text`, `hole_in_hole`, `dovetail`. The nut trap, print-in-place and bed-chamfer coupons have no ready-made generator: build them on request from `nut_trap()`, two parts with `pip_gap_xy` / `pip_gap_z`, and `bed_chamfer()` at a few sizes, each labelled with `tab_label()`.

| Coupon | What it shows | Updates |
|---|---|---|
| **Fit gauge:** pins and matching holes, 0.0–0.4 mm per side in 0.05 steps, vertical and horizontal | Which gap is press, snug and sliding | `press_fit_per_side`, `snug_fit_per_side`, `clearance_per_side` |
| **Hole gauge:** vertical holes for a reference (M3 screw, a rod or drill shank the user has) at several oversizes | Smallest hole the reference passes freely | `hole_oversize` |
| **Insert holes:** for the user's inserts, datasheet hole + 0.0 / 0.1 / 0.2 / 0.3 | Which one seats with slight resistance and holds | `heatset_oversize`, `[heatset]` entry |
| **Nut trap:** pockets at several clearances | Nut slides in / presses in | `nut_clearance_per_side` |
| **Print-in-place:** hinges or sliders at several gaps (XY and Z) | Smallest gap that breaks free and moves | `pip_gap_xy`, `pip_gap_z` |
| **Overhang fan:** 30°–70° in 5° steps | Steepest clean overhang | `max_overhang_deg` |
| **Bridge ladder:** 5–40 mm spans | Longest clean bridge | `max_bridge_mm` |
| **Corner relief:** square pegs in pockets with no relief, dog-bone, T-bone and slot | Which seats fully and looks acceptable | `corner_relief_dia`, `corner_slot` |
| **Bed-edge chamfer:** steps of chamfer size | Smallest that hides elephant's foot | `elephant_foot_chamfer` |
| **Hole-in-hole:** with and without the octagon step, a few hole sizes | Clean hole roofs; size where the octagon is needed | `bridge_step_layers` |
| **Text:** heights 2–8 mm, cut and raised | Smallest readable text | `min_text_height` |
| **Dovetail:** 10° / 15° / 20° at a few clearances | Fit and hold | `dovetail_angle_deg` |

For a first calibration, suggest the fit gauge, hole gauge and (if the user has inserts) insert holes: they matter most for functional parts.

## Running a calibration

1. Confirm the printer profile and material; calibration values are stored per material.
2. Ask which coupons to print; generate them on one plate if they fit, else several.
3. Tell the user: print with their usual settings for that material (calibration only holds for those settings), then how to judge each coupon.
4. Ask for the results per coupon, in plain words ("0.15 slides, 0.10 is tight").
5. Translate the results into profile values and hand them to the `printer-profile` skill to save, marked as calibrated with the date and the range tested.

## Without a printer

If the user can't print now, say that designs use uncalibrated defaults, and offer to generate the coupons for later.
