"""Designed-in break-away support fins."""

from __future__ import annotations

import build123d as bd

from .features import _prof
from .printer import Printer


def tine_levels(height: float, profile: Printer | None = None) -> list[float]:
    """Layer-aligned tine heights: dense near the base, sparser higher up."""
    p = _prof(profile)
    first, h = p.first_layer_height, p.layer_height
    layer_idx = [2, 4, 6, 8, 10, 13, 16]
    z = [first + (i - 1) * h for i in layer_idx]
    nxt = z[-1] + 5.0
    while nxt < height - 1.0:
        z.append(first + round((nxt - first) / h) * h)
        nxt += 5.0
    return [round(v, 4) for v in z if v < height - 0.5]


def support_fin(height: float, length: float = 8.0, profile: Printer | None = None,
                levels: list[float] | None = None, embed: float = 0.4, pad: bool = True) -> bd.Part:
    """A support fin for a part face at x = 0 (part on the +X side), standing on the bed at z = 0.

    The fin is a thin wall in the XZ plane, `support_gap_xy` off the face, `length` deep (along -X),
    `height` tall, with a rounded top. One-layer horizontal tines bridge the gap and reach `embed` into the part.
    Union the result with the part; give the part a ~2 mm bed chamfer; place fins on edges or corners.
    """
    p = _prof(profile)
    gap = max(p.support_gap_xy, p.min_open_gap)
    th = p.wall(1.0)
    x_far, x_near = -(gap + length), -gap
    wall = bd.Plane.XZ * bd.Rectangle(length, height, align=(bd.Align.MIN, bd.Align.MIN))
    wall = bd.extrude(wall, amount=th / 2, both=True)
    wall = bd.Pos(x_far, 0, 0) * wall
    top_edges = wall.edges().filter_by(bd.Axis.Y).group_by(bd.Axis.Z)[-1]
    wall = bd.fillet(top_edges, radius=min(length / 2 - 0.05, 3.0))
    fin = wall
    tine_w = 2 * p.line_width
    for z in levels or tine_levels(height, p):
        fin += bd.Pos(x_near - 0.5, -tine_w / 2, z) * bd.Box(gap + 0.5 + embed, tine_w, p.layer_height,
                                                            align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    if pad:
        pad_t = p.layers(1.0)
        foot = bd.Pos(x_far + length / 2, 0) * bd.Ellipse(length / 2 + 2, 3.0)
        keep_off = max(0.12, p.min_open_gap)  # pad stays clear of the part's first layer
        foot &= bd.Pos(-keep_off, 0) * bd.Rectangle(2 * length + 10, 10, align=(bd.Align.MAX, bd.Align.CENTER))
        fin += bd.extrude(foot, amount=pad_t)
    return fin
