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
  tldr-block-shape              `ai-slop-tldr.md`: a per-file `##` block
                                has no `**Impact on readability:**` line
                                or a level outside the scale (None,
                                Minor, Moderate, Major, Severe, followed
                                by the rewrite share in parentheses), no
                                `**AI use:**` line or a verdict other
                                than Reasonable, Harder to read, or
                                Little sign of AI tools, no assessment
                                or more than five sentences in it, more
                                than three bullets, or bullets without
                                the `**Patterns that most affect
                                readability:**` line before them. The block that
                                lists the files without findings is
                                exempt. Sentences are counted after
                                quotes, code spans, and common
                                abbreviations are removed, so the count
                                is a heuristic that errs low.

The linter (`lint_markdown.py`, synced from pymarkdown-skill) loads this
file via importlib and calls `schema_findings(text, path)` at lint time.
"""
import re

SKILL_NAME = "ai-slop"

REPORT_H1_BODY = "AI Slop Review"
TLDR_H1_BODY = "AI Slop TL;DR"
TLDR_EXEMPT_H2_BODY = "Files without findings"
TLDR_LEVELS = ("None", "Minor", "Moderate", "Major", "Severe")
TLDR_VERDICTS = ("Reasonable", "Harder to read", "Little sign of AI tools")
TLDR_BULLETS_INTRO = "**Patterns that most affect readability:**"
TLDR_MAX_SENTENCES = 5
TLDR_MAX_BULLETS = 3
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
LEVEL_RE = re.compile(r'^\*\*Impact on readability:\*\*\s*(.*?)(?:\s*\([^()]*\))?\.?\s*$')
VERDICT_RE = re.compile(r'^\*\*AI use:\*\*\s*(.*?)\.?\s*$')
BULLET_RE = re.compile(r'^[-*+]\s+')
QUOTED_RE = re.compile(r'`[^`]*`|"[^"]*"|\u201c[^\u201d]*\u201d')
ABBREV_RE = re.compile(r'\b(e\.g|i\.e|et al|cf|vs|etc)\.')
SENTENCE_END_RE = re.compile(r'[.!?](?=\s+[(\[]?[A-Z0-9]|\s*$)')


def count_sentences(text):
    """Count the sentences in an assessment, ignoring quoted text, code spans,
    and the periods of common abbreviations."""
    text = ABBREV_RE.sub(lambda m: m.group(1), QUOTED_RE.sub('Q', text))
    return len(SENTENCE_END_RE.findall(text.strip()))


def tldr_findings(lines):
    """Check the per-file blocks of an `ai-slop-tldr.md` (see the module
    docstring for the shape they must have)."""
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
        level = None
        verdict = None
        intro = False
        prose = []
        bullets = 0
        in_bullet = False
        for _, line in body:
            lm = LEVEL_RE.match(line)
            vm = VERDICT_RE.match(line)
            if lm and level is None:
                level = lm.group(1).strip()
                in_bullet = False
            elif vm and verdict is None:
                verdict = vm.group(1).strip()
                in_bullet = False
            elif line.strip() == TLDR_BULLETS_INTRO:
                intro = True
                in_bullet = False
            elif BULLET_RE.match(line):
                if not bullets and not intro:
                    findings.append((head, 'tldr-block-shape',
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
        if level is None:
            findings.append((head, 'tldr-block-shape',
                             'TL;DR block has no **Impact on readability:** line'))
        elif level not in TLDR_LEVELS:
            findings.append((head, 'tldr-block-shape',
                             f'TL;DR impact level {level!r} is not one of '
                             + ', '.join(TLDR_LEVELS)))
        if verdict is None:
            findings.append((head, 'tldr-block-shape',
                             'TL;DR block has no **AI use:** line'))
        elif verdict not in TLDR_VERDICTS:
            findings.append((head, 'tldr-block-shape',
                             f'TL;DR AI-use verdict {verdict!r} is not one of '
                             + ', '.join(TLDR_VERDICTS)))
        n = count_sentences(' '.join(prose))
        if n == 0:
            findings.append((head, 'tldr-block-shape',
                             'TL;DR block has no assessment'))
        elif n > TLDR_MAX_SENTENCES:
            findings.append((head, 'tldr-block-shape',
                             f'TL;DR assessment has {n} sentences '
                             f'(at most {TLDR_MAX_SENTENCES})'))
        if bullets > TLDR_MAX_BULLETS:
            findings.append((head, 'tldr-block-shape',
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
