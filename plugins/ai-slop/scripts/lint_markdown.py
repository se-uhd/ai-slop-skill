#!/usr/bin/env python3
"""lint_markdown.py [--fix] <path>

Lint a Markdown file against the dialect from ADR-0001 (GFM) and the
schema rules from ADR-0002. Stdlib only.

Rules
-----
Generic (every file):
  crlf-line-endings           CR or CRLF line endings.
  trailing-whitespace         line ends with whitespace.
  eof-newline                 file does not end with exactly one LF.
  multiple-blank-lines        more than two consecutive blank lines.
  unclosed-fence              a fenced code block has no matching closer.
  unclosed-frontmatter        a leading `---` has no matching `---`.
  heading-level-jump          heading level jumps by more than one.
  multiple-h1                 more than one H1 in the document.

Schema (triggered by H1 sniffing):
  finding-block-missing-label   `ai-slop-report.md`: a `#### Finding N`
                                block is missing one of the four labels
                                (`**Rule:**`, `**Location:**`, `**Quote:**`,
                                `**Suggested revision:**`).
  writing-md-structure          `WRITING.md`: not exactly one
                                `## AI Writing Tropes to Avoid` section,
                                or an H1 appears inside that section.

Auto-fix
--------
`--fix` rewrites the file in place applying:
  - line endings → LF;
  - trailing whitespace stripped;
  - exactly one trailing newline at EOF;
  - runs of three or more consecutive blank lines collapsed to two.

After the rewrite the linter re-checks the file and reports the remaining
findings on stdout. Rules that need authorial judgment
(unclosed-fence, unclosed-frontmatter, heading-level-jump, multiple-h1,
finding-block-missing-label, writing-md-structure) are reported, not
rewritten.

CLI
---
  python3 lint_markdown.py <path>
  python3 lint_markdown.py --fix <path>

Stdout: one finding per line as `<path>:<line>\\t<rule>\\t<message>`.
Stderr: one-line summary `checked <path>; <N> finding(s)`.

Exit codes
----------
  0  clean (no findings).
  1  one or more findings (after --fix, if used).
  2  could not read the input file.

Excluded by caller
------------------
`plugins/ai-slop/shared/tropes-snapshot.md` is vendored from upstream
(ADR-0001) and out of scope. Callers must not pass it as a positional
argument; the linter itself enforces no exclusion.
"""
import argparse
import re
import sys
from pathlib import Path

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


def fix_text(text):
    """Apply the four auto-fixable rules and return the rewritten text."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    # Collapse runs of 4+ consecutive newlines (3+ blank lines) to 3 newlines
    # (2 blank lines). A run of <=3 newlines is fine.
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    if text:
        text = text.rstrip('\n') + '\n'
    return text


def find_crlf(raw):
    """Yield (line_no, rule, message) for every CR or CRLF line ending."""
    line_no = 1
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == '\r':
            yield (line_no, 'crlf-line-endings', 'CR or CRLF line ending')
            if i + 1 < n and raw[i + 1] == '\n':
                i += 2
            else:
                i += 1
            line_no += 1
        elif ch == '\n':
            i += 1
            line_no += 1
        else:
            i += 1


def split_lines(text):
    """Split into lines, dropping the last empty entry if text ends with \\n."""
    if not text:
        return []
    if text.endswith('\n'):
        return text[:-1].split('\n')
    return text.split('\n')


def check_text(text):
    """Return findings as a sorted list of (line_no, rule, message)."""
    findings = []

    # crlf-line-endings (on raw text, before normalization).
    findings.extend(find_crlf(text))

    norm = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = split_lines(norm)

    # trailing-whitespace.
    for i, line in enumerate(lines, 1):
        if line != line.rstrip():
            findings.append((i, 'trailing-whitespace',
                             'line ends with whitespace'))

    # eof-newline.
    if norm:
        if not norm.endswith('\n'):
            findings.append((len(lines), 'eof-newline',
                             'no trailing newline at EOF'))
        elif norm.endswith('\n\n'):
            findings.append((len(lines) + 1, 'eof-newline',
                             'more than one trailing newline at EOF'))

    # multiple-blank-lines: flag the third blank line of any run.
    blank_run = 0
    for i, line in enumerate(lines, 1):
        if line.strip() == '':
            blank_run += 1
            if blank_run == 3:
                findings.append((i, 'multiple-blank-lines',
                                 'more than 2 consecutive blank lines'))
        else:
            blank_run = 0

    # State pass for fences, frontmatter, headings, finding blocks, and the
    # WRITING.md trope section.
    current_fence = None       # width of the open fence, or None
    fence_open_line = None
    in_frontmatter = False
    frontmatter_open_line = None
    if lines and lines[0].strip() == '---':
        in_frontmatter = True
        frontmatter_open_line = 1

    headings = []              # (line_no, level, body)
    is_report = False
    is_writing = False
    finding_blocks = []        # (header_line, [content_lines])
    current_finding = None
    in_trope_section = False
    h1_in_trope_section = []   # (line_no, body)

    for i, line in enumerate(lines, 1):
        # Frontmatter close.
        if in_frontmatter:
            if i > 1 and line.strip() == '---':
                in_frontmatter = False
            continue

        # Fence open/close.
        if current_fence is not None:
            m = FENCE_CLOSER_RE.match(line)
            if m and len(m.group(1)) >= current_fence:
                current_fence = None
                fence_open_line = None
            continue
        m = FENCE_OPENER_RE.match(line)
        if m:
            current_fence = len(m.group(1))
            fence_open_line = i
            continue

        # Headings (only outside fences and frontmatter).
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

            # Check section membership BEFORE updating section state, so a
            # spurious H1 inside the trope section is caught (the H1 itself
            # would otherwise close the section a step too early).
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

        # Body line inside an open finding block.
        if current_finding is not None:
            current_finding[1].append(line)

    if current_finding is not None:
        finding_blocks.append(current_finding)

    # unclosed-frontmatter.
    if in_frontmatter and frontmatter_open_line is not None:
        findings.append((frontmatter_open_line, 'unclosed-frontmatter',
                         'leading `---` has no matching close'))

    # unclosed-fence.
    if current_fence is not None and fence_open_line is not None:
        findings.append((fence_open_line, 'unclosed-fence',
                         f'{current_fence}-backtick fence opened with no '
                         'matching closer'))

    # heading-level-jump.
    prev_level = 0
    for ln, level, _body in headings:
        if prev_level > 0 and level > prev_level + 1:
            findings.append((ln, 'heading-level-jump',
                             f'heading level jumped from H{prev_level} '
                             f'to H{level}'))
        prev_level = level

    # multiple-h1.
    h1_seen = [(ln, b) for ln, lvl, b in headings if lvl == 1]
    for ln, _ in h1_seen[1:]:
        findings.append((ln, 'multiple-h1', 'more than one H1 in document'))

    # finding-block-missing-label.
    if is_report:
        for header_line, content in finding_blocks:
            content_text = '\n'.join(content)
            for label in FINDING_LABELS:
                if label not in content_text:
                    findings.append((header_line, 'finding-block-missing-label',
                                     f'Finding block is missing {label}'))

    # writing-md-structure.
    if is_writing:
        trope_h2 = [(ln, b) for ln, lvl, b in headings
                    if lvl == 2 and b == WRITING_TROPES_H2_BODY]
        if not trope_h2:
            findings.append((1, 'writing-md-structure',
                             'no `## AI Writing Tropes to Avoid` section'))
        elif len(trope_h2) > 1:
            for ln, _ in trope_h2[1:]:
                findings.append((ln, 'writing-md-structure',
                                 'duplicate `## AI Writing Tropes to Avoid` '
                                 'section'))
        for ln, _ in h1_in_trope_section:
            findings.append((ln, 'writing-md-structure',
                             'H1 inside `## AI Writing Tropes to Avoid` '
                             'section'))

    findings.sort()
    return findings


def main():
    parser = argparse.ArgumentParser(
        description=("Lint a Markdown file against the dialect from "
                     "ADR-0001 and the schemas from ADR-0002."),
    )
    parser.add_argument('path', help='Markdown file to check')
    parser.add_argument('--fix', action='store_true',
                        help='apply auto-fixable rules in place, then re-check')
    args = parser.parse_args()

    p = Path(args.path)
    try:
        # read_bytes + decode preserves CR / CRLF so the linter can flag them;
        # read_text would silently normalize via universal newlines mode.
        original = p.read_bytes().decode('utf-8')
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write(f"lint_markdown.py: cannot read {args.path}: {e}\n")
        sys.exit(2)

    if args.fix:
        fixed = fix_text(original)
        if fixed != original:
            p.write_text(fixed, encoding='utf-8')
        text_to_check = fixed
    else:
        text_to_check = original

    findings = check_text(text_to_check)

    for line_no, rule, message in findings:
        print(f"{args.path}:{line_no}\t{rule}\t{message}")

    sys.stderr.write(f"checked {args.path}; {len(findings)} finding(s)\n")
    sys.exit(0 if not findings else 1)


if __name__ == '__main__':
    main()
