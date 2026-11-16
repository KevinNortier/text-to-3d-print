"""Printable-feature helpers. Z is the print direction; cutters are returned as solids to subtract."""

from __future__ import annotations

import math

import build123d as bd

from .printer import Printer, load_printer


def _prof(profile: Printer | None) -> Printer:
    return profile if profile is not None else load_printer()


def _axis_plane(axis: str) -> bd.Plane:
    """Plane whose normal is the hole axis and whose local +Y is world +Z (up)."""
    planes = {"X": bd.Plane.YZ, "Y": bd.Plane.XZ}
    try:
        return planes[axis.upper()]
    except KeyError:
        raise ValueError("horizontal axis must be 'X' or 'Y'") from None


def teardrop_profile(d: float, angle: float = 45.0, flat_top: float | None = None) -> bd.Sketch:
    """2D teardrop in local XY with the point toward +Y. `angle` is the flank angle from vertical.
    `flat_top` cuts the point off at that height above the centre (e.g. d/2)."""
    r = d / 2
    a = math.radians(angle)
    apex = r / math.sin(a)
    tangent = (r * math.cos(a), r * math.sin(a))
    shape = bd.Circle(r) + bd.Polygon((0, 0), tangent, (0, apex), (-tangent[0], tangent[1]), align=None)
    if flat_top is not None and flat_top < apex:
        shape -= bd.Pos(0, flat_top + 2 * apex) * bd.Rectangle(4 * apex, 4 * apex)
    return shape


def teardrop_hole(d: float, length: float, axis: str = "X", profile: Printer | None = None,
                  angle: float | None = None, flat_top: bool = False) -> bd.Part:
    """Horizontal hole cutter of diameter `d` along `axis`, centred on the origin, pointed top up.
    Diameter is used as given (fits.hole adds oversize and fit)."""
    p = _prof(profile)
    angle = angle if angle is not None else min(p.max_overhang_deg, 60.0)
    sketch = _axis_plane(axis) * teardrop_profile(d, angle, d / 2 if flat_top else None)
    return bd.extrude(sketch, amount=length / 2, both=True)


def bottom_edges(part: bd.Part) -> bd.ShapeList:
    """Edges lying in the part's lowest plane (on the bed)."""
    return part.edges().group_by(bd.Axis.Z)[0]


def bed_chamfer(part: bd.Part, size: float | None = None, profile: Printer | None = None) -> bd.Part:
    """Chamfer every edge on the bed by `size` (default: elephant_foot_chamfer)."""
    size = size if size is not None else _prof(profile).elephant_foot_chamfer
    return bd.chamfer(bottom_edges(part), length=size)


def bed_fillet(part: bd.Part, radius: float | None = None, profile: Printer | None = None) -> bd.Part:
    """Fillet the edges on the bed, no larger than the printer's max_bed_fillet()."""
    p = _prof(profile)
    limit = p.max_bed_fillet()
    radius = min(radius if radius is not None else limit, limit)
    return bd.fillet(bottom_edges(part), radius=radius)


def max_bed_fillet(profile: Printer | None = None) -> float:
    return _prof(profile).max_bed_fillet()


def _footprint(cavity) -> bd.Sketch:
    if isinstance(cavity, (int, float)):
        return bd.Circle(cavity / 2)
    if isinstance(cavity, tuple) and len(cavity) == 2 and cavity[0] == "hex":
        return bd.RegularPolygon(cavity[1] / 2, 6, major_radius=False)
    if isinstance(cavity, tuple) and len(cavity) == 2:
        return bd.Rectangle(*cavity)
    if isinstance(cavity, bd.Sketch):
        return cavity
    raise ValueError("cavity: diameter, (w, l), ('hex', across_flats) or a Sketch")


def bridged_hole(hole_d: float, cavity, hole_depth: float, profile: Printer | None = None,
                 cavity_depth: float = 0.0, octagon: bool | None = None,
                 step_layers: int | None = None) -> bd.Part:
    """Hole-in-hole cutter: a hole of `hole_d` rising from the top of a larger cavity, printed without supports.

    z = 0 is the top of the cavity (where the bridges start); the hole goes up to z = hole_depth.
    cavity: its diameter, (w, l), ('hex', across_flats) or a centred Sketch. With cavity_depth > 0 the cavity
    itself is included below z = 0. Each step is `step_layers` layers of the profile's layer height:
    slot, square, optional octagon (default for holes >= 8 mm), then the round hole.
    """
    p = _prof(profile)
    t = (step_layers or p.bridge_step_layers) * p.layer_height
    octagon = hole_d >= 8 if octagon is None else octagon
    foot = _footprint(cavity)
    bb = foot.bounding_box()
    big = 2 * max(bb.size.X, bb.size.Y) + hole_d
    # bridges span the cavity's shorter direction, so the slot runs along it
    slot = bd.Rectangle(hole_d, big) if bb.size.X >= bb.size.Y else bd.Rectangle(big, hole_d)
    steps = [slot & foot, bd.Rectangle(hole_d, hole_d)]
    if octagon:
        steps.append(bd.Rot(0, 0, 22.5) * bd.RegularPolygon(hole_d / 2 / math.cos(math.pi / 8), 8))
    cutter = bd.Pos(0, 0, -0.01) * bd.Cylinder(hole_d / 2, hole_depth + 0.01, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    for i, s in enumerate(steps):
        cutter += bd.extrude(bd.Plane.XY.offset(i * t) * s, amount=t)
    if cavity_depth > 0:
        cutter += bd.extrude(bd.Plane.XY.offset(-cavity_depth) * foot, amount=cavity_depth)
    return cutter


def sacrificial_layer(cutter: bd.Part, z: float, profile: Printer | None = None,
                      layers: int | None = None) -> bd.Part:
    """Leave a membrane in a cutter: material stays from z to z + layers * layer_height.
    Tell the user to drill or cut it open after printing."""
    p = _prof(profile)
    t = (layers or p.sacrificial_layers) * p.layer_height
    bb = cutter.bounding_box()
    slab = bd.Pos(bb.center().X, bb.center().Y, z) * bd.Box(bb.size.X + 2, bb.size.Y + 2, t,
                                                           align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return cutter - slab


def label(text: str, height: float | None = None, depth: float = 0.8, profile: Printer | None = None,
          font: str = "Arial", bold: bool = True) -> bd.Part:
    """Text cutter centred on the origin, from z = 0 down by `depth`. Subtract it from a face at z = 0."""
    p = _prof(profile)
    height = height or p.min_text_height
    style = bd.FontStyle.BOLD if bold else bd.FontStyle.REGULAR
    sketch = bd.Text(text, font_size=height, font=font, font_style=style,
                     align=(bd.Align.CENTER, bd.Align.CENTER))
    return bd.extrude(sketch, amount=depth, dir=(0, 0, -1))


def raised_label(text: str, height: float | None = None, raise_by: float = 0.6,
                 profile: Printer | None = None, font: str = "Arial") -> bd.Part:
    """Raised text from z = 0 up by `raise_by` (for top faces)."""
    p = _prof(profile)
    sketch = bd.Text(text, font_size=height or p.min_text_height, font=font, font_style=bd.FontStyle.BOLD,
                     align=(bd.Align.CENTER, bd.Align.CENTER))
    return bd.extrude(sketch, amount=raise_by)


def bed_corners(part: bd.Part) -> list[tuple[float, float]]:
    """XY positions of the vertices on the bed (candidates for mouse ears)."""
    z = part.bounding_box().min.Z
    return [(v.X, v.Y) for v in part.vertices() if abs(v.Z - z) < 1e-6]


def mouse_ears(points, profile: Printer | None = None, diameter: float = 10.0, layers: int = 2) -> bd.Part:
    """Thin discs on the bed at `points` (e.g. bed_corners(part)), to union with the part. Snap off after printing."""
    p = _prof(profile)
    t = p.first_layer_height + (layers - 1) * p.layer_height
    ears = [bd.Pos(x, y, 0) * bd.Cylinder(diameter / 2, t, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
            for x, y in points]
    out = ears[0]
    for e in ears[1:]:
        out += e
    return out
