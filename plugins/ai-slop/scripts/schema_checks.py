"""schema_checks.py — ai-slop schema rules consumed by lint_markdown.py.

Two checks against `ai-slop-report.md` and `WRITING.md`:

  finding-block-missing-label   `ai-slop-report.md`: a `#### Finding N`
                                block is missing one of the four labels
                                (`**Rule:**`, `**Location:**`, `**Quote:**`,
                                `**Suggested revision:**`).
  writing-md-structure          `WRITING.md`: not exactly one
                                `## AI Writing Tropes to Avoid` section,
                                or an H1 appears inside that section.

The linter (`lint_markdown.py`, synced from pymarkdown-skill) loads this
file via importlib and calls `schema_findings(text, path)` at lint time.
"""
import re

SKILL_NAME = "ai-slop"

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


def schema_findings(text, path):
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
