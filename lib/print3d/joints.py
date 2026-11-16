"""Splitting and joining: split, alignment pins, dovetails, snap-fits."""

from __future__ import annotations

import math

import build123d as bd

from .features import _prof
from .printer import Printer


def split(part: bd.Part, z: float) -> tuple[bd.Part, bd.Part]:
    """Split at the plane z = const. Returns (lower, upper); flip the upper piece to print it cut-face down."""
    plane = bd.Plane.XY.offset(z)
    return (bd.split(part, bisect_by=plane, keep=bd.Keep.BOTTOM),
            bd.split(part, bisect_by=plane, keep=bd.Keep.TOP))


def pin_hole_diameter(d: float, profile: Printer | None = None, fit: str = "snug", metal: bool = False) -> float:
    p = _prof(profile)
    per_side = p.fit(fit) + (0.05 if d > 10 else 0.0)
    return round(d + 2 * per_side + (p.hole_oversize if metal else 0.0), 3)


def alignment_pins(points, d: float = 4.0, length: float | None = None, profile: Printer | None = None,
                   fit: str = "snug", metal: bool = False, z: float = 0.0) -> tuple[bd.Part, bd.Part]:
    """Holes across a cut plane at height z, and one printable pin.

    Returns (holes, pin). Subtract `holes` from both pieces. The pin is D-shaped, lying on its flat;
    print `len(points)` of them separately. fit: "snug" (removable) or "glue". metal=True for metal dowels.
    """
    p = _prof(profile)
    length = length or 2.5 * d
    hole_d = pin_hole_diameter(d, p, fit, metal)
    reach = length / 2 + 0.3
    holes = None
    for x, y in points:
        h = bd.Pos(x, y, z) * bd.Cylinder(hole_d / 2, 2 * reach)
        holes = h if holes is None else holes + h
    pin = bd.Rot(0, 90, 0) * bd.Cylinder(d / 2, length)
    flat = d * 0.15
    pin -= bd.Pos(0, 0, -d / 2) * bd.Box(length + 2, d + 2, 2 * flat)
    pin = bd.Pos(0, 0, d / 2 - flat) * pin
    pin = bd.chamfer(pin.edges().filter_by(bd.GeomType.CIRCLE), length=min(0.4, d / 10)) if d >= 3 else pin
    return holes, pin


def dovetail(width: float, depth: float, thickness: float, profile: Printer | None = None,
             angle: float | None = None, fit: str = "clearance") -> tuple[bd.Part, bd.Part]:
    """Dovetail lying flat (profile in XY, thickness along Z, slides together along Z).

    The joint line is y = 0; the tail sticks out into +Y. Returns (tail, socket_cutter):
    union `tail` with the piece on the -Y side, subtract `socket_cutter` from the piece on the +Y side.
    Clearance is taken off the tail's flanks and tip; shoulders stay nominal.
    """
    p = _prof(profile)
    angle = angle if angle is not None else p.dovetail_angle_deg
    c = p.fit(fit)
    spread = depth * math.tan(math.radians(angle))
    socket = bd.Polygon((-width / 2, -0.01), (width / 2, -0.01), (width / 2 + spread, depth),
                        (-width / 2 - spread, depth), align=None)
    shift = c / math.cos(math.radians(angle))
    tip = depth - c
    tip_spread = tip * math.tan(math.radians(angle))
    tail = bd.Polygon((-width / 2 + shift, -0.5), (width / 2 - shift, -0.5), (width / 2 - shift + tip_spread, tip),
                      (-width / 2 + shift - tip_spread, tip), align=None)
    return (bd.extrude(tail, amount=thickness),
            bd.Pos(0, 0, -1) * bd.extrude(socket, amount=thickness + 2))


def snap_fit(length: float = 12.0, width: float = 5.0, thickness: float | None = None,
             undercut: float = 0.8, entry_angle: float = 35.0, exit_angle: float = 90.0,
             profile: Printer | None = None) -> bd.Part:
    """Cantilever clip lying flat: root at x = 0, arm along +X, hook on the +Y side, width along Z.

    Union it with a wall at x <= 0 and fillet the root. exit_angle 90 = permanent, 45-60 = removable.
    Mating catch gets snap_clearance_per_side.
    """
    p = _prof(profile)
    t_root = thickness or p.wall(1.6)
    t_tip = max(p.min_wall, round(0.6 * t_root, 3))
    run_in = undercut / math.tan(math.radians(entry_angle))
    run_out = 0.0 if exit_angle >= 89.9 else undercut / math.tan(math.radians(exit_angle))
    top = 0.4

    def arm_top(x):
        return t_root + (t_tip - t_root) * x / length

    x1 = length - run_in
    x0 = x1 - top
    x_back = x0 - run_out
    pts = [(0, 0), (length, 0), (length, arm_top(length)), (x1, arm_top(x1) + undercut),
           (x0, arm_top(x0) + undercut), (x_back, arm_top(x_back)), (0, t_root)]
    return bd.extrude(bd.Polygon(*pts, align=None), amount=width)
