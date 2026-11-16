# text-to-3d-print

Design parts that print well and fit the first time, with an AI agent.

text-to-3d-print is a Claude Code plugin for **FDM 3D printing**. It adds design-for-printing knowledge on top of [text-to-cad](https://github.com/earthtojake/text-to-cad): print orientation and splitting, fits and clearances, teardrop and floating holes, heat-set inserts, nut traps, pins, dovetails, snap-fits, support fins, and test prints that calibrate the values for *your* printer.

## Built on text-to-cad

This plugin is an add-on to, and inspired by, [text-to-cad](https://github.com/earthtojake/text-to-cad) by [@earthtojake](https://github.com/earthtojake). text-to-cad does the CAD work: it writes models as Python scripts with [build123d](https://github.com/gumyr/build123d), builds them in its server, shows them in its viewer, checks meshes, slices with OrcaSlicer and sends prints to Bambu Lab printers.

text-to-3d-print doesn't replace any of that. It decides *what* to model so a part prints: which way it lies on the bed, how much gap a lid needs, how big the hole for an M3 insert should be, and how to bridge a hole above a counterbore. It also supplies build123d helpers that text-to-cad models import. text-to-cad is required.

## Install

1. Install text-to-cad by following [its install instructions](https://github.com/earthtojake/text-to-cad#readme). It sets up the `cad` command and the plugin.

2. Add this plugin in Claude Code:
   ```
   /plugin marketplace add KevinNortier/text-to-3d-print
   /plugin install text-to-3d-print@text-to-3d-print
   ```

The plugin declares text-to-cad as a dependency, so Claude Code checks that it's installed and enabled.

## Skills

| Skill | What it does |
|---|---|
| `print-design` | Designs or changes a part for printing: orientation and splits first, then fits, hardware and printable features, modeled with text-to-cad and checked before slicing. |
| `test-prints` | Small prints before a long one: pieces broken out of your model to test one fit in several sizes, or calibration coupons for fits, holes, inserts, overhangs, bridges, corner reliefs, text, hole-in-hole and dovetails. |
| `printer-profile` | Creates and updates `printer.toml` for your printer, nozzle and materials, including an import from OrcaSlicer presets, and saves test-print results as calibrated values. |

Example requests:

- "Design a wall bracket for a 20 mm pipe, with two M4 screws."
- "Make a box with a snap-fit lid, printed in PETG."
- "This enclosure is too big for my bed. Split it."
- "Set up my printer from OrcaSlicer."
- "Make a test print for the lid fit before I print the whole box."
- "Calibrate my fits and insert holes."

## The printer profile

Every number the skills use (fit gaps, hole oversize, insert holes, overhang and bridge limits, and more) comes from a `printer.toml` in your project. One file per printer and nozzle: `printer.toml`, or `printer-<name>.toml` when there are several.

- **No file?** The skills use defaults for a 0.4 mm nozzle, 0.2 mm layers and PLA, and say so.
- **Materials** adjust the defaults: PETG gets a little more clearance and shorter bridges, ABS and ASA get mouse ears and fillets, silk and fibre-filled materials get warnings.
- **Calibration:** print the calibration coupons once per printer and material, report which piece fit, and the value is saved as calibrated. Calibrated values are never overwritten by defaults.

See [`templates/printer.toml`](templates/printer.toml) for every setting and its default.

## Helpers

The `print3d` package (in [`lib/print3d`](lib/print3d)) is copied into your project the first time it's needed (`src/lib/print3d`), so your models keep working without the plugin. Models import it next to text-to-cad:

```python
import build123d as bd
from cad import model
from lib.print3d import find_profile, load_printer, heatset_hole, teardrop_hole, bed_chamfer

PROFILE = find_profile(root=__file__)


@model
def bracket():
    p = load_printer(path=PROFILE)
    body = bd.Box(40, 20, 10, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    body = bed_chamfer(body, profile=p)
    body -= bd.Pos(-10, 0, 10) * heatset_hole("M3", p)
    body -= bd.Pos(10, 0, 5) * teardrop_hole(5.3, 30, "Y", p)
    return body
```

It covers holes and fits, corner reliefs, teardrops, hole-in-hole bridging, sacrificial layers, bed chamfers and fillets, labels, mouse ears, heat-set inserts (the common ruthex / CNC Kitchen geometry, M2 to M8 and UNC), nut traps, magnet pockets, splitting with alignment pins, dovetails, snap-fits, support fins, and test-print and calibration coupon generators.

## Repository layout

```
.claude-plugin/        plugin and marketplace manifests
skills/                print-design, test-prints, printer-profile (SKILL.md + references)
lib/print3d/           build123d helpers and their data (defaults, insert table)
scripts/               install_lib.py (copy helpers into a project), orca_import.py (OrcaSlicer → printer.toml)
templates/printer.toml every profile setting with its default
tests/check_helpers.py builds every helper and coupon and checks the results
```

## Development

Run the helper checks with text-to-cad's Python environment:

```bash
cad run tests/check_helpers.py [OUT_DIR]
```

With `OUT_DIR`, every result is also exported as STL. Validate the plugin with `claude plugin validate .`.

The default values are starting points from public design guides, insert datasheets and slicer sources. Test prints on your own printer beat any table.

## License

[MIT](LICENSE)
