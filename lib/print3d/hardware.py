"""Heat-set inserts, captive nuts and magnets. Cutters open at z = 0 and go down unless noted."""

from __future__ import annotations

import tomllib

import build123d as bd

from .features import _prof
from .fits import hole_diameter
from .printer import DATA, Printer

_TOP_DOWN = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX)
_BOTTOM_UP = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)

# ISO 4032 hex nuts / DIN 562 thin square nuts: across flats, height
HEX_NUTS = {"M2": (4.0, 1.6), "M2.5": (5.0, 2.0), "M3": (5.5, 2.4), "M4": (7.0, 3.2),
            "M5": (8.0, 4.7), "M6": (10.0, 5.2), "M8": (13.0, 6.8)}
SQUARE_NUTS = {"M3": (5.5, 1.8), "M4": (7.0, 2.2), "M5": (8.0, 2.7), "M6": (10.0, 3.2)}


def inserts() -> dict:
    with open(DATA / "heatset_inserts.toml", "rb") as f:
        return tomllib.load(f)["inserts"]


def insert(spec: str) -> tuple[str, dict]:
    """Look up an insert: 'M3' (the standard length), 'M3x5.7', 'M3 short', 'M3x5x4'."""
    table = inserts()
    key = spec.strip().replace(" ", "") if spec.strip().replace(" ", "") in table else spec.strip()
    if key in table:
        return key, table[key]
    low = spec.lower().replace(" ", "")
    for k, v in table.items():
        if low in [a.lower().replace(" ", "") for a in v.get("aliases", [])]:
            return k, v
    for k, v in table.items():
        if v["thread"].lower() == low and v.get("default"):
            return k, v
    raise KeyError(f"Unknown insert {spec!r}; known: {', '.join(table)}")


def heatset_info(spec: str = "M3", profile: Printer | None = None) -> dict:
    """Hole diameter, depth, minimum wall and boss diameter for an insert on this printer."""
    p = _prof(profile)
    key, ins = insert(spec)
    over = p.heatset_overrides.get(key) or p.heatset_overrides.get(spec, {})
    hole_d = over.get("hole", round(ins["hole"] + p.heatset_oversize, 3))
    depth = over.get("depth", round(ins["length"] + 1.0, 2))
    wall = max(ins["wall"], p.min_wall)
    return {"insert": key, "hole": hole_d, "depth": depth, "wall": wall,
            "boss_d": round(hole_d + 2 * wall, 2), "length": ins["length"], "od": ins["d1"],
            "calibrated": bool(over)}


def heatset_hole(spec: str = "M3", profile: Printer | None = None, depth: float | None = None,
                 chamfer: float = 0.5) -> bd.Part:
    """Cutter for an insert pressed in from the top (z = 0)."""
    info = heatset_info(spec, profile)
    depth = depth or info["depth"]
    cut = bd.Cylinder(info["hole"] / 2, depth, align=_TOP_DOWN)
    if chamfer:
        cut += bd.Cone(info["hole"] / 2, info["hole"] / 2 + chamfer, chamfer, align=_TOP_DOWN)
    return cut


def heatset_boss(spec: str = "M3", profile: Printer | None = None, height: float | None = None,
                 wall: float | None = None) -> bd.Part:
    """A standalone boss standing on z = 0 with an insert hole opening at its top."""
    info = heatset_info(spec, profile)
    height = height or info["depth"] + 1.0
    outer = info["hole"] / 2 + (wall or info["wall"])
    boss = bd.Cylinder(outer, height, align=_BOTTOM_UP)
    return boss - bd.Pos(0, 0, height) * heatset_hole(spec, profile)


def nut_info(size: str = "M3", profile: Printer | None = None, kind: str = "hex") -> dict:
    p = _prof(profile)
    af, h = (HEX_NUTS if kind == "hex" else SQUARE_NUTS)[size]
    c = p.nut_clearance_per_side
    return {"across_flats": af, "height": h, "pocket_af": round(af + 2 * c, 3),
            "pocket_h": p.layers(h + 2 * c)}


def nut_trap(size: str = "M3", profile: Printer | None = None, kind: str = "hex",
             insertion: str = "side", slot_length: float = 10.0) -> bd.Part:
    """Nut pocket cutter with its bottom at z = 0, centred on the screw axis.

    insertion: "side" (slot along +X to slide the nut in), "top" (open upward), "buried"
    (closed; pause the print at nut_pause_z() above this pocket's bottom and drop the nut in).
    The pocket height is rounded up to whole layers. Screw holes are separate (fits.hole).
    """
    info = nut_info(size, profile, kind)
    af, h = info["pocket_af"], info["pocket_h"]
    shape = bd.RegularPolygon(af / 2, 6, major_radius=False) if kind == "hex" else bd.Rectangle(af, af)
    pocket = bd.extrude(shape, amount=h)
    if insertion == "side":
        pocket += bd.Box(slot_length, af, h, align=(bd.Align.MIN, bd.Align.CENTER, bd.Align.MIN))
    elif insertion == "top":
        pocket += bd.extrude(bd.Plane.XY.offset(h) * shape, amount=50)
    elif insertion != "buried":
        raise ValueError("insertion: side, top or buried")
    return pocket


def nut_pause_z(size: str = "M3", profile: Printer | None = None, kind: str = "hex") -> float:
    """Height above the pocket bottom to pause at (before the first covering layer)."""
    return nut_info(size, profile, kind)["pocket_h"]


def magnet_pocket(d: float, h: float, profile: Printer | None = None, fit: str = "press",
                  buried: bool = False) -> bd.Part:
    """Cylindrical magnet pocket. Open: opening at z = 0 going down. Buried: bottom at z = 0, height in whole layers
    (pause at the returned solid's top height)."""
    p = _prof(profile)
    dia = hole_diameter(d, p, fit, metal=True)
    if buried:
        return bd.Cylinder(dia / 2, p.layers(h + 0.1), align=_BOTTOM_UP)
    return bd.Cylinder(dia / 2, h + 0.1, align=_TOP_DOWN)
