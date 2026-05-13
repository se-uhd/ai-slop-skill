#!/usr/bin/env python3
"""lint_markdown.py [--fix] <path>

Lint a Markdown file against the GFM dialect using the vendored PyMarkdown
tree under `_vendor/`, and apply the project-specific schema checks for
`ai-slop-report.md` and `WRITING.md`.

The vendored tree is refreshed by `refresh_vendor.py` (maintainer-only).
End users never need to install anything; the bundle is self-contained.

Dialect
-------
GitHub-Flavored Markdown via PyMarkdown's CommonMark base plus the
`markdown-tables`, `markdown-task-list-items`, `markdown-strikethrough`,
`markdown-extended-autolinks`, and `front-matter` extensions. Disabled
plugins (`md013` line-length, `md033` no-inline-html, `md041`
first-line-heading) are noisy or report-template-incompatible and add no
value to the prose this skill produces.

Pre-pass checks
---------------
PyMarkdown silently accepts these, so the wrapper runs a small pre-pass
on the raw bytes before pymarkdown is invoked:

  crlf-line-endings     CR or CRLF line ending anywhere in the file.
  unclosed-fence        a fenced code block has no matching closer.
  unclosed-frontmatter  a leading `---` has no matching `---`.

Schema checks
-------------
  finding-block-missing-label   `ai-slop-report.md`: a `#### Finding N`
                                block is missing one of the four labels
                                (`**Rule:**`, `**Location:**`, `**Quote:**`,
                                `**Suggested revision:**`).
  writing-md-structure          `WRITING.md`: not exactly one
                                `## AI Writing Tropes to Avoid` section,
                                or an H1 appears inside that section.

CLI
---
  python3 lint_markdown.py <path>
  python3 lint_markdown.py --fix <path>

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
import io
import re
import runpy
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
VENDOR_DIR = SCRIPTS_DIR / "_vendor"
CONFIG_FILE = SCRIPTS_DIR / "lint_markdown.yaml"

if not VENDOR_DIR.is_dir():
    sys.stderr.write(
        f"lint_markdown.py: vendored tree not found at {VENDOR_DIR}; "
        f"run refresh_vendor.py\n"
    )
    sys.exit(2)

sys.path.insert(0, str(VENDOR_DIR))

REPORT_H1_BODY = "AI Slop Review"
WRITING_H1_BODY = "Writing rules for this paper"
WRITING_TROPES_H2_BODY = "AI Writing Tropes to Avoid"
FINDING_LABELS = (
    "**Rule:**",
    "**Location:**",
    "**Quote:**",
    "**Suggested revision:**",
)

FINDING_HEADER_RE = re.compile(r'^####\s+Finding\s+\d+')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')
FENCE_OPENER_RE = re.compile(r'^(`{3,})')
FENCE_CLOSER_RE = re.compile(r'^(`{3,})\s*$')
PYMARKDOWN_LINE_RE = re.compile(
    r'^(?P<path>.+?):(?P<line>\d+):\d+:\s+(?P<rule>[A-Za-z0-9_]+):\s+'
    r'(?P<message>.+?)(?:\s+\((?P<aliases>[^)]+)\))?\s*$'
)


def pre_findings(raw_text):
    """Findings PyMarkdown silently accepts but the bundle should still flag.

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


def run_pymarkdown(subcommand, path):
    """Invoke the vendored PyMarkdown CLI; return (rc, stdout, stderr)."""
    argv = [
        "pymarkdown",
        "--no-json5",
        "--config", str(CONFIG_FILE),
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


def schema_findings(text):
    """Apply the ai-slop-report.md and WRITING.md schema checks."""
    findings = []
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines = lines[:-1]

    headings = []
    in_fence = None
    in_frontmatter = False
    if lines and lines[0].strip() == '---':
        in_frontmatter = True

    finding_blocks = []
    current_finding = None
    is_report = False
    is_writing = False
    in_trope_section = False
    h1_in_trope_section = []

    for i, line in enumerate(lines, 1):
        if in_frontmatter:
            if i > 1 and line.strip() == '---':
                in_frontmatter = False
            continue
        if in_fence is not None:
            m = FENCE_CLOSER_RE.match(line)
            if m and len(m.group(1)) >= in_fence:
                in_fence = None
            continue
        m = FENCE_OPENER_RE.match(line)
        if m:
            in_fence = len(m.group(1))
            continue

        hm = HEADING_RE.match(line)
        if hm:
            level = len(hm.group(1))
            body = hm.group(2).rstrip().rstrip('#').rstrip()
            headings.append((i, level, body))
            if level == 1 and not is_report and not is_writing:
                if body == REPORT_H1_BODY:
                    is_report = True
                elif body == WRITING_H1_BODY:
                    is_writing = True
            if in_trope_section and level == 1:
                h1_in_trope_section.append((i, body))
            if level == 2 and body == WRITING_TROPES_H2_BODY:
                in_trope_section = True
            elif level <= 2:
                in_trope_section = False
            if FINDING_HEADER_RE.match(line):
                if current_finding is not None:
                    finding_blocks.append(current_finding)
                current_finding = (i, [])
            else:
                if current_finding is not None:
                    finding_blocks.append(current_finding)
                    current_finding = None
            continue

        if current_finding is not None:
            current_finding[1].append(line)

    if current_finding is not None:
        finding_blocks.append(current_finding)

    if is_report:
        for header_line, content in finding_blocks:
            joined = '\n'.join(content)
            for label in FINDING_LABELS:
                if label not in joined:
                    findings.append((
                        header_line, 'finding-block-missing-label',
                        f'Finding block is missing {label}',
                    ))

    if is_writing:
        trope_h2 = [(ln, b) for ln, lvl, b in headings
                    if lvl == 2 and b == WRITING_TROPES_H2_BODY]
        if not trope_h2:
            findings.append((
                1, 'writing-md-structure',
                'no `## AI Writing Tropes to Avoid` section',
            ))
        elif len(trope_h2) > 1:
            for ln, _ in trope_h2[1:]:
                findings.append((
                    ln, 'writing-md-structure',
                    'duplicate `## AI Writing Tropes to Avoid` section',
                ))
        for ln, _ in h1_in_trope_section:
            findings.append((
                ln, 'writing-md-structure',
                'H1 inside `## AI Writing Tropes to Avoid` section',
            ))

    return findings


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
    parser = argparse.ArgumentParser(
        description=("Lint a Markdown file via the vendored PyMarkdown "
                     "tree plus the ai-slop schema checks."),
    )
    parser.add_argument('path', help='Markdown file to check')
    parser.add_argument('--fix', action='store_true',
                        help='apply auto-fixable rules in place, then re-check')
    args = parser.parse_args()

    p = Path(args.path)
    try:
        # read_bytes + decode preserves CR/CRLF so the pre-pass can flag them;
        # read_text would silently normalize via universal newlines mode.
        raw = p.read_bytes().decode('utf-8')
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"lint_markdown.py: cannot read {args.path}: {e}\n")
        sys.exit(2)

    if args.fix:
        rc_fix, _, _ = run_pymarkdown('fix', p)
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

    rc_scan, stdout, stderr = run_pymarkdown('scan', p)
    if rc_scan not in (0, 1):
        sys.stderr.write(
            f"lint_markdown.py: pymarkdown scan exited {rc_scan}\n{stderr}\n"
        )
        sys.exit(2)

    findings = pre_findings(raw)
    findings.extend(parse_pymarkdown_stdout(stdout))
    findings.extend(schema_findings(raw))
    findings.sort()

    for line_no, rule, message in findings:
        print(f"{args.path}:{line_no}\t{rule}\t{message}")

    sys.stderr.write(f"checked {args.path}; {len(findings)} finding(s)\n")
    sys.exit(0 if not findings else 1)


if __name__ == '__main__':
    main()
