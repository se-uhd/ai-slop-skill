#!/usr/bin/env python3
"""lint_markdown.py [--fix] [--config PATH] <path>

Lint a Markdown file against the GFM dialect using the vendored PyMarkdown
tree under `_vendor/`. If a `schema_checks.py` module sits next to this
script, its `schema_findings(text, path)` function is invoked and its
findings are merged into the output.

The vendored tree is refreshed by `refresh_vendor.py` (maintainer-only).
End users never need to install anything; the bundle is self-contained.

Dialect
-------
GitHub-Flavored Markdown via PyMarkdown's CommonMark base plus the
`markdown-tables`, `markdown-task-list-items`, `markdown-strikethrough`,
`markdown-extended-autolinks`, and `front-matter` extensions. Disabled
plugins (`md013` line-length, `md033` no-inline-html, `md041`
first-line-heading) are noisy or report-template-incompatible and add no
value to the prose this linter targets.

Pre-pass checks
---------------
PyMarkdown silently accepts these, so the wrapper runs a small pre-pass
on the raw bytes before pymarkdown is invoked:

  crlf-line-endings     CR or CRLF line ending anywhere in the file.
  unclosed-fence        a fenced code block has no matching closer.
  unclosed-frontmatter  a leading `---` has no matching `---`.

Schema checks
-------------
If `schema_checks.py` is present in this script's directory, it is loaded
via importlib and its `schema_findings(text, path)` function is called
with the raw file body and a `pathlib.Path` for the file under lint.
The function returns a list of `(line_no, rule_id, message)` tuples.
The optional `SKILL_NAME` module attribute is shown in `--help` output.

CLI
---
  python3 lint_markdown.py <path>
  python3 lint_markdown.py --fix <path>
  python3 lint_markdown.py --config <yaml> <path>

Stdout: one finding per line, tab-separated `<path>:<line>\\t<rule>\\t<message>`.
Stderr: one-line summary `checked <path>; <N> finding(s)`.

Exit codes
----------
  0  clean.
  1  one or more findings (after --fix, if used).
  2  could not read or run the linter.
"""
import argparse
import contextlib
import importlib.util
import io
import re
import runpy
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
VENDOR_DIR = SCRIPTS_DIR / "_vendor"
DEFAULT_CONFIG_FILE = SCRIPTS_DIR / "lint_markdown.yaml"
SCHEMA_CHECKS_FILE = SCRIPTS_DIR / "schema_checks.py"

if not VENDOR_DIR.is_dir():
    sys.stderr.write(
        f"lint_markdown.py: vendored tree not found at {VENDOR_DIR}; "
        f"run refresh_vendor.py\n"
    )
    sys.exit(2)

sys.path.insert(0, str(VENDOR_DIR))

FENCE_OPENER_RE = re.compile(r'^(`{3,})')
FENCE_CLOSER_RE = re.compile(r'^(`{3,})\s*$')
PYMARKDOWN_LINE_RE = re.compile(
    r'^(?P<path>.+?):(?P<line>\d+):\d+:\s+(?P<rule>[A-Za-z0-9_]+):\s+'
    r'(?P<message>.+?)(?:\s+\((?P<aliases>[^)]+)\))?\s*$'
)


def load_schema_checks():
    """Load the sibling `schema_checks.py`. Return (skill_name, finder) or
    (None, None) if absent."""
    if not SCHEMA_CHECKS_FILE.is_file():
        return None, None
    spec = importlib.util.spec_from_file_location(
        "schema_checks", SCHEMA_CHECKS_FILE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    skill_name = getattr(module, "SKILL_NAME", None)
    finder = getattr(module, "schema_findings", None)
    return skill_name, finder


def pre_findings(raw_text):
    """Findings PyMarkdown silently accepts but the linter should still flag.

    Runs on the raw text (with CR/CRLF preserved) before pymarkdown is
    invoked. Reports CRLF / lone CR once per file, an unclosed fenced code
    block, and an unclosed YAML frontmatter block.
    """
    findings = []

    if '\r' in raw_text:
        line_no = 1
        for ch in raw_text:
            if ch == '\r':
                findings.append((
                    line_no, 'crlf-line-endings',
                    'CR or CRLF line ending; pymarkdown silently accepts this',
                ))
                break
            if ch == '\n':
                line_no += 1

    norm = raw_text.replace('\r\n', '\n').replace('\r', '\n')
    lines = norm.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]

    fence_width = None
    fence_open_line = None
    for ln, line in enumerate(lines, 1):
        if fence_width is not None:
            m = FENCE_CLOSER_RE.match(line)
            if m and len(m.group(1)) >= fence_width:
                fence_width = None
                fence_open_line = None
            continue
        m = FENCE_OPENER_RE.match(line)
        if m:
            fence_width = len(m.group(1))
            fence_open_line = ln
    if fence_width is not None:
        findings.append((
            fence_open_line, 'unclosed-fence',
            f'{fence_width}-backtick fence opened with no matching closer',
        ))

    if lines and lines[0].strip() == '---':
        closed = any(line.strip() == '---' for line in lines[1:])
        if not closed:
            findings.append((
                1, 'unclosed-frontmatter',
                'leading `---` has no matching close',
            ))

    return findings


def run_pymarkdown(subcommand, path, config):
    """Invoke the vendored PyMarkdown CLI; return (rc, stdout, stderr)."""
    argv = [
        "pymarkdown",
        "--no-json5",
        "--config", str(config),
        "--return-code-scheme", "minimal",
        subcommand, str(path),
    ]
    saved_argv = sys.argv
    sys.argv = argv
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    rc = 0
    try:
        with contextlib.redirect_stdout(out_buf), \
             contextlib.redirect_stderr(err_buf):
            try:
                runpy.run_module("pymarkdown", run_name="__main__",
                                 alter_sys=True)
            except SystemExit as exc:
                rc = int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = saved_argv
    return rc, out_buf.getvalue(), err_buf.getvalue()


def parse_pymarkdown_stdout(stdout):
    """Parse pymarkdown's `<path>:<line>:<col>: <rule>: <message>` lines."""
    findings = []
    for raw in stdout.splitlines():
        m = PYMARKDOWN_LINE_RE.match(raw.rstrip())
        if not m:
            continue
        findings.append((
            int(m.group('line')),
            m.group('rule').lower(),
            m.group('message').strip(),
        ))
    return findings


def main():
    skill_name, schema_findings = load_schema_checks()
    description = (
        f"Lint a Markdown file via the vendored PyMarkdown tree"
        f"{' plus the ' + skill_name + ' schema checks' if skill_name else ''}."
    )
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('path', help='Markdown file to check')
    parser.add_argument('--fix', action='store_true',
                        help='apply auto-fixable rules in place, then re-check')
    parser.add_argument('--config', metavar='PATH',
                        help=('PyMarkdown config (defaults to '
                              'lint_markdown.yaml next to this script)'))
    args = parser.parse_args()

    config = Path(args.config) if args.config else DEFAULT_CONFIG_FILE
    if not config.is_file():
        if args.config:
            sys.stderr.write(
                f"lint_markdown.py: --config path not found: {config}\n"
            )
        else:
            sys.stderr.write(
                f"lint_markdown.py: no PyMarkdown config at {config}\n"
                f"create a lint_markdown.yaml next to this script or "
                f"pass --config <path>\n"
            )
        sys.exit(2)

    p = Path(args.path)
    try:
        # read_bytes + decode preserves CR/CRLF so the pre-pass can flag them;
        # read_text would silently normalize via universal newlines mode.
        raw = p.read_bytes().decode('utf-8')
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"lint_markdown.py: cannot read {args.path}: {e}\n")
        sys.exit(2)

    if args.fix:
        rc_fix, _, _ = run_pymarkdown('fix', p, config)
        if rc_fix not in (0, 3):
            sys.stderr.write(
                f"lint_markdown.py: pymarkdown fix exited {rc_fix}\n"
            )
        try:
            raw = p.read_bytes().decode('utf-8')
        except (OSError, UnicodeDecodeError) as e:
            sys.stderr.write(
                f"lint_markdown.py: cannot reread {args.path}: {e}\n"
            )
            sys.exit(2)

    rc_scan, stdout, stderr = run_pymarkdown('scan', p, config)
    if rc_scan not in (0, 1):
        sys.stderr.write(
            f"lint_markdown.py: pymarkdown scan exited {rc_scan}\n{stderr}\n"
        )
        sys.exit(2)

    findings = pre_findings(raw)
    findings.extend(parse_pymarkdown_stdout(stdout))
    if schema_findings is not None:
        findings.extend(schema_findings(raw, p))
    findings.sort()

    for line_no, rule, message in findings:
        print(f"{args.path}:{line_no}\t{rule}\t{message}")

    sys.stderr.write(f"checked {args.path}; {len(findings)} finding(s)\n")
    sys.exit(0 if not findings else 1)


if __name__ == '__main__':
    main()
