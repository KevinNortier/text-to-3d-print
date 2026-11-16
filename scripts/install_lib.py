"""Copy the print3d helpers into a project, so its models can `from lib.print3d import ...`.

    cad run <plugin root>/scripts/install_lib.py [PROJECT_DIR] [--update]

Destination: <project>/src/lib/print3d when the project has a src/ folder, else <project>/lib/print3d.
An existing copy is left alone unless it's older than the plugin's and --update is given;
the old copy is then kept as print3d.bak-<version>.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "lib" / "print3d"


def version(pkg: Path) -> str | None:
    init = pkg / "__init__.py"
    if not init.exists():
        return None
    m = re.search(r'__version__\s*=\s*"([^"]+)"', init.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def as_tuple(v: str | None) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or "0"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--update", action="store_true", help="replace an older copy (keeps a backup)")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    lib = (project / "src" / "lib") if (project / "src").is_dir() else (project / "lib")
    dest = lib / "print3d"
    new = version(SOURCE)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")

    if dest.exists():
        old = version(dest)
        if as_tuple(old) >= as_tuple(new):
            print(f"up to date: {dest} (version {old})")
            return 0
        if not args.update:
            print(f"older copy: {dest} is version {old}, the plugin has {new}. Rerun with --update to replace it "
                  f"(a backup is kept).")
            return 3
        backup = dest.with_name(f"print3d.bak-{old}")
        if backup.exists():
            shutil.rmtree(backup)
        dest.rename(backup)
        shutil.copytree(SOURCE, dest, ignore=ignore)
        print(f"updated: {dest} {old} -> {new} (old copy in {backup.name}; delete it once the models build)")
        return 0

    lib.mkdir(parents=True, exist_ok=True)
    if not (lib / "__init__.py").exists():
        (lib / "__init__.py").write_text("", encoding="utf-8")
    shutil.copytree(SOURCE, dest, ignore=ignore)
    print(f"installed: {dest} (version {new}). Models in {lib.parent} import it as `from lib.print3d import ...`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
