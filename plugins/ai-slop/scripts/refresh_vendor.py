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
  1  vendoring produced compiled extensions, or one or more vendored
     packages had no license text in their dist-info and no entry
     under `bundled_licenses/` (aborts before overwriting `_vendor/`).
  2  venv creation, pip install, or site-packages resolution failed.
"""
import argparse
import email.parser
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

# Distribution-name (case-insensitive) -> SPDX-style label overrides.
# Used when a wheel's METADATA declares a license that disagrees with the
# bundled LICENSE text, or when METADATA omits the License: field but the
# upstream project has a known license. Examples:
#   - sly 0.5: METADATA classifies as MIT but the shipped LICENSE is a
#     3-clause BSD-style notice with a non-endorsement clause.
#   - Columnar 1.4.1: METADATA's License: field is absent; classifiers
#     and the upstream LICENSE.txt confirm MIT.
LICENSE_LABEL_OVERRIDES = {
    "sly": "BSD-3-Clause",
    "columnar": "MIT",
}


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
    """Return any compiled artifacts found under root.

    Even a POSIX-host build can pick up `.pyd`/`.dll` files: a sdist may
    ship them as package data, in which case pip copies them verbatim
    into site-packages regardless of platform.
    """
    binaries = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {
            ".so", ".pyd", ".dylib", ".dll",
        }:
            binaries.append(path)
    return binaries


def install_pyjson5_shim(vendor_dir: Path) -> None:
    """Replace pyjson5/ in the vendored tree with the stdlib shim."""
    target = vendor_dir / "pyjson5"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    (target / "__init__.py").write_text(PYJSON5_SHIM, encoding="utf-8")


def collect_notice(
    site_packages: Path, vendor_dir: Path, bundled_dir: Path,
) -> tuple[str, list[str]]:
    """Build a NOTICE body from each vendored package's dist-info metadata.

    Returns (body, missing) where `missing` is the list of "name version"
    entries for which no license text could be located — neither in the
    package's dist-info nor in `bundled_dir`. The caller is expected to
    abort if `missing` is non-empty so the bundle is never published
    without attribution.
    """
    # Stems, not file names: top_level.txt entries are bare module names,
    # so a single-module dist like typing_extensions must be recorded as
    # "typing_extensions", not "typing_extensions.py".
    vendored_names = {
        p.stem if p.is_file() else p.name
        for p in vendor_dir.iterdir()
        if p.is_dir() or (p.is_file() and p.suffix == ".py")
    }
    sections = [
        "Third-party software vendored in this directory.",
        "",
        "Each package below is included verbatim except `pyjson5`, which is",
        "replaced by a stdlib shim (see pyjson5/__init__.py). License texts",
        "are reproduced from the upstream `dist-info` metadata, or from",
        "`bundled_licenses/` when the upstream wheel does not ship a",
        "LICENSE file.",
        "",
    ]
    missing: list[str] = []
    dist_info_dirs = sorted(
        d for d in site_packages.iterdir()
        if d.is_dir() and d.name.endswith(".dist-info")
    )
    for di in dist_info_dirs:
        metadata = di / "METADATA"
        if not metadata.is_file():
            continue
        # METADATA is RFC 822; email.parser handles folded multiline
        # values that naive line-prefix matching would truncate.
        msg = email.parser.Parser().parsestr(
            metadata.read_text(encoding="utf-8", errors="replace"),
            headersonly=True,
        )
        name = (msg.get("Name") or "").strip()
        version = (msg.get("Version") or "").strip()
        # License-Expression (PEP 639) is canonical; the deprecated
        # free-text License field is the fallback, whichever order the
        # wheel's build backend emitted them in.
        license_field = " ".join(
            (msg.get("License-Expression") or msg.get("License") or "")
            .split()
        )
        # Match top-level package(s) the dist-info installs.
        top_level_path = di / "top_level.txt"
        top_levels = []
        if top_level_path.is_file():
            top_levels = [
                ln.strip() for ln in top_level_path.read_text(
                    encoding="utf-8").splitlines() if ln.strip()
            ]
        # Skip dist-infos whose top-level entries aren't in the vendored
        # tree. Dist-infos without top_level.txt are kept: dropping them
        # on a name guess could lose attribution for packages whose
        # module name differs from the dist name (PyYAML installs
        # `yaml`), and over-attribution is harmless.
        if top_levels and not any(t in vendored_names for t in top_levels):
            continue
        override = LICENSE_LABEL_OVERRIDES.get(name.lower())
        if override:
            license_field = override
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
        if license_text is None and bundled_dir.is_dir():
            # Maintainer-supplied text for packages whose wheel does not
            # ship a LICENSE file in its dist-info (e.g. Columnar 1.4.1).
            for candidate in (f"{name}.txt", f"{name.lower()}.txt"):
                entry = bundled_dir / candidate
                if entry.is_file():
                    body = entry.read_text(
                        encoding="utf-8", errors="replace").rstrip()
                    # Match the `--- filename ---` style used by the
                    # licenses/-subdir branch so dist-info and
                    # bundled_licenses entries render consistently.
                    license_text = f"--- {candidate} ---\n{body}"
                    break
        if license_text:
            sections.append("")
            sections.append("```")
            sections.append(license_text)
            sections.append("```")
        else:
            missing.append(f"{name} {version}")
        # Apache-2.0 §4(d) requires reproducing any upstream NOTICE file.
        # We do this unconditionally — it's a no-op for packages that don't
        # ship one — so future Apache-licensed additions don't silently
        # miss the obligation.
        for candidate in ("NOTICE", "NOTICE.txt", "NOTICE.md"):
            nf = di / candidate
            if nf.is_file():
                notice_text = nf.read_text(
                    encoding="utf-8", errors="replace").rstrip()
                if notice_text:
                    sections.append("")
                    sections.append(f"NOTICE ({candidate}):")
                    sections.append("")
                    sections.append("```")
                    sections.append(notice_text)
                    sections.append("```")
                break
        sections.append("")
    return "\n".join(sections) + "\n", missing


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
        try:
            subprocess.check_call(
                [sys.executable, "-m", "venv", str(venv_dir)],
            )
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"venv creation failed: {e}\n")
            return 2
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

        try:
            site_packages = find_site_packages(venv_dir)
        except RuntimeError as e:
            sys.stderr.write(f"{e}\n")
            return 2
        sys.stderr.write(f"resolved site-packages: {site_packages}\n")

        # Stage the new tree in a sibling directory; swap at the end.
        staging = scripts_dir / "_vendor.new"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir()

        try:
            return _populate_and_swap(site_packages, scripts_dir, staging)
        except BaseException:
            # Unexpected failure (or Ctrl-C): don't leave a half-built
            # _vendor.new in the repo. The handled failure paths inside
            # remove it themselves before returning. If _vendor/ itself
            # is missing we crashed mid-swap and staging may hold the
            # only complete new tree, so leave everything for recovery.
            if (scripts_dir / "_vendor").exists():
                shutil.rmtree(staging, ignore_errors=True)
            raise


def _populate_and_swap(site_packages, scripts_dir, staging) -> int:
    """Copy site-packages into staging, validate, and swap into _vendor/."""
    vendor_dir = scripts_dir / "_vendor"
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

    bundled_dir = scripts_dir / "bundled_licenses"
    notice, missing = collect_notice(site_packages, staging, bundled_dir)
    if missing:
        sys.stderr.write(
            "refusing to vendor: no license text found for "
            f"{len(missing)} package(s):\n"
        )
        for entry in missing:
            sys.stderr.write(f"  {entry}\n")
        sys.stderr.write(
            f"add the missing LICENSE text under {bundled_dir} "
            f"(one <package-name>.txt per package) and re-run.\n"
        )
        shutil.rmtree(staging)
        return 1
    (staging / "NOTICE").write_text(notice, encoding="utf-8")

    # Swap via two renames so the old tree is never deleted before the
    # new one is in place; a crash in the window between them leaves
    # both trees on disk (_vendor.old and _vendor.new), recoverable by
    # renaming either back.
    old_dir = scripts_dir / "_vendor.old"
    if old_dir.exists():
        shutil.rmtree(old_dir)
    if vendor_dir.exists():
        vendor_dir.rename(old_dir)
    staging.rename(vendor_dir)
    if old_dir.exists():
        shutil.rmtree(old_dir)

    sys.stderr.write(
        f"vendored {len(copied)} top-level package(s) into "
        f"{vendor_dir}\n",
    )
    for name in copied:
        sys.stderr.write(f"  {name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
