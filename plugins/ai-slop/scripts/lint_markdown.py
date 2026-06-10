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
  unclosed-fence        a fenced code block (backtick or tilde, indented
                        up to 3 spaces) has no matching closer. Fences
                        nested inside lists or blockquotes are not
                        tracked.
  unclosed-frontmatter  a leading `---` frontmatter block is not closed
                        before the first blank line (or EOF); pymarkdown
                        abandons such a block and silently re-parses it
                        as body text. Emitted only when the config
                        enables the front-matter extension, and honors
                        its allow_blank_lines setting. A bare leading
                        thematic break (`---` followed directly by a
                        blank line) is not frontmatter and is not
                        flagged. Closed blocks are YAML-validated the
                        same way pymarkdown validates them; a block that
                        does not parse as YAML is treated as body text,
                        so fences inside it are tracked.

Note: pymarkdown 0.9.37 crashes (internal assertion) on files that open
with `---` but lack a final newline; the wrapper exits 2 on such files
and still prints the pre-pass and schema findings it detected.

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
  2  could not read the file or run the linter, including files
     pymarkdown refuses to scan (e.g. extension not recognized as
     Markdown) and pymarkdown-internal failures. Pre-pass and schema
     findings already detected are still printed to stdout.
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

import yaml  # noqa: E402  (vendored; resolvable only after the insert)

# CommonMark fence: backticks or tildes, indented at most 3 spaces.
FENCE_RE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
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


def frontmatter_settings(config_path):
    """Read the front-matter extension settings from the pymarkdown config.

    Returns (enabled, allow_blank_lines). Mirrors pymarkdown's strict
    booleans — a truthy non-boolean leaves the setting at its default —
    and its defaults (the extension is disabled unless enabled
    explicitly). An unparseable config yields (False, False), which only
    suppresses the frontmatter pre-pass, never adds findings.
    """
    try:
        doc = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError):
        return False, False
    if not isinstance(doc, dict):
        return False, False
    extensions = doc.get('extensions')
    if not isinstance(extensions, dict):
        return False, False
    entry = extensions.get('front-matter')
    if not isinstance(entry, dict):
        return False, False
    return (entry.get('enabled') is True,
            entry.get('allow_blank_lines') is True)


def frontmatter_yaml_valid(content_lines):
    """Mirror pymarkdown's front-matter YAML validation: the block counts
    as frontmatter only if it loads as non-None, non-string YAML;
    otherwise pymarkdown requeues the whole block as body text."""
    try:
        loaded = yaml.safe_load('\n'.join(content_lines))
    except yaml.YAMLError:
        return False
    return loaded is not None and not isinstance(loaded, str)


def pre_findings(raw_text, fm_enabled=False, fm_allow_blanks=False):
    """Findings PyMarkdown silently accepts but the linter should still flag.

    Runs on the raw text (with CR/CRLF preserved) before pymarkdown is
    invoked. Reports CRLF / lone CR once per file, an unclosed fenced code
    block, and — when the front-matter extension is enabled — an
    abandoned YAML frontmatter block.
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

    # Frontmatter first: pymarkdown's front-matter extension opens on a
    # first line of exactly `---` (no leading whitespace) and closes on the
    # next `---` line, but abandons the block at the first blank line
    # (unless allow_blank_lines) or at EOF — silently re-parsing
    # everything as body text. Flag abandonment only when the block had
    # content; a bare `---` followed by a blank line is a thematic break,
    # not frontmatter. A structurally closed block must also parse as
    # YAML, or pymarkdown likewise demotes it to body text.
    fence_scan_start = 0
    if fm_enabled and lines and lines[0].rstrip() == '---':
        content_seen = False
        closed_at = None
        for idx in range(1, len(lines)):
            if lines[idx].rstrip() == '---':
                closed_at = idx
                break
            if not lines[idx].strip():
                if not fm_allow_blanks:
                    break
                continue
            content_seen = True
        if closed_at is not None:
            if frontmatter_yaml_valid(lines[1:closed_at]):
                # Valid frontmatter; keep the fence scan out of the YAML.
                fence_scan_start = closed_at + 1
        elif content_seen:
            findings.append((
                1, 'unclosed-frontmatter',
                'leading `---` has no matching close before '
                + ('EOF' if fm_allow_blanks else 'a blank line')
                + '; pymarkdown silently treats the block as body text',
            ))

    fence_char = None
    fence_width = 0
    fence_open_line = None
    for idx in range(fence_scan_start, len(lines)):
        m = FENCE_RE.match(lines[idx])
        if not m:
            continue
        marker, rest = m.group(1), m.group(2)
        if fence_char is not None:
            # Inside an open fence only a closer counts: same character,
            # at least the opener's length, nothing but whitespace after.
            if (marker[0] == fence_char and len(marker) >= fence_width
                    and not rest.strip()):
                fence_char = None
                fence_open_line = None
            continue
        if marker[0] == '`' and '`' in rest:
            # A backtick run whose info string contains a backtick is
            # inline code, not a fence opener (CommonMark).
            continue
        fence_char = marker[0]
        fence_width = len(marker)
        fence_open_line = idx + 1
    if fence_char is not None:
        kind = 'backtick' if fence_char == '`' else 'tilde'
        findings.append((
            fence_open_line, 'unclosed-fence',
            f'{fence_width}-{kind} fence opened with no matching closer',
        ))

    return findings


def run_pymarkdown(subcommand, path, config):
    """Invoke the vendored PyMarkdown CLI; return (rc, stdout, stderr).

    Uses the `explicit` return-code scheme, the only one in which every
    outcome is distinguishable: 0 success, 1 no files to scan, 2 command
    line error, 3 fixed at least one file, 4 scan triggered at least
    once, 5 system error (see _vendor/pymarkdown/return_code_helper.py).
    """
    argv = [
        "pymarkdown",
        "--no-json5",
        "--config", str(config),
        "--return-code-scheme", "explicit",
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
                if exc.code is None:
                    rc = 0
                elif isinstance(exc.code, int):
                    rc = exc.code
                else:
                    # sys.exit("message") convention: message, exit 1.
                    err_buf.write(f"{exc.code}\n")
                    rc = 1
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
        # Under the explicit scheme 0 means nothing to fix and 3 means at
        # least one file was fixed; anything else is worth a warning (the
        # scan below surfaces terminal conditions with a hard error).
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

    fm_enabled, fm_allow_blanks = frontmatter_settings(config)
    findings = pre_findings(raw, fm_enabled, fm_allow_blanks)
    if schema_findings is not None:
        findings.extend(schema_findings(raw, p))

    def emit(found):
        for line_no, rule, message in sorted(found):
            print(f"{args.path}:{line_no}\t{rule}\t{message}")

    rc_scan, stdout, stderr = run_pymarkdown('scan', p, config)
    if rc_scan == 1:
        # NO_FILES_TO_SCAN: pymarkdown declined the path (typically a
        # non-Markdown extension) and emits no diagnostic of its own, so
        # reporting "clean" here would be a lie.
        emit(findings)
        sys.stderr.write(
            f"lint_markdown.py: pymarkdown did not scan {args.path} "
            f"(not recognized as a Markdown file)\n"
        )
        sys.exit(2)
    if rc_scan not in (0, 4):
        # Print what the wrapper itself found before bailing; pymarkdown
        # crashing must not suppress the pre-pass/schema diagnoses.
        emit(findings)
        sys.stderr.write(
            f"lint_markdown.py: pymarkdown scan exited {rc_scan}\n{stderr}\n"
        )
        sys.exit(2)

    findings.extend(parse_pymarkdown_stdout(stdout))
    emit(findings)

    sys.stderr.write(f"checked {args.path}; {len(findings)} finding(s)\n")
    sys.exit(0 if not findings else 1)


if __name__ == '__main__':
    main()
