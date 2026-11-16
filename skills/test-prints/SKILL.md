---
name: test-prints
description: Makes small FDM test prints before a long print - pieces broken out of the user's own model to check one fit (a lid, a clip, an insert hole, a dovetail) in several sizes, and general calibration coupons that measure the printer's press, snug and sliding fits, hole and insert sizes, overhang and bridge limits. Use when the user wants to test a fit, calibrate tolerances, or print a test piece before the real part.
---

# Test prints

Small, fast prints that settle a dimension before the real print. Two kinds:

| | Model test print | Calibration print |
|---|---|---|
| Question | Will *this* lid / clip / insert hole fit? | What gaps does *this printer + material* need? |
| Geometry | Broken out of the user's model | Ready-made coupons |
| Result goes to | That model's parameters | The printer profile |
| Details | `references/model-test-prints.md` | `references/calibration-prints.md` |

Pick the kind from the request. For "test my lid" use a model test print. For "calibrate", a new printer or material, or an uncalibrated profile before a fit-critical design, suggest a calibration print. When unclear, ask in one line.

Plugin root: `${CLAUDE_PLUGIN_ROOT}`. References are in `${CLAUDE_PLUGIN_ROOT}/skills/test-prints/references/`.

## Setup

Same as the `print-design` skill: a printer profile (or stated defaults), and the helpers copied into the project with
`cad run ${CLAUDE_PLUGIN_ROOT}/scripts/install_lib.py <project dir>`. Test prints are sized for the active profile, so confirm the printer and material first.

## Building the plate

Write a text-to-cad model script that returns the plate, so it shows in the viewer and exports like any model:

```python
import build123d as bd
from cad import model
from lib.print3d import find_profile, load_printer, coupons, layout

PROFILE = find_profile(root=__file__)


@model
def calibration_plate():
    p = load_printer(path=PROFILE)
    parts = [s for group in coupons(p, which=["fit", "hole", "heatset"], insert="M3x5.7").values() for s in group]
    return layout(parts, p)
```

For a model test print, build the pieces with `breakout()`, the variants with `variants()`, label them with `tab_label()`, then `layout()`. Export with `cad export <id> plate.3mf` and hand off to text-to-cad's `gcode` / `bambu-labs` skills, or give the user the file.

## Results

- Ask what happened in plain words, per labelled piece ("15 slides, 10 is tight").
- Labels on pieces are hundredths of a mm (`15` = 0.15 mm); say so when handing over the plate.
- Model test print: write the winning value into the model's parameter and rebuild.
- Calibration print, or a model result that is really a printer + material property: pass the values to the `printer-profile` skill to save as calibrated (with date and range tested). Never save without asking.
- Nothing worked: extend the range toward the best piece and print again.
- The user can't print now: say designs stay on uncalibrated defaults, and offer to generate the plate for later.
