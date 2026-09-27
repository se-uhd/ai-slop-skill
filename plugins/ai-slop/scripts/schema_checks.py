"""schema_checks.py: ai-slop schema rules consumed by lint_markdown.py.

The checks against `ai-slop-report.md`, `ai-slop-tldr.md`, and `WRITING.md`:

  finding-block-missing-label   `ai-slop-report.md`: a `#### Finding N`
                                block is missing one of the four labels
                                (`**Rule:**`, `**Location:**`, `**Quote:**`,
                                `**Suggested revision:**`).
  writing-md-structure          `WRITING.md`: not exactly one
                                `## AI Writing Tropes to Avoid` section,
                                or an H1 appears inside that section. A
                                WRITING.md is recognized by its H1, which
                                `/ai-slop:init` writes as "Writing rules for
                                this project" (older files say "paper").
  tldr-block-format             `ai-slop-tldr.md`: a per-file `##` block
                                has no `**Number of patterns that affect
                                readability:**` line with a number (and
                                the word count, as in `3 in 850 words`),
                                has an `**Impact on readability:**` or
                                an `**AI use:**` line (the TL;DR counts
                                patterns and does not rate the text or
                                say who or what wrote it), has text
                                besides the count line and the bullets,
                                has more than five bullets, or has
                                bullets without the `**Patterns that
                                affect readability:**` line before them. The
                                block that lists the files that need no
                                feedback is exempt.

The linter (`lint_markdown.py`, synced from pymarkdown-skill) loads this
file via importlib and calls `schema_findings(text, path)` at lint time.
"""
import re

SKILL_NAME = "ai-slop"

REPORT_H1_BODY = "AI Slop Review"
TLDR_H1_BODY = "AI Slop TL;DR"
TLDR_EXEMPT_H2_BODY = "Files that need no feedback"
TLDR_BULLETS_INTRO = "**Patterns that affect readability:**"
TLDR_MAX_BULLETS = 5
WRITING_H1_BODIES = ("Writing rules for this project", "Writing rules for this paper")
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
COUNT_RE = re.compile(r'^\*\*Number of patterns that affect readability:\*\*\s*(.*?)\s*$')
COUNT_VALUE_RE = re.compile(r'^\d+(?: in [\d,]+ words(?: [^.]*)?)?\.?$')
RETIRED_RE = re.compile(r'^\*\*(?:Impact on readability|AI use):\*\*')
BULLET_RE = re.compile(r'^[-*+]\s+')


def tldr_findings(lines):
    """Check the per-file blocks of an `ai-slop-tldr.md` (see the module
    docstring for the structure they must have)."""
    findings = []
    blocks = []  # (heading line, body, [(lineno, line), ...])
    in_fence = None
    for i, line in enumerate(lines, 1):
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
        if hm and len(hm.group(1)) <= 2:
            body = hm.group(2).rstrip().rstrip('#').rstrip()
            blocks.append((i, body, []) if len(hm.group(1)) == 2 else None)
            continue
        if blocks and blocks[-1] is not None:
            blocks[-1][2].append((i, line))
    for block in blocks:
        if block is None or block[1] == TLDR_EXEMPT_H2_BODY:
            continue
        head, _, body = block
        count = None
        retired = False
        intro = False
        prose = []
        bullets = 0
        in_bullet = False
        for _, line in body:
            cm = COUNT_RE.match(line)
            if cm and count is None:
                count = cm.group(1)
                in_bullet = False
            elif RETIRED_RE.match(line):
                retired = True
                in_bullet = False
            elif line.strip() == TLDR_BULLETS_INTRO:
                intro = True
                in_bullet = False
            elif BULLET_RE.match(line):
                if not bullets and not intro:
                    findings.append((head, 'tldr-block-format',
                                     f'TL;DR bullets without the {TLDR_BULLETS_INTRO} line'))
                bullets += 1
                in_bullet = True
            elif not line.strip():
                in_bullet = False
            elif in_bullet and line[:1].isspace():
                continue
            else:
                in_bullet = False
                prose.append(line.strip())
        if count is None:
            findings.append((head, 'tldr-block-format',
                             'TL;DR block has no **Number of patterns that affect '
                             'readability:** line'))
        elif not COUNT_VALUE_RE.match(count):
            findings.append((head, 'tldr-block-format',
                             f'TL;DR pattern count {count!r} is not a number, '
                             'optionally followed by "in <N> words"'))
        if retired:
            findings.append((head, 'tldr-block-format',
                             'TL;DR block has an **Impact on readability:** or '
                             '**AI use:** line, which the TL;DR leaves out'))
        if prose:
            findings.append((head, 'tldr-block-format',
                             'TL;DR block has text besides the count line and '
                             'the bullets'))
        if bullets > TLDR_MAX_BULLETS:
            findings.append((head, 'tldr-block-format',
                             f'TL;DR block has {bullets} bullets '
                             f'(at most {TLDR_MAX_BULLETS})'))
    return findings


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
    is_tldr = False
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
            if level == 1 and not (is_report or is_tldr or is_writing):
                if body == REPORT_H1_BODY:
                    is_report = True
                elif body == TLDR_H1_BODY:
                    is_tldr = True
                elif body in WRITING_H1_BODIES:
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

    if is_tldr:
        findings.extend(tldr_findings(lines))

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
