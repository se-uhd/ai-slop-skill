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
  2  could not read or parse the yaml, or the yaml has the wrong shape
     (the document or its extensions/plugins sections are not mappings).
"""
import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
VENDOR_DIR = SCRIPTS_DIR / "_vendor"

if VENDOR_DIR.is_dir():
    sys.path.insert(0, str(VENDOR_DIR))

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "check_baseline.py: PyYAML not importable; expected the vendored "
        f"copy under {VENDOR_DIR}\n"
    )
    sys.exit(2)

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
        doc = yaml.safe_load(body)
    except yaml.YAMLError as e:
        sys.stderr.write(f"check_baseline.py: invalid yaml: {e}\n")
        return 2
    if doc is None:
        doc = {}
    if not isinstance(doc, dict):
        # No `or {}` shortcuts here or below: they would coerce falsy
        # non-mappings ([], "", false) past the shape check.
        sys.stderr.write(
            f"check_baseline.py: top level of {yaml_path} must be a "
            f"mapping, not {type(doc).__name__}\n"
        )
        return 2

    sections = {}
    for key in ("extensions", "plugins"):
        section = doc.get(key)
        if section is None:
            section = {}
        if not isinstance(section, dict):
            sys.stderr.write(
                f"check_baseline.py: `{key}` must be a mapping, not "
                f"{type(section).__name__}\n"
            )
            return 2
        sections[key] = section

    def entry_for(section, name):
        entry = section.get(name) or {}
        return entry if isinstance(entry, dict) else {}

    problems = []
    for name in REQUIRED_EXTENSIONS:
        # PyMarkdown requires a real boolean here; a truthy non-boolean
        # such as the string "true" leaves the extension disabled.
        entry = entry_for(sections["extensions"], name)
        if entry.get("enabled") is not True:
            problems.append(
                f"extension `{name}` must be enabled (boolean true)"
            )

    for name in REQUIRED_DISABLED_PLUGINS:
        entry = entry_for(sections["plugins"], name)
        if entry.get("enabled", True) is not False:
            problems.append(
                f"plugin `{name}` must be disabled (boolean false)"
            )

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
    parser = argparse.ArgumentParser(
        description=("Verify that a skill's lint_markdown.yaml carries "
                     "the pymarkdown-skill baseline rules."),
    )
    parser.add_argument(
        "yaml_path", nargs="?", metavar="lint_markdown.yaml",
        help=("config to check (defaults to lint_markdown.yaml next to "
              "this script)"),
    )
    args = parser.parse_args()
    target = (Path(args.yaml_path) if args.yaml_path
              else SCRIPTS_DIR / "lint_markdown.yaml")
    return check(target)


if __name__ == "__main__":
    sys.exit(main())
