"""Test prints: break out features of a model, make variants, label and lay them out; calibration coupons."""

from __future__ import annotations

import math

import build123d as bd

from .features import _prof, label, teardrop_hole
from .fits import relieved_pocket
from .hardware import heatset_info
from .joints import dovetail
from .printer import Printer

_BOTTOM = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


# --- model test prints ---------------------------------------------------------------------------

def breakout(shape: bd.Part, center, size, to_bed: bool = True) -> bd.Part:
    """The part of `shape` inside a box of `size` (x, y, z) at `center`, keeping its orientation.
    to_bed moves the piece so its lowest point is at z = 0."""
    piece = shape & (bd.Pos(*center) * bd.Box(*size))
    if to_bed:
        piece = bd.Pos(0, 0, -piece.bounding_box().min.Z) * piece
    return piece


def variants(make, values) -> list[tuple[object, bd.Part]]:
    """[(value, make(value)), ...] for a function that builds the feature from one parameter."""
    return [(v, make(v)) for v in values]


def value_text(v) -> str:
    """Short label for a value: 0.15 -> '15' (hundredths) below 1, else as is."""
    if isinstance(v, float) and abs(v) < 1:
        return f"{round(v * 100):d}"
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def tab_label(shape: bd.Part, text: str, profile: Printer | None = None, gap: float = 0.0) -> bd.Part:
    """Attach a thin tab with the text cut into it, on the bed at the -Y side of the shape."""
    p = _prof(profile)
    h = p.min_text_height
    bb = shape.bounding_box()
    t = p.layers(1.2)
    w = max(len(text) * 0.75 * h + 3, 8)
    tab = bd.Pos(bb.center().X, bb.min.Y - (h + 3) / 2 + 0.5 - gap, 0) * bd.Box(w, h + 3, t, align=_BOTTOM)
    tab -= bd.Pos(bb.center().X, bb.min.Y - (h + 3) / 2 + 0.5 - gap, t) * label(text, h, depth=t / 2, profile=p)
    return shape + tab


def layout(items, profile: Printer | None = None, gap: float = 5.0, row_width: float | None = None) -> bd.Compound:
    """Arrange shapes in rows on the bed (each moved to z = 0). Returns one Compound to export."""
    p = _prof(profile)
    if row_width is None:
        row_width = (p.build_volume[0] - 20) if p.build_volume else 180
    placed, x, y, row_h = [], 0.0, 0.0, 0.0
    for s in items:
        bb = s.bounding_box()
        if x > 0 and x + bb.size.X > row_width:
            x, y, row_h = 0.0, y + row_h + gap, 0.0
        placed.append(bd.Pos(x - bb.min.X, y - bb.min.Y, -bb.min.Z) * s)
        x += bb.size.X + gap
        row_h = max(row_h, bb.size.Y)
    return bd.Compound(children=placed)


# --- calibration coupons -------------------------------------------------------------------------

def _plate_with_holes(diams, labels, thickness, pitch, p) -> bd.Part:
    h = p.min_text_height
    w = pitch * len(diams) + 4
    plate = bd.Box(w, pitch + h + 4, thickness, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    for i, (d, txt) in enumerate(zip(diams, labels)):
        cx = 2 + pitch * (i + 0.5)
        plate -= bd.Pos(cx, h + 3 + pitch / 2, -1) * bd.Cylinder(d / 2, thickness + 2, align=_BOTTOM)
        plate -= bd.Pos(cx, (h + 3) / 2, thickness) * label(txt, h, 0.6, p)
    return plate


def fit_gauge(profile: Printer | None = None, d: float = 6.0, steps=None, thickness: float = 6.0) -> list[bd.Part]:
    """Printed pin + holes at d + 2*gap; label = gap per side in hundredths of a mm.
    Returns [hole plate, standing pin, lying pin]. Gives press / snug / clearance per side."""
    p = _prof(profile)
    steps = steps or [round(0.05 * i, 2) for i in range(0, 9)]
    plate = _plate_with_holes([d + 2 * s for s in steps], [value_text(s) for s in steps], thickness, d + 5, p)
    standing = bd.Cylinder(d / 2, 15, align=_BOTTOM)
    standing = bd.chamfer(standing.edges().group_by(bd.Axis.Z)[-1], length=0.4)
    lying = bd.Pos(0, 0, d / 2 - 0.15 * d) * (bd.Rot(0, 90, 0) * bd.Cylinder(d / 2, 15)
                                              - bd.Pos(0, 0, -d / 2) * bd.Box(17, d + 2, 0.3 * d))
    return [plate, standing, lying]


def hole_gauge(ref_d: float = 3.0, profile: Printer | None = None, steps=None, thickness: float = 5.0) -> bd.Part:
    """Vertical holes for a metal reference of diameter ref_d at ref_d + oversize; label = oversize in hundredths."""
    p = _prof(profile)
    steps = steps or [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    return _plate_with_holes([ref_d + s for s in steps], [value_text(s) for s in steps], thickness, ref_d + 5, p)


def heatset_coupon(spec: str = "M3", profile: Printer | None = None, steps=(0.0, 0.1, 0.2, 0.3)) -> bd.Part:
    """Insert holes at datasheet hole + step; label = step in tenths."""
    p = _prof(profile)
    info = heatset_info(spec, p)
    base_hole = info["hole"] - p.heatset_oversize
    pitch = info["boss_d"] + 4
    thickness = info["depth"] + 1.5
    return _plate_with_holes([base_hole + s for s in steps], [value_text(s) for s in steps], thickness, pitch, p)


def overhang_fan(profile: Printer | None = None, angles=range(30, 75, 5), height: float = 10.0,
                 width: float = 8.0) -> bd.Part:
    """A row of ledges overhanging at each angle (from vertical); label = angle."""
    p = _prof(profile)
    h = p.min_text_height
    parts = []
    x = 0.0
    for a in angles:
        reach = height * math.tan(math.radians(a))
        prof = bd.Polygon((0, 0), (2, 0), (2 + reach, height), (0, height), align=None)
        ledge = bd.Plane.XZ * prof
        ledge = bd.extrude(ledge, amount=-width)
        base = bd.Box(2 + reach, width + h + 3, 1.0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        base = bd.Pos(0, -(h + 3), 0) * base
        base -= bd.Pos((2 + reach) / 2, -(h + 3) / 2, 1.0) * label(str(a), h * 0.8, 0.5, p)
        parts.append(bd.Pos(x, 0, 0) * (ledge + base))
        x += 2 + reach + 3
    out = parts[0]
    for q in parts[1:]:
        out += q
    return out


def bridge_ladder(profile: Printer | None = None, spans=(5, 10, 15, 20, 25, 30, 40), height: float = 5.0,
                  width: float = 5.0) -> bd.Part:
    """Bridges of each span between two posts; label = span in mm."""
    p = _prof(profile)
    h = p.min_text_height
    out = None
    y = 0.0
    deck = p.layers(1.0)
    for s in spans:
        row = bd.Box(s + 6, width, 1.0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        row += bd.Box(3, width, height + deck, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        row += bd.Pos(s + 3, 0, 0) * bd.Box(3, width, height + deck, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        row += bd.Pos(0, 0, height) * bd.Box(s + 6, width, deck, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        tag = bd.Pos(s + 6, 0, 0) * bd.Box(h * 1.8 + 2, width, 1.0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        tag -= bd.Pos(s + 6 + (h * 1.8 + 2) / 2, width / 2, 1.0) * label(str(s), min(h, width - 1), 0.5, p)
        row = bd.Pos(0, y, 0) * (row + tag)
        out = row if out is None else out + row
        y += width + 2
    return out


def corner_relief_coupon(size: float = 10.0, profile: Printer | None = None, depth: float = 4.0) -> list[bd.Part]:
    """Square pockets with none / dog-bone / T-bone / slot reliefs, and a square peg to try in each."""
    p = _prof(profile)
    kinds = ["none", "dogbone", "tbone", "slot"]
    names = ["N", "D", "T", "S"]
    pitch = size + 8
    h = p.min_text_height
    plate = bd.Box(pitch * 4, pitch + h + 3, depth + 1.5, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    for i, (k, n) in enumerate(zip(kinds, names)):
        cx = pitch * (i + 0.5)
        plate -= bd.Pos(cx, h + 3 + pitch / 2, depth + 1.5) * relieved_pocket(size, size, depth + 0.01, k, p, fit="snug")
        plate -= bd.Pos(cx, (h + 3) / 2, depth + 1.5) * label(n, h, 0.6, p)
    peg = bd.Box(size, size, depth + 4, align=_BOTTOM)
    return [plate, peg]


def text_coupon(profile: Printer | None = None, heights=(2, 3, 4, 5, 6, 8), text: str = "Ab8") -> bd.Part:
    """Rows of cut and raised text at each height."""
    p = _prof(profile)
    rows, y = [], 0.0
    for hgt in heights:
        w = len(text) * hgt * 0.8 + 4
        plate = bd.Box(2 * w + 4, hgt + 3, 2.0, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
        plate -= bd.Pos(w / 2, (hgt + 3) / 2, 2.0) * label(text, hgt, 0.8, p)
        plate += bd.Pos(w + 4 + w / 2, (hgt + 3) / 2, 2.0) * bd.extrude(
            bd.Text(text, font_size=hgt, font_style=bd.FontStyle.BOLD), amount=0.6)
        rows.append(bd.Pos(0, y, 0) * plate)
        y += hgt + 4
    out = rows[0]
    for r in rows[1:]:
        out += r
    return out


def hole_in_hole_coupon(profile: Printer | None = None, holes=(3.4, 5.5, 8.5), cavity_factor: float = 1.9,
                        thickness: float = 6.0) -> bd.Part:
    """Counterbored holes printed face-down, with and without the octagon step. Label: hole size, o = octagon."""
    from .features import bridged_hole
    p = _prof(profile)
    h = p.min_text_height
    cells = [(d, octo) for d in holes for octo in (False, True)]
    pitch = max(holes) * cavity_factor + 6
    plate = bd.Box(pitch * len(cells), pitch + h + 3, thickness, align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    cav_depth = p.layers(thickness / 2)
    for i, (d, octo) in enumerate(cells):
        cx = pitch * (i + 0.5)
        cut = bridged_hole(d, d * cavity_factor, thickness - cav_depth + 1, p, cavity_depth=cav_depth + 1, octagon=octo)
        plate -= bd.Pos(cx, h + 3 + pitch / 2, cav_depth) * cut
        plate -= bd.Pos(cx, (h + 3) / 2, thickness) * label(f"{d:g}{'o' if octo else ''}", h * 0.8, 0.5, p)
    return plate


def dovetail_coupon(profile: Printer | None = None, angles=(10, 15, 20), width: float = 8.0, depth: float = 6.0,
                    thickness: float = 5.0) -> list[bd.Part]:
    """Male and female blocks for each dovetail angle (clearance fit). Label: angle."""
    p = _prof(profile)
    h = p.min_text_height
    males, females = [], []
    for a in angles:
        tail, socket = dovetail(width, depth, thickness, p, angle=a)
        block_w = width + 2 * depth * math.tan(math.radians(a)) + 8
        m = bd.Box(block_w, 10, thickness, align=(bd.Align.CENTER, bd.Align.MAX, bd.Align.MIN)) + tail
        m -= bd.Pos(0, -5, thickness) * label(str(a), h * 0.8, 0.5, p)
        f = bd.Box(block_w, depth + 6, thickness, align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN)) - socket
        males.append(m)
        females.append(f)
    return males + females


def coupons(profile: Printer | None = None, which=None, insert: str = "M3", ref_d: float = 3.0) -> dict[str, list]:
    """The calibration set by name: fit, hole, heatset, overhang, bridge, corner, text, hole_in_hole, dovetail."""
    p = _prof(profile)
    makers = {
        "fit": lambda: fit_gauge(p),
        "hole": lambda: [hole_gauge(ref_d, p)],
        "heatset": lambda: [heatset_coupon(insert, p)],
        "overhang": lambda: [overhang_fan(p)],
        "bridge": lambda: [bridge_ladder(p)],
        "corner": lambda: corner_relief_coupon(10.0, p),
        "text": lambda: [text_coupon(p)],
        "hole_in_hole": lambda: [hole_in_hole_coupon(p)],
        "dovetail": lambda: dovetail_coupon(p),
    }
    which = which or list(makers)
    return {k: makers[k]() for k in which}
