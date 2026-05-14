#!/usr/bin/env python3
"""check_baseline.py [<path-to-lint_markdown.yaml>]

Verify that a skill's `lint_markdown.yaml` carries the baseline rules
shipped by pymarkdown-skill. The yaml itself is per-skill and may
include extra plugin tuning; this check only asserts the baseline is
present and matches.

Defaults to the `lint_markdown.yaml` next to this script.

Exit codes
----------
  0  baseline satisfied.
  1  one or more baseline mismatches.
  2  could not read or parse the yaml.
"""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
VENDOR_DIR = SCRIPTS_DIR / "_vendor"

if VENDOR_DIR.is_dir():
    sys.path.insert(0, str(VENDOR_DIR))

import yaml  # noqa: E402

REQUIRED_EXTENSIONS = (
    "front-matter",
    "markdown-tables",
    "markdown-task-list-items",
    "markdown-strikethrough",
    "markdown-extended-autolinks",
)
REQUIRED_DISABLED_PLUGINS = ("md013", "md033", "md041")


def check(yaml_path):
    try:
        body = yaml_path.read_text(encoding="utf-8")
    except OSError as e:
        sys.stderr.write(f"check_baseline.py: cannot read {yaml_path}: {e}\n")
        return 2
    try:
        doc = yaml.safe_load(body) or {}
    except yaml.YAMLError as e:
        sys.stderr.write(f"check_baseline.py: invalid yaml: {e}\n")
        return 2

    problems = []
    extensions = (doc.get("extensions") or {})
    for name in REQUIRED_EXTENSIONS:
        entry = extensions.get(name) or {}
        if not entry.get("enabled"):
            problems.append(f"extension `{name}` must be enabled")

    plugins = (doc.get("plugins") or {})
    for name in REQUIRED_DISABLED_PLUGINS:
        entry = plugins.get(name) or {}
        if entry.get("enabled", True) is not False:
            problems.append(f"plugin `{name}` must be disabled")

    for p in problems:
        sys.stderr.write(f"baseline mismatch: {p}\n")
    if problems:
        sys.stderr.write(
            f"{len(problems)} baseline mismatch(es) in {yaml_path}\n"
        )
        return 1
    sys.stderr.write(f"baseline ok: {yaml_path}\n")
    return 0


def main():
    if len(sys.argv) > 2:
        sys.stderr.write("usage: check_baseline.py [<lint_markdown.yaml>]\n")
        return 2
    target = (Path(sys.argv[1]) if len(sys.argv) == 2
              else SCRIPTS_DIR / "lint_markdown.yaml")
    return check(target)


if __name__ == "__main__":
    sys.exit(main())
