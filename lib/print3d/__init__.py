"""Design-for-FDM helpers for build123d models (text-to-3d-print).

    from lib.print3d import load_printer, teardrop_hole, heatset_hole, ...
    p = load_printer()          # printer.toml from the project; defaults if none
    print(p.summary())

Every helper takes `profile=` (a Printer); without it, the project's profile is loaded.
Z is the print direction. Cutters are solids to subtract.
"""

__version__ = "0.1.0"

from .printer import Printer, find_profile, find_profiles, load_printer, material_family
from .features import (bed_chamfer, bed_corners, bed_fillet, bottom_edges, bridged_hole, label, max_bed_fillet,
                       mouse_ears, raised_label, sacrificial_layer, teardrop_hole, teardrop_profile)
from .fits import fit, hole, hole_diameter, relieved_pocket
from .hardware import (heatset_boss, heatset_hole, heatset_info, insert, inserts, magnet_pocket, nut_info,
                       nut_pause_z, nut_trap)
from .joints import alignment_pins, dovetail, pin_hole_diameter, snap_fit, split
from .supports import support_fin, tine_levels
from .testprint import (breakout, coupons, layout, tab_label, value_text, variants)
