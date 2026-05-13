#!/usr/bin/env python3
"""refresh_vendor.py [--version VERSION]

Refresh the vendored PyMarkdown tree under `./_vendor/` (sibling of this
script) and regenerate `./_vendor/NOTICE`.

The script creates a temporary virtual environment, installs
`pymarkdownlnt` with `--no-binary :all:` so every dependency is built from
source (forcing pure-Python wheels where the package supports it), walks
the resolved package set, copies the top-level packages into `_vendor/`,
replaces the `pyjson5` C-extension with a stdlib shim (PyMarkdown is
always invoked with `--no-json5`), strips `__pycache__` directories,
verifies no compiled extensions landed in the tree, and writes a NOTICE
file collecting each package's license metadata.

Maintainer-only. End users invoke `lint_markdown.py`, which loads the
vendored tree from `_vendor/` directly and never shells out to pip.

CLI
---
  python3 refresh_vendor.py
  python3 refresh_vendor.py --version pymarkdownlnt==0.9.37

Exit codes
----------
  0  success.
  1  vendoring produced compiled extensions (aborts before overwriting).
  2  pip install failed.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PYJSON5_SHIM = '''"""Stdlib-backed pyjson5 shim used by the vendored PyMarkdown tree.

PyMarkdown's `application_properties` dependency imports pyjson5 at module
load time. The upstream pyjson5 ships as a C extension; vendoring it would
bake one platform's compiled artifact into the skill bundle. The
PyMarkdown CLI is always invoked with --no-json5, so the
`load_json_files_as_json5` code paths in application_properties never run.
This shim therefore only satisfies the imports and the exception symbols
those modules reference. Calling load/loads raises so misuse is loud.
"""


class Json5EOF(Exception):
    pass


class Json5DecoderException(Exception):
    pass


def _unavailable(*_args, **_kwargs):
    raise RuntimeError(
        "vendored pyjson5 shim: JSON5 support is not bundled; "
        "invoke pymarkdown with --no-json5"
    )


load = _unavailable
loads = _unavailable
dump = _unavailable
dumps = _unavailable
'''


# Top-level entries to skip when copying site-packages into _vendor/.
SKIP_ENTRIES = frozenset({
    "pip", "_distutils_hack", "pkg_resources", "setuptools",
    "wheel", "distutils-precedence.pth", "__pycache__",
})


def find_site_packages(venv_dir: Path) -> Path:
    """Return the venv's site-packages directory (versioned subpath)."""
    lib = venv_dir / "lib"
    for child in lib.iterdir():
        if child.name.startswith("python"):
            sp = child / "site-packages"
            if sp.is_dir():
                return sp
    raise RuntimeError(f"could not find site-packages under {lib}")


def strip_pycache(root: Path) -> None:
    """Remove all __pycache__ directories under root."""
    for dirpath, dirnames, _filenames in os.walk(root, topdown=False):
        for d in dirnames:
            if d == "__pycache__":
                shutil.rmtree(Path(dirpath) / d, ignore_errors=True)


def find_binary_extensions(root: Path) -> list[Path]:
    """Return any compiled extensions found under root."""
    binaries = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".so", ".pyd", ".dylib"}:
            binaries.append(path)
    return binaries


def install_pyjson5_shim(vendor_dir: Path) -> None:
    """Replace pyjson5/ in the vendored tree with the stdlib shim."""
    target = vendor_dir / "pyjson5"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    (target / "__init__.py").write_text(PYJSON5_SHIM, encoding="utf-8")


def collect_notice(site_packages: Path, vendor_dir: Path) -> str:
    """Build a NOTICE body from each vendored package's dist-info metadata."""
    vendored_names = {
        p.name for p in vendor_dir.iterdir()
        if p.is_dir() or (p.is_file() and p.suffix == ".py")
    }
    sections = [
        "Third-party software vendored in this directory.",
        "",
        "Each package below is included verbatim except `pyjson5`, which is",
        "replaced by a stdlib shim (see pyjson5/__init__.py). License texts",
        "are reproduced from the upstream `dist-info` metadata.",
        "",
    ]
    dist_info_dirs = sorted(
        d for d in site_packages.iterdir()
        if d.is_dir() and d.name.endswith(".dist-info")
    )
    for di in dist_info_dirs:
        metadata = di / "METADATA"
        if not metadata.is_file():
            continue
        name = ""
        version = ""
        license_field = ""
        for line in metadata.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Name: ") and not name:
                name = line[len("Name: "):].strip()
            elif line.startswith("Version: ") and not version:
                version = line[len("Version: "):].strip()
            elif line.startswith("License: ") and not license_field:
                license_field = line[len("License: "):].strip()
            elif line.startswith("License-Expression: ") and not license_field:
                license_field = line[len("License-Expression: "):].strip()
            if line == "":
                break
        # Match top-level package(s) the dist-info installs.
        top_level_path = di / "top_level.txt"
        top_levels = []
        if top_level_path.is_file():
            top_levels = [
                ln.strip() for ln in top_level_path.read_text(
                    encoding="utf-8").splitlines() if ln.strip()
            ]
        # Skip dist-infos whose top-level entries aren't in the vendored tree.
        if top_levels and not any(t in vendored_names for t in top_levels):
            continue
        sections.append(f"## {name} {version}")
        if license_field:
            sections.append(f"License: {license_field}")
        # Bundle the license file if present.
        license_text = None
        for candidate in ("LICENSE", "LICENSE.txt", "LICENSE.md", "LICENCE",
                          "COPYING"):
            cand = di / candidate
            if cand.is_file():
                license_text = cand.read_text(
                    encoding="utf-8", errors="replace").rstrip()
                break
        if license_text is None:
            licenses_dir = di / "licenses"
            if licenses_dir.is_dir():
                parts = []
                for f in sorted(licenses_dir.iterdir()):
                    if f.is_file():
                        parts.append(f"--- {f.name} ---")
                        parts.append(f.read_text(
                            encoding="utf-8", errors="replace").rstrip())
                if parts:
                    license_text = "\n".join(parts)
        if license_text:
            sections.append("")
            sections.append("```")
            sections.append(license_text)
            sections.append("```")
        sections.append("")
    return "\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=("Refresh the vendored PyMarkdown tree under "
                     "./_vendor/, alongside this script."),
    )
    parser.add_argument(
        "--version", default="pymarkdownlnt",
        help="package spec to install (default: pymarkdownlnt latest)",
    )
    args = parser.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    vendor_dir = scripts_dir / "_vendor"

    with tempfile.TemporaryDirectory(prefix="pymd-vendor-") as tmp:
        venv_dir = Path(tmp) / "venv"
        sys.stderr.write(f"creating venv at {venv_dir}\n")
        subprocess.check_call(
            [sys.executable, "-m", "venv", str(venv_dir)],
        )
        pip = venv_dir / "bin" / "pip"
        sys.stderr.write(f"installing {args.version} (--no-binary :all:)\n")
        try:
            subprocess.check_call(
                [str(pip), "install", "--quiet", "--no-binary", ":all:",
                 args.version],
            )
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"pip install failed: {e}\n")
            return 2

        site_packages = find_site_packages(venv_dir)
        sys.stderr.write(f"resolved site-packages: {site_packages}\n")

        # Stage the new tree in a sibling directory, swap atomically at the end.
        staging = scripts_dir / "_vendor.new"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()

        copied = []
        for entry in sorted(site_packages.iterdir()):
            if entry.name in SKIP_ENTRIES:
                continue
            if entry.name.endswith(".dist-info"):
                continue
            if entry.is_dir():
                shutil.copytree(entry, staging / entry.name)
                copied.append(entry.name)
            elif entry.is_file() and entry.suffix == ".py":
                shutil.copy2(entry, staging / entry.name)
                copied.append(entry.name)

        strip_pycache(staging)
        install_pyjson5_shim(staging)

        binaries = find_binary_extensions(staging)
        if binaries:
            sys.stderr.write(
                f"refusing to vendor compiled extensions ({len(binaries)} "
                f"found):\n",
            )
            for b in binaries:
                sys.stderr.write(f"  {b.relative_to(staging)}\n")
            shutil.rmtree(staging)
            return 1

        notice = collect_notice(site_packages, staging)
        (staging / "NOTICE").write_text(notice, encoding="utf-8")

        # Swap.
        if vendor_dir.exists():
            shutil.rmtree(vendor_dir)
        staging.rename(vendor_dir)

        sys.stderr.write(
            f"vendored {len(copied)} top-level package(s) into "
            f"{vendor_dir}\n",
        )
        for name in copied:
            sys.stderr.write(f"  {name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
