"""Find and load printer.toml / printer-<name>.toml, with defaults and material adjustments.

In a text-to-cad model script, find the file at module level and load it inside the body
(the server tracks files a body reads, but not folder searches):

    from lib.print3d import find_profile, load_printer
    PROFILE = find_profile(root=__file__)      # module level: a Path or None
    ...
    p = load_printer(path=PROFILE)             # inside the body; pass profile=p to every helper

    p.clearance_per_side            # effective value
    p.clearance_per_side            # effective value
    p.source("clearance_per_side")  # "calibrated", "profile", "material default" or "default"
    print(p.summary())
"""

from __future__ import annotations

import math
import re
import tomllib
from pathlib import Path

DATA = Path(__file__).parent / "data"

PRINTER_KEYS = ("name", "build_volume", "nozzle", "line_width", "layer_height",
                "first_layer_height", "min_layer_height", "max_layer_height")
FIT_KINDS = {
    "press": "press_fit_per_side",
    "snug": "snug_fit_per_side",
    "clearance": "clearance_per_side",
    "sliding": "clearance_per_side",
    "glue": "glue_gap_per_side",
    "nut": "nut_clearance_per_side",
    "snap": "snap_clearance_per_side",
}


def _read_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _defaults() -> dict:
    return _read_toml(DATA / "defaults.toml")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", text.lower()).strip("-")


def find_profiles(root: str | Path | None = None) -> list[Path]:
    """Printer files in the project root: the first folder from `root` (default: cwd; a file means its folder)
    upward that has any, stopping at a folder with .git."""
    folder = Path(root or Path.cwd()).resolve()
    if folder.is_file():
        folder = folder.parent
    for candidate in (folder, *folder.parents):
        found = sorted(candidate.glob("printer.toml")) + sorted(candidate.glob("printer-*.toml"))
        if found:
            return found
        if (candidate / ".git").exists():
            break
    return []


def find_profile(name: str | None = None, root: str | Path | None = None) -> Path | None:
    """Pick the profile: by name (slug or [printer].name) if given, else the only one.
    Raises LookupError when several exist and no name says which."""
    files = find_profiles(root)
    if not files:
        return None
    if name:
        want = _slug(name)
        for f in files:
            if f.stem == f"printer-{want}" or (f.stem == "printer" and want == "printer"):
                return f
        for f in files:
            pname = _read_toml(f).get("printer", {}).get("name", "")
            if pname and (_slug(pname) == want or want in _slug(pname)):
                return f
        raise LookupError(f"No printer profile matches {name!r}: {[f.name for f in files]}")
    if len(files) == 1:
        return files[0]
    raise LookupError(f"Several printer profiles, name one: {[f.name for f in files]}")


def material_family(mtype: str) -> tuple[str, list[str]]:
    """Map a filament type ('PETG', 'PLA-CF', 'PLA Silk', 'Wood PLA') to (base, extra adjustment keys)."""
    t = mtype.upper().replace("_", "-")
    extras = []
    for word, key in (("SILK", "SILK"), ("WOOD", "WOOD"), ("METAL", "METAL")):
        if word in t:
            return key, extras
    if re.search(r"[-\s+](CF|GF)\b|CARBON|GLASS", t):
        extras.append("FIBRE")
        t = re.split(r"[-\s+](CF|GF)\b|CARBON|GLASS", t)[0]
    for base in ("PETG", "PLA", "ABS", "ASA", "PC", "PA", "TPU", "NYLON"):
        if base in t:
            return ("PA" if base == "NYLON" else base), extras
    return "PLA", extras


class Printer:
    """Effective printer + material values. Attribute access gives the value; source() tells where it came from."""

    def __init__(self, path: Path | None, data: dict, material: str | None = None):
        self.path = path
        self._values: dict = {}
        self._sources: dict = {}
        self.warnings: list[str] = []
        self.unknown_material = False
        d = _defaults()

        printer = data.get("printer", {})
        mats = data.get("materials", {})
        active = material or data.get("material", {}).get("active")
        if active is None and len(mats) == 1:
            active = next(iter(mats))
        if active is not None and active not in mats:
            # allow picking by type ("PETG") as well as by table name
            by_type = [k for k, v in mats.items() if str(v.get("type", "")).upper() == active.upper()]
            if by_type:
                active = by_type[0]
            elif material:
                mats = {**mats, active: {"type": active}}
        mat = mats.get(active, {}) if active else {}
        self.material_name = active or "default"

        # printer level
        self._set("nozzle", printer.get("nozzle"), d["printer"]["nozzle"])
        self._set("line_width", printer.get("line_width"), round(self.nozzle * d["printer"]["line_width_factor"], 3))
        self._set("layer_height", printer.get("layer_height"), d["printer"]["layer_height"])
        self._set("first_layer_height", printer.get("first_layer_height"), self.layer_height)
        for key in ("name", "build_volume", "min_layer_height", "max_layer_height"):
            self._set(key, printer.get(key), None)

        # material defaults, then type adjustments, then derived multipliers
        base = dict(d["material"])
        mtype = mat.get("type") or base["type"]
        family, extras = material_family(mtype)
        adjusted: dict = {}
        for key in self._adjust_chain(d["adjust"], family) + extras:
            adj = d["adjust"].get(key, {})
            for k, v in adj.items():
                if k == "fit_offset":
                    for fk in d["adjust"]["fit_keys"]:
                        adjusted[fk] = round(adjusted.get(fk, base[fk]) + v, 3)
                elif k == "warning":
                    self.warnings.append(v)
                elif k != "base":
                    adjusted[k] = v
        if not mat.get("type"):
            self.unknown_material = active is None
        base.update(adjusted)
        base["type"] = mtype
        base["pip_gap_z"] = round(base.pop("pip_gap_z_layers") * self.layer_height, 3)
        base["support_gap_z"] = round(base.pop("support_gap_z_layers") * self.layer_height, 3)
        base["corner_relief_dia"] = round(base.pop("corner_relief_dia_lines") * self.line_width, 3)
        base.setdefault("shrinkage_pct", None)
        base.setdefault("warps", False)
        base.setdefault("flexible", False)

        calibrated = mat.get("calibrated", {})
        for key, default in base.items():
            src = "material default" if key in adjusted else "default"
            if key in mat:
                self._values[key] = mat[key]
                self._sources[key] = "calibrated" if key in calibrated else "profile"
            else:
                self._values[key] = default
                self._sources[key] = src
        for key, val in mat.items():  # unknown keys the user added
            if key not in self._values and key not in ("calibrated", "heatset"):
                self._values[key] = val
                self._sources[key] = "profile"
        self.heatset_overrides: dict = mat.get("heatset", {})
        self.calibrated: dict = calibrated

        # slicer compensation already applied by the slicer: don't double it
        self.slicer: dict = data.get("slicer", {})
        hole_comp = float(self.slicer.get("xy_hole_compensation", 0) or 0)
        if hole_comp:
            for key in ("hole_oversize", "heatset_oversize"):
                if self._sources[key] in ("default", "material default"):
                    self._values[key] = round(max(0.0, self._values[key] - 2 * hole_comp), 3)
                    self._sources[key] += " - slicer hole compensation"
        foot = float(self.slicer.get("elephant_foot_compensation", 0) or 0)
        if foot and self._sources["elephant_foot_chamfer"] in ("default", "material default"):
            self._values["elephant_foot_chamfer"] = round(max(0.0, self.elephant_foot_chamfer - foot), 3)
        closing = float(self.slicer.get("slice_closing_radius", 0.049) or 0.049)
        self.min_open_gap = round(2 * closing + 0.002, 3)

    @staticmethod
    def _adjust_chain(adjust: dict, family: str) -> list[str]:
        chain, key = [], family
        while key and key not in chain:
            chain.insert(0, key)
            key = adjust.get(key, {}).get("base")
        return chain

    def _set(self, key, value, default):
        if value is None:
            self._values[key], self._sources[key] = default, "default"
        else:
            self._values[key], self._sources[key] = value, "profile"

    def __getattr__(self, key):
        try:
            return self.__dict__["_values"][key]
        except KeyError:
            raise AttributeError(key) from None

    def get(self, key, default=None):
        return self._values.get(key, default)

    def source(self, key: str) -> str:
        return self._sources.get(key, "unknown")

    def values(self) -> dict:
        return dict(self._values)

    # derived values
    def fit(self, kind: str) -> float:
        """Per-side gap for a fit class: press, snug, clearance (sliding), glue, nut, snap."""
        return self._values[FIT_KINDS[kind]]

    @property
    def min_wall(self) -> float:
        return round(2 * self.line_width, 3)

    @property
    def rib(self) -> float:
        return round(3 * self.line_width, 3)

    def wall(self, at_least: float) -> float:
        """Smallest whole number of lines (>= 2) that is at least `at_least` thick."""
        lines = max(2, math.ceil(at_least / self.line_width - 1e-6))
        return round(lines * self.line_width, 3)

    def layers(self, height: float) -> float:
        """Round a height up to a whole number of layers above the first layer."""
        first, h = self.first_layer_height, self.layer_height
        if height <= first:
            return first
        return round(first + math.ceil((height - first) / h - 1e-6) * h, 4)

    def max_bed_fillet(self) -> float:
        """Largest fillet on a bed edge whose second layer overhangs the first by at most one line width."""
        h, w = self.layer_height, self.line_width
        z1, z2 = self.first_layer_height / 2, self.first_layer_height + h / 2

        def inset(r, z):
            return r - math.sqrt(max(0.0, r * r - (r - z) ** 2)) if z < r else r

        r = 0.1
        while r < 20 and inset(r, z1) - inset(r, z2) <= w:
            r += 0.05
        return round(r - 0.05, 2)

    def fits_on_bed(self, size_xyz) -> bool | None:
        if not self.build_volume:
            return None
        bx = sorted(self.build_volume[:2])
        sx = sorted(size_xyz[:2])
        return sx[0] <= bx[0] - 5 and sx[1] <= bx[1] - 5 and size_xyz[2] <= self.build_volume[2]

    def summary(self) -> str:
        where = self.path.name if self.path else "no printer file (defaults: 0.4 mm nozzle, 0.2 mm layers, PLA)"
        lines = [f"Printer profile: {where}",
                 f"  printer: {self.name or 'unnamed'}, nozzle {self.nozzle}, line {self.line_width}, "
                 f"layer {self.layer_height}, bed {self.build_volume or 'unknown'}",
                 f"  material: {self.material_name} ({self.type})"]
        cal = [k for k in self._values if self._sources[k] == "calibrated"]
        lines.append(f"  calibrated: {', '.join(cal) if cal else 'nothing yet (uncalibrated defaults)'}")
        for w in self.warnings:
            lines.append(f"  warning: {w}")
        return "\n".join(lines)


def load_printer(name: str | None = None, *, path: str | Path | None = None,
                 material: str | None = None, root: str | Path | None = None) -> Printer:
    """Load the effective profile. No file → defaults (0.4 mm nozzle, 0.2 mm layers, PLA)."""
    p = Path(path) if path else find_profile(name, root)
    data = _read_toml(p) if p else {}
    return Printer(p, data, material)
