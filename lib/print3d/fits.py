"""Fits, holes and corner reliefs.

Two kinds of interface:
- printed to printed (pin in a printed hole, lid on a box): gap = 2 * fit per side.
- printed to metal or a bought part (screw, rod, bearing, magnet): hole = d + hole_oversize + 2 * fit,
  because hole_oversize corrects the printed hole's shrinkage against an exact part.
"""

from __future__ import annotations

import math

import build123d as bd

from .features import _prof, teardrop_hole
from .printer import Printer

_TOP_DOWN = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX)


def fit(kind: str, profile: Printer | None = None) -> float:
    """Per-side gap: press, snug, clearance/sliding, glue, nut, snap."""
    return _prof(profile).fit(kind)


def hole_diameter(d: float, profile: Printer | None = None, fit: str | None = None, metal: bool = True) -> float:
    """Model diameter for a hole that must take a part of diameter `d`."""
    p = _prof(profile)
    extra = (p.hole_oversize if metal else 0.0) + (2 * p.fit(fit) if fit else 0.0)
    return round(d + extra, 3)


def hole(d: float, depth: float, profile: Printer | None = None, fit: str | None = "clearance",
         axis: str = "Z", metal: bool = True, chamfer: float | None = None) -> bd.Part:
    """Hole cutter for a part of diameter `d`.

    axis "Z": vertical, opening at z = 0 going down to -depth, optional entry chamfer.
    axis "X"/"Y": horizontal, centred on the origin, teardrop from teardrop_min_dia up.
    """
    p = _prof(profile)
    dia = hole_diameter(d, p, fit, metal)
    if axis.upper() != "Z":
        if dia >= p.teardrop_min_dia:
            return teardrop_hole(dia, depth, axis, p)
        rot = (0, 90, 0) if axis.upper() == "X" else (90, 0, 0)
        return bd.Rot(*rot) * bd.Cylinder(dia / 2, depth)
    cut = bd.Cylinder(dia / 2, depth, align=_TOP_DOWN)
    if chamfer:
        cut += bd.Cone(dia / 2, dia / 2 + chamfer, chamfer, align=_TOP_DOWN)
    return cut


def relieved_pocket(width: float, length: float, depth: float, kind: str = "dogbone",
                    profile: Printer | None = None, fit: str | None = "snug") -> bd.Part:
    """Rectangular pocket cutter (opening at z = 0, going down) for a square part, with corner reliefs.

    kind: "dogbone", "tbone", "slot" or "none". The pocket is the part size + 2 * fit per side.
    """
    p = _prof(profile)
    gap = p.fit(fit) if fit else 0.0
    w, l = width + 2 * gap, length + 2 * gap
    sketch = bd.Rectangle(w, l)
    reliefs = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * w / 2, sy * l / 2
            if kind == "dogbone":
                r = p.corner_relief_dia / 2
                reliefs.append(bd.Pos(cx + sx * r / math.sqrt(2), cy + sy * r / math.sqrt(2)) * bd.Circle(r))
            elif kind == "tbone":
                r = p.corner_relief_dia / 2
                reliefs.append(bd.Pos(cx + sx * r, cy) * bd.Circle(r))
            elif kind == "slot":
                s_depth, s_width = p.corner_slot
                s_width = max(s_width, p.min_open_gap)
                along = (s_depth - s_width) / 2
                ux, uy = sx / math.sqrt(2), sy / math.sqrt(2)
                angle = 45 if sx * sy > 0 else -45
                reliefs.append(bd.Pos(cx + ux * along, cy + uy * along) * bd.Rot(0, 0, angle)
                               * bd.Rectangle(s_depth + s_width, s_width))
            elif kind != "none":
                raise ValueError("kind: dogbone, tbone, slot or none")
    for r in reliefs:
        sketch += r
    return bd.extrude(sketch, amount=depth, dir=(0, 0, -1))
