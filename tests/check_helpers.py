"""Build every print3d helper and check the result is a valid, non-empty solid.

    cad run tests/check_helpers.py [OUT_DIR]

With OUT_DIR, each result is also exported as STL there.
"""

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))

import build123d as bd  # noqa: E402

import print3d as p3  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
P = p3.load_printer(root=ROOT / "tests")  # no profile there: defaults

block = bd.Box(30, 20, 15, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
holes, pin = p3.alignment_pins([(-8, 0), (8, 0)], 4, profile=P, z=7.5)
tail, socket = p3.dovetail(10, 6, 5, P)

CASES = {
    "teardrop_hole": lambda: block - bd.Pos(0, 0, 7.5) * p3.teardrop_hole(8, 40, "X", P),
    "teardrop_hole_flat": lambda: block - bd.Pos(0, 0, 7.5) * p3.teardrop_hole(8, 40, "Y", P, flat_top=True),
    "bed_chamfer": lambda: p3.bed_chamfer(block, profile=P),
    "bed_fillet": lambda: p3.bed_fillet(block, profile=P),
    "bridged_hole_round": lambda: block - bd.Pos(0, 0, 4) * p3.bridged_hole(3.4, 6.5, 11, P, cavity_depth=5),
    "bridged_hole_hex_octagon": lambda: block - bd.Pos(0, 0, 4) * p3.bridged_hole(9, ("hex", 14), 11, P,
                                                                                 cavity_depth=5, octagon=True),
    "sacrificial_layer": lambda: block - p3.sacrificial_layer(bd.Cylinder(2, 40), 7.5, P),
    "label": lambda: block - bd.Pos(0, 0, 15) * p3.label("M3", profile=P),
    "raised_label": lambda: block + bd.Pos(0, 0, 15) * p3.raised_label("OK", profile=P),
    "mouse_ears": lambda: block + p3.mouse_ears(p3.bed_corners(block), P),
    "hole_vertical": lambda: block - bd.Pos(0, 0, 15) * p3.hole(3, 15, P, chamfer=0.5),
    "hole_horizontal_small": lambda: block - bd.Pos(0, 0, 7.5) * p3.hole(3, 40, P, axis="X"),
    "hole_horizontal_teardrop": lambda: block - bd.Pos(0, 0, 7.5) * p3.hole(6, 40, P, axis="Y"),
    "pocket_none": lambda: block - bd.Pos(0, 0, 15) * p3.relieved_pocket(10, 8, 5, "none", P),
    "pocket_dogbone": lambda: block - bd.Pos(0, 0, 15) * p3.relieved_pocket(10, 8, 5, "dogbone", P),
    "pocket_tbone": lambda: block - bd.Pos(0, 0, 15) * p3.relieved_pocket(10, 8, 5, "tbone", P),
    "pocket_slot": lambda: block - bd.Pos(0, 0, 15) * p3.relieved_pocket(10, 8, 5, "slot", P),
    "heatset_hole": lambda: block - bd.Pos(0, 0, 15) * p3.heatset_hole("M3", P),
    "heatset_boss_M4": lambda: p3.heatset_boss("M4", P),
    "nut_trap_side": lambda: block - bd.Pos(0, 0, 5) * p3.nut_trap("M3", P),
    "nut_trap_buried": lambda: block - bd.Pos(0, 0, 5) * p3.nut_trap("M4", P, insertion="buried"),
    "nut_trap_square_top": lambda: block - bd.Pos(0, 0, 5) * p3.nut_trap("M3", P, kind="square", insertion="top"),
    "magnet_pocket": lambda: block - bd.Pos(0, 0, 15) * p3.magnet_pocket(6, 3, P),
    "split_lower": lambda: p3.split(block, 7.5)[0] - holes,
    "split_upper": lambda: p3.split(block, 7.5)[1] - holes,
    "pin": lambda: pin,
    "dovetail_tail": lambda: bd.Box(30, 10, 5, align=(bd.Align.CENTER, bd.Align.MAX, bd.Align.MIN)) + tail,
    "dovetail_socket": lambda: bd.Box(30, 12, 5, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN)) - socket,
    "snap_fit": lambda: bd.Box(4, 12, 5, align=(bd.Align.MAX, bd.Align.MIN, bd.Align.MIN)) + p3.snap_fit(profile=P),
    "snap_fit_removable": lambda: p3.snap_fit(exit_angle=50, profile=P),
    "support_fin": lambda: bd.Box(10, 10, 30, align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN))
    + p3.support_fin(25, profile=P),
    "breakout": lambda: p3.breakout(block - bd.Pos(0, 0, 15) * p3.heatset_hole("M3", P), (0, 0, 12), (12, 12, 8)),
    "tab_label": lambda: p3.tab_label(bd.Box(10, 10, 3, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)),
                                      "15", P),
}
for name, parts in p3.coupons(P).items():
    for i, part in enumerate(parts):
        CASES[f"coupon_{name}_{i}"] = (lambda part=part: part)

ok = True
for name, make in CASES.items():
    try:
        shape = make()
        solids = shape.solids()
        valid = shape.is_valid
        vol = shape.volume
        bb = shape.bounding_box()
        good = valid and vol > 0 and len(solids) >= 1
        ok &= good
        print(f"{'OK ' if good else 'BAD'} {name:28s} solids={len(solids):2d} vol={vol:9.1f} "
              f"size={bb.size.X:6.1f}x{bb.size.Y:6.1f}x{bb.size.Z:6.1f} valid={valid}")
        if OUT:
            OUT.mkdir(parents=True, exist_ok=True)
            bd.export_stl(shape, str(OUT / f"{name}.stl"))
    except Exception:
        ok = False
        print(f"ERR {name}")
        traceback.print_exc(limit=3)

print("insert M3:", p3.heatset_info("M3", P))
print("nut M3 pause z:", p3.nut_pause_z("M3", P), "max bed fillet:", P.max_bed_fillet())
sys.exit(0 if ok else 1)
