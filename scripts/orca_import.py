"""Import OrcaSlicer presets into a printer.toml / printer-<name>.toml.

    cad run scripts/orca_import.py --list
    cad run scripts/orca_import.py --printer NAME --process NAME --filament NAME [--filament NAME ...] --out printer.toml

Names are preset names as OrcaSlicer shows them, or paths to preset .json files.
Only standard-library Python; no OrcaSlicer settings are changed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

KINDS = ("machine", "process", "filament")


def orca_dirs(extra: list[str]) -> list[Path]:
    home = Path.home()
    dirs = [Path(e) for e in extra]
    if os.environ.get("APPDATA"):
        dirs.append(Path(os.environ["APPDATA"]) / "OrcaSlicer")
    dirs += [home / "AppData" / "Roaming" / "OrcaSlicer",
             home / "Library" / "Application Support" / "OrcaSlicer",
             Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "OrcaSlicer"]
    for app_id in ("com.orcaslicer.OrcaSlicer", "io.github.softfever.OrcaSlicer"):
        dirs.append(home / ".var" / "app" / app_id / "config" / "OrcaSlicer")
    seen, out = set(), []
    for d in dirs:
        r = d.resolve() if d.exists() else None
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out


def resource_dirs() -> list[Path]:
    cands = [Path(os.environ.get("ProgramFiles") or r"C:\Program Files") / "OrcaSlicer" / "resources" / "profiles",
             Path("/Applications/OrcaSlicer.app/Contents/Resources/profiles"),
             Path("/usr/share/OrcaSlicer/profiles"), Path("/opt/OrcaSlicer/resources/profiles")]
    return [c for c in cands if c.is_dir()]


def read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def kind_of(path: Path, data: dict) -> str | None:
    if data.get("type") in KINDS:
        return data["type"]
    for part in reversed(path.parts[:-1]):
        if part in KINDS:
            return part
    return None


class Index:
    """All presets by (kind, name). User presets are listed; vendor presets resolve parents."""

    def __init__(self, extra: list[str]):
        self.found: dict[tuple[str, str], tuple[Path, dict]] = {}
        self.all: dict[tuple[str, str], list[tuple[Path, dict]]] = {}
        self.user: dict[str, list[str]] = {k: [] for k in KINDS}
        for base in orca_dirs(extra):
            for f in sorted((base / "user").glob("*/*/*.json")) if (base / "user").is_dir() else []:
                self._add(f, user=True)
        for base in orca_dirs(extra):
            for f in sorted((base / "system").rglob("*.json")) if (base / "system").is_dir() else []:
                self._add(f)
        for base in resource_dirs():
            for f in sorted(base.rglob("*.json")):
                self._add(f)

    def _add(self, path: Path, user: bool = False):
        data = read(path)
        if not data or not isinstance(data.get("name"), str):
            return
        kind = kind_of(path, data)
        if not kind:
            return
        key = (kind, data["name"])
        self.all.setdefault(key, []).append((path, data))
        if key in self.found:
            return
        self.found[key] = (path, data)
        if user and data["name"] not in self.user[kind]:
            self.user[kind].append(data["name"])

    def resolve(self, kind: str, ref: str) -> tuple[dict, list[str]]:
        """Merged preset (parent values first) and a list of unresolved parent names."""
        p = Path(ref)
        if p.suffix == ".json" and p.exists():
            path, data = p.resolve(), read(p) or {}
        elif (kind, ref) in self.found:
            path, data = self.found[(kind, ref)]
        else:
            raise SystemExit(f"No {kind} preset named {ref!r}. Use --list.")
        chain, missing, seen = [data], [], set()
        anchor = path
        while chain[-1].get("inherits") and chain[-1]["inherits"] not in seen:
            parent = chain[-1]["inherits"]
            seen.add(parent)
            hits = self.all.get((kind, parent))
            if not hits:
                missing.append(parent)
                break
            # same-named parents exist per vendor: take the one closest to the child's file
            anchor, pdata = max(hits, key=lambda h: shared_depth(h[0], anchor))
            chain.append(pdata)
        merged: dict = {}
        for d in reversed(chain):
            merged.update(d)
        return merged, missing


def shared_depth(a: Path, b: Path) -> int:
    n = 0
    for x, y in zip(a.parts, b.parts):
        if x.lower() != y.lower():
            break
        n += 1
    return n


def first(v):
    return v[0] if isinstance(v, list) and v else v


def num(v, nozzle: float | None = None):
    v = first(v)
    if v is None or v == "":
        return None
    s = str(v).strip()
    if s.endswith("%"):
        pct = float(s[:-1])
        return round(pct / 100 * nozzle, 4) if nozzle else pct
    try:
        return float(s)
    except ValueError:
        return None


def bed_size(area) -> list[float] | None:
    pts = []
    for p in area or []:
        m = re.match(r"\s*(-?[\d.]+)\s*x\s*(-?[\d.]+)", str(p))
        if m:
            pts.append((float(m.group(1)), float(m.group(2))))
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [round(max(xs) - min(xs), 1), round(max(ys) - min(ys), 1)]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def fmt(v) -> str:
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    return str(v)


COMMENTED = """
# Calibrated or adjusted values go in a material table; defaults apply when absent:
# max_overhang_deg = 45          # material-adjusted
# max_bridge_mm = 15             # PETG/ASA 10, TPU 5
# teardrop_min_dia = 5
# hole_oversize = 0.3            # on diameter
# press_fit_per_side = 0.0
# snug_fit_per_side = 0.1        # fits +0.05 for PETG, ABS, ASA, PC, PA
# clearance_per_side = 0.2
# glue_gap_per_side = 0.2
# nut_clearance_per_side = 0.15
# snap_clearance_per_side = 0.25
# pip_gap_xy = 0.3
# pip_gap_z = 0.4                # 2 layers
# heatset_oversize = 0.2         # on diameter, added to the insert's datasheet hole
# elephant_foot_chamfer = 0.4
# corner_relief_dia = 0.84       # 2 line widths
# corner_slot = [1.0, 0.1]
# support_gap_xy = 0.2
# support_gap_z = 0.2            # 1 layer
# sacrificial_layers = 1
# bridge_step_layers = 1
# dovetail_angle_deg = 15
# min_text_height = 4
"""


def build(args, idx: Index) -> tuple[str, list[str]]:
    notes = []
    machine, miss = idx.resolve("machine", args.printer)
    notes += [f"machine parent not found: {m}" for m in miss]
    process, miss = idx.resolve("process", args.process)
    notes += [f"process parent not found: {m}" for m in miss]

    nozzle = num(machine.get("nozzle_diameter"))
    lines = ["# Imported from OrcaSlicer presets:",
             f"#   printer: {machine.get('name', args.printer)}",
             f"#   process: {process.get('name', args.process)}", "", "[printer]"]
    name = machine.get("printer_model") or machine.get("name") or args.printer
    lines.append(f"name = {fmt(str(name))}")
    bed = bed_size(machine.get("printable_area"))
    height = num(machine.get("printable_height"))
    if bed and height:
        lines.append(f"build_volume = {fmt(bed + [height])}")
    else:
        notes.append("build volume not found")
    for key, val in (("nozzle", nozzle),
                     ("line_width", num(process.get("outer_wall_line_width"), nozzle)
                      or num(process.get("line_width"), nozzle)),
                     ("layer_height", num(process.get("layer_height"))),
                     ("first_layer_height", num(process.get("initial_layer_print_height"))),
                     ("min_layer_height", num(machine.get("min_layer_height"))),
                     ("max_layer_height", num(machine.get("max_layer_height")))):
        if val:
            lines.append(f"{key} = {fmt(val)}")

    lines += ["", "[slicer]"]
    for out_key, orca_key in (("xy_hole_compensation", "xy_hole_compensation"),
                              ("xy_contour_compensation", "xy_contour_compensation"),
                              ("elephant_foot_compensation", "elefant_foot_compensation"),
                              ("slice_closing_radius", "slice_closing_radius"),
                              ("wall_loops", "wall_loops")):
        val = num(process.get(orca_key))
        if val is not None:
            lines.append(f"{out_key} = {fmt(int(val) if out_key == 'wall_loops' else val)}")

    tables = []
    for ref in args.filament:
        fil, miss = idx.resolve("filament", ref)
        notes += [f"filament parent not found: {m} (used the values in {fil.get('name', ref)})" for m in miss]
        ftype = str(first(fil.get("filament_type")) or "PLA")
        vendor = str(first(fil.get("filament_vendor")) or "")
        table = slug(ftype if not vendor or vendor.lower() == "generic" else f"{ftype}-{vendor}")
        base, n = table, 2
        while table in tables:
            table, n = f"{base}-{n}", n + 1
        tables.append(table)
        lines += ["", f"# {fil.get('name', ref)}", f"[materials.{table}]", f"type = {fmt(ftype)}"]
        shrink = num(fil.get("filament_shrink"))
        if shrink is not None and abs(shrink - 100) > 1e-6:
            lines.append(f"shrinkage_pct = {fmt(round(100 - shrink, 3))}  # slicer already scales by this")
    if tables:
        lines[lines.index("[slicer]") - 1:lines.index("[slicer]") - 1] = []
        lines.insert(lines.index("[slicer]") - 1, "")
        lines += ["", "[material]", f"active = {fmt(tables[0])}"]
    lines.append(COMMENTED)
    return "\n".join(lines).replace("\n\n\n", "\n\n"), notes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--list", action="store_true", help="list the user's presets")
    ap.add_argument("--all", action="store_true", help="with --list, include vendor presets")
    ap.add_argument("--printer")
    ap.add_argument("--process")
    ap.add_argument("--filament", action="append", default=[])
    ap.add_argument("--orca-dir", action="append", default=[], help="another OrcaSlicer data folder")
    ap.add_argument("--out", help="printer.toml or printer-<name>.toml to write; omit to print")
    ap.add_argument("--force", action="store_true", help="overwrite an existing --out file")
    args = ap.parse_args()

    idx = Index(args.orca_dir)
    if args.list:
        for kind in KINDS:
            names = idx.user[kind] if not args.all else sorted({n for k, n in idx.found if k == kind})
            print(f"[{kind}]")
            for n in names:
                print(f"  {n}")
        if not any(idx.user.values()):
            print("No OrcaSlicer user presets found." + ("" if orca_dirs(args.orca_dir) else " OrcaSlicer data folder not found."))
        return 0
    if not (args.printer and args.process and args.filament):
        ap.error("give --printer, --process and at least one --filament, or --list")

    text, notes = build(args, idx)
    for n in notes:
        print(f"note: {n}", file=sys.stderr)
    if args.out:
        out = Path(args.out)
        if out.exists() and not args.force:
            print(f"{out} exists; not overwritten (use --force after confirming with the user).", file=sys.stderr)
            print(text)
            return 2
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
