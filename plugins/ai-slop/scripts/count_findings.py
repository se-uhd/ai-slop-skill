#!/usr/bin/env python3
"""count_findings.py [REPORT] [--root=DIR] [--tropes=PATH]

Count the findings of an ai-slop review report per file, sort them by what
they cost the reader, and give each file's impact level and AI-use verdict, for
`/ai-slop:tldr`. A count taken by eye from a long report drifts, and two readers
of the same findings classify, rank, and rate them differently, so the skill
takes every count, class, ranking, level, and verdict from this script.

REPORT defaults to `ai-slop-report.md`. Only the `#### Finding <N>` blocks under
a `## Findings by ...` heading are counted. Items requiring author judgment, the
metric sections, and the grounding to-do are not findings.

Each finding is assigned to a file by its `**Location:**` field:

    `<path>:<line>` (or a line range)   the file at <path>
    `commit <sha>:<line>`                the group `commit messages`
    `Section: <name>`, or anything else  the file named in the `**Paper:**`
                                         header (a PDF has no line numbers)

Each rule that a finding's `**Rule:**` field names falls into one of three
classes. A rule of a layer is classed by its key (see OBSCURES, DELAYS, and
DISTRACTS). A catalog trope is classed by the category that the catalog gives
it (see TROPE_CATEGORY_CLASS and TROPE_CLASS), when --tropes names the catalog,
and counts as `delays` otherwise.

    obscures   the reader cannot tell what is meant
    delays     the reader has to get through text that adds nothing
    distracts  the meaning comes through, but the wording draws attention

A finding that names several rules takes the costliest of their classes.

Output (stdout), tab-separated. Per file with findings, ordered by finding
count, highest first, then by path:

    file\\t<path>\\t<findings>\\t<words>\\t<obscures>\\t<delays>\\t<distracts>\\t<level>\\t<rewrite>%\\t<ai>\\t<ai in rewrite>\\t<signs>\\t<verdict>
    rule\\t<path>\\t<count>\\t<class>\\t<rule>
    para\\t<path>\\t<first line>-<last line>\\t<obscures>\\t<delays>

<words> is the file's prose word count as the reviews extract it with
`scan_repo.py`: every non-blank line of a Markdown, plain-text, or LaTeX file
(so LaTeX markup and form text count too, and the figure is approximate) and
only the comments of a source or config file. The three class columns count
findings. The `rule` lines rank the file's rules by cost, which is the count
times WEIGHT of the class, then by count and by name. A field that names several
rules counts once for each of them, so the `rule` counts can add up to more than
the findings.

The level follows from the paragraphs, which are runs of consecutive prose
lines. A paragraph needs a rewrite when at least two of its findings obscure or
delay, and at least one per REWRITE_WORDS words of the paragraph, so a long
paragraph does not qualify by its length alone. Each such paragraph gets a
`para` line. <rewrite> is the share of the prose words, in percent, that are in
paragraphs that need a rewrite. The prose is every paragraph of at least
MIN_PARAGRAPH_WORDS words (shorter ones are mostly form fields and headings)
plus any shorter paragraph that needs a rewrite. The level is

    None       no finding obscures or delays
    Minor      under a tenth of the prose needs a rewrite
    Moderate   a tenth to under a third
    Major      a third to under two thirds
    Severe     two thirds or more

Major and Severe also need at least MIN_REWRITE_PARAGRAPHS paragraphs that need
a rewrite, since in a short text one or two paragraphs make up most of the
prose. With fewer, the level stays at Moderate.

The verdict answers whether the writers used AI tools in a reasonable way or in
a way that makes the text harder to read. It rests on the AI-typical findings,
which are the findings of a catalog trope or of a rule in AI_TYPICAL, the
patterns that AI output overproduces. Grammar slips, dropped words, spelling,
and unclear pronouns are left out, since hurried human writing produces them
too. A trope in EDITOR_TROPES never counts, because the editor or the web form
inserts it rather than the writer (curly quotes appeared in 68 to 88 percent of
a set of peer reviews, whatever else the reviews showed).

The report's `## Signs of unassisted writing` section, which `/ai-slop:tldr`
adds, lists typos, grammar slips, missing articles, and missing words, one
bullet each that opens with its location in backticks. Current models rarely
produce them, and a sign shows that its own paragraph was typed by a person. In
a paragraph with a sign, the findings of the rules in WEAK_AI stop counting as
AI-typical, since non-native and hurried writers produce figurative phrasing,
padding, long sentences, and enumerations as readily as models do. The sign
does not affect other paragraphs, which in a file with several writers may be
someone else's. Where the script cannot read the file by paragraphs, the WEAK_AI
findings stop counting when the file has at least MIN_HUMAN_SIGNS signs. <ai> counts the AI-typical findings that count,
<ai in rewrite> counts those in paragraphs that need a rewrite, and <signs>
counts the signs of unassisted writing. The verdict is

    Little sign of AI tools  fewer than MIN_AI_FINDINGS AI-typical findings,
                             or fewer than MIN_AI_DENSITY per page-equivalent
                             of PAGE_WORDS words
    Harder to read           otherwise, when the level is Moderate or above
                             and at least one AI-typical finding is in a
                             paragraph that needs a rewrite
    Reasonable               otherwise

On a set of 339 peer reviews without recorded signs of unassisted writing, this
rule matched the answer of a model that read each review with its findings in
190 of 298 cases, and in 75 of the 103 that the model called harder to read.
The synthetic reviews under tests/fixtures/tldr pin the intended verdict for
each case.

The words, the level, the share, and <ai in rewrite> are `-` where the script
cannot read the file, as for a PDF, a path that does not exist under DIR, or
the commit messages, except that the level is `None` there too when no finding
obscures or delays. The verdict is `-` there when it depends on the paragraphs.

--root=DIR is the directory that the Location paths are relative to. It defaults
to the current working directory. --tropes=PATH is the trope catalog that the
review used.

The `**Rule:**` and `**Location:**` labels are also read without the bullet
or the bold, as a model sometimes writes them. A one-line summary is always
printed to stderr, followed by a warning when a finding block has no rule:

    counted 42 finding(s) across 5 file(s)
    warning: 2 finding(s) have no Rule field and are counted under `-`

Exit codes:
    0  the report was read (with or without findings)
    2  usage error, or the report or the catalog cannot be read
"""
import re
import sys
from collections import Counter
from pathlib import Path

import scan_repo
from scan_io import FenceTracker, report_unreadable

COMMITS = 'commit messages'
CLASSES = ('obscures', 'delays', 'distracts')
WEIGHT = {'obscures': 4, 'delays': 3, 'distracts': 1}
MIN_PARAGRAPH_WORDS = 15
REWRITE_WORDS = 100
MIN_REWRITE_PARAGRAPHS = 3
LEVELS = ((2 / 3, 'Severe'), (1 / 3, 'Major'), (1 / 10, 'Moderate'), (0, 'Minor'))

OBSCURES = {
    'G.one-term', 'G.define-once', 'G.distinct-synonyms', 'G.anchor-pronouns',
    'G.summarizing-nouns', 'G.definite-article', 'G.stand-ins', 'G.connectives',
    'G.parenthetical-lists', 'G.be-concrete', 'G.no-coinages',
    'S.significant', 'S.citation-clusters', 'S.cite-specific-works',
    'S.ground-claims', 'S.state-the-gap', 'S.verify-references',
    'S.no-invented-fields', 'S.effect-sizes', 'S.exact-p-values',
    'S.confidence-intervals', 'S.specific-captions',
    'L.verify-bibtex', 'L.no-invented-fields',
    'T.one-meaning',
}
DELAYS = {
    'G.phrases-to-avoid', 'G.no-formulaic-openings', 'G.no-formulaic-closings',
    'G.no-rule-of-three', 'G.no-announced-counts', 'G.short-enumerations',
    'G.no-list-cramming', 'G.no-prose-listicle', 'G.refer-back',
    'G.sentence-padding', 'G.paragraph-padding', 'G.hedge-from-evidence',
    'G.take-positions', 'G.no-metacommentary', 'G.plain-language',
    'G.no-figurative-language',
    'S.research-coded-phrases', 'S.no-restatement', 'S.body-independent',
    'S.analyze-prior-work', 'S.no-table-repetition', 'S.specific-threats',
    'S.no-performative-hedging',
    'T.short-sentences', 'T.one-topic',
}
DISTRACTS = {
    'G.american-english', 'G.data-singular', 'G.such-as', 'G.restricted-words',
    'G.consequence-connectives', 'G.catalog-precedence', 'G.active-voice',
    'G.consistent-tense', 'G.participial-openings', 'G.keep-that',
    'G.whose-on-things', 'G.em-dashes', 'G.em-dash-glyphs', 'G.colons',
    'G.introducer-colon', 'G.colon-capitalization', 'G.semicolons',
    'G.pause-mark-count', 'G.sentence-length', 'G.compound-hyphens',
    'G.oxford-comma', 'G.paragraph-length', 'G.one-example-signal',
    'G.no-excess-bold', 'G.reformulate', 'G.match-voice', 'G.plain-words',
    'S.we', 'S.tense-by-section', 'S.paper-vs-study', 'S.no-lists',
    'S.no-abstract-citations', 'S.spell-out-below-ten', 'S.no-initial-numeral',
    'S.numerals-from-ten', 'S.thousands-separator', 'S.rounding',
    'S.consistent-decimals', 'S.leading-zeros', 'S.sample-size-symbols',
    'S.italic-symbols', 'S.spell-out-statistics',
    'S.capitalize-cross-references', 'S.refer-to-every-figure',
    'S.sequential-numbering',
    'L.quotes', 'L.unspaced-em-dashes', 'L.caption-punctuation',
    'L.cross-reference-macros', 'L.citeauthor', 'L.grounding-comments',
    'L.editorial-comments', 'L.source-priority', 'L.check-fields',
    'T.scope', 'T.precedence', 'T.vary-length', 'T.active-voice',
    'T.verbs-not-nouns', 'T.keep-articles', 'T.one-device', 'T.quotations',
    'T.literals', 'T.keep-original',
}
# Rules for the patterns that AI output overproduces. Every catalog trope counts
# too. A finding of one of them is AI-typical.
AI_TYPICAL = {
    'G.restricted-words', 'G.phrases-to-avoid', 'G.sentence-padding',
    'G.paragraph-padding', 'G.refer-back', 'G.no-formulaic-openings',
    'G.no-formulaic-closings', 'G.no-rule-of-three', 'G.no-announced-counts',
    'G.no-prose-listicle', 'G.em-dashes', 'G.em-dash-glyphs', 'G.no-excess-bold',
    'G.hedge-from-evidence', 'G.take-positions', 'G.no-metacommentary',
    'G.no-figurative-language', 'G.plain-words', 'G.no-coinages',
    'G.sentence-length',
    'S.research-coded-phrases', 'S.no-restatement', 'S.analyze-prior-work',
    'S.specific-threats', 'S.no-performative-hedging',
}
MIN_AI_FINDINGS = 2
# Catalog tropes (lowercase names) that the editor or web form inserts.
EDITOR_TROPES = {'unicode decoration'}
# AI-typical rules whose patterns non-native and hurried writers produce too.
# They stop counting when a file shows signs of unassisted writing.
WEAK_AI = {
    'G.no-figurative-language', 'G.sentence-padding', 'G.sentence-length',
    'G.no-prose-listicle', 'G.plain-words', 'G.no-coinages', 'G.em-dashes',
    'G.take-positions', 'G.hedge-from-evidence',
}
MIN_HUMAN_SIGNS = 2
MIN_AI_DENSITY = 1.0
PAGE_WORDS = 350
MODERATE_OR_ABOVE = ('Moderate', 'Major', 'Severe')

KEY_CLASS = {**{k: 'obscures' for k in OBSCURES},
             **{k: 'delays' for k in DELAYS},
             **{k: 'distracts' for k in DISTRACTS}}

# Catalog tropes by the category under their heading, with the tropes whose
# cost differs from their category's named in TROPE_CLASS (lowercase names).
# The formatting tropes are named there too, so they keep their class when no
# catalog is given.
TROPE_CATEGORY_CLASS = {
    'composition': 'delays', 'tone': 'delays', 'sentence structure': 'delays',
    'paragraph structure': 'delays', 'word choice': 'distracts',
    'formatting': 'distracts',
}
TROPE_CLASS = {
    'synonym cycling': 'obscures',
    'vague attributions': 'obscures',
    'invented concept labels': 'obscures',
    'unicode decoration': 'distracts',
    'em-dash addiction': 'distracts',
    'title case headings': 'distracts',
    'bold-first bullets': 'distracts',
}

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
FINDING_RE = re.compile(r'^####\s+Finding\s+\d+')
FIELD_RE = re.compile(
    r'^\s*(?:[-*]\s+)?(?:\*\*)?(Rule|Location)(?:\*\*)?:(?:\*\*)?\s*(.*?)\s*$')
PAPER_RE = re.compile(r'^\*\*Paper:\*\*\s*(.*?)\s*$')
COMMIT_LOC_RE = re.compile(r'^commit\s+[0-9a-fA-F]{4,40}\b')
PATH_LOC_RE = re.compile(r'^(.+?):(\d+)(?:[-:,]\d+)*\b')
RULE_RE = re.compile(r'[^(),;]+?\s*\([^()]*\)')
JOINER_RE = re.compile(r'^(?:and|or|plus)\s+', re.IGNORECASE)
KEY_RE = re.compile(r'^\(\s*([GSLT]\.[a-z0-9-]+)')
SIGNS_TITLE = 'Signs of unassisted writing'
SIGN_RE = re.compile(r'^\s*[-*]\s+`([^`]+)`')
TROPE_HEADING_RE = re.compile(r'^##\s+(.*?)\s*$')
TROPE_META_RE = re.compile(r'^`(?:new|rising|consistent|fading)`\s*·\s*(.+?)\s*$')


def strip_code(value):
    """Drop the backticks around a field value."""
    return value.strip().strip('`').strip()


def parse_report(text):
    """Return (paper, findings) for a report. `paper` is the `**Paper:**`
    header value or None, and each finding is a (rule, location) pair, either
    of which may be ''."""
    paper = None
    findings = []
    in_findings = False
    current = None
    fences = FenceTracker()
    for line in text.splitlines():
        if fences.feed(line):
            continue
        m = PAPER_RE.match(line)
        if m and paper is None:
            paper = strip_code(m.group(1))
            continue
        h = HEADING_RE.match(line)
        if h:
            level, title = len(h.group(1)), h.group(2)
            if current is not None:
                findings.append(current)
                current = None
            if level <= 2:
                in_findings = level == 2 and title.startswith('Findings by')
            elif in_findings and FINDING_RE.match(line):
                current = {'Rule': '', 'Location': ''}
            continue
        if current is not None:
            f = FIELD_RE.match(line)
            if f and not current[f.group(1)]:
                current[f.group(1)] = strip_code(f.group(2))
    if current is not None:
        findings.append(current)
    return paper, [(f['Rule'], f['Location']) for f in findings]


def parse_signs(text):
    """Return the locations listed under the report's `## Signs of unassisted
    writing` heading."""
    signs, inside = [], False
    fences = FenceTracker()
    for line in text.splitlines():
        if fences.feed(line):
            continue
        h = HEADING_RE.match(line)
        if h:
            inside = len(h.group(1)) == 2 and h.group(2) == SIGNS_TITLE
            continue
        m = SIGN_RE.match(line) if inside else None
        if m:
            signs.append(m.group(1).strip())
    return signs


def parse_catalog(text):
    """Return {lowercase trope name: lowercase category} for a trope catalog."""
    categories = {}
    name = None
    for line in text.splitlines():
        h = TROPE_HEADING_RE.match(line)
        if h:
            name = h.group(1).strip().lower()
            continue
        m = TROPE_META_RE.match(line.strip())
        if m and name:
            categories[name] = m.group(1).strip().lower()
            name = None
    return categories


def place(location, paper):
    """Map a Location field to (file or group, line or None)."""
    if COMMIT_LOC_RE.match(location):
        return COMMITS, None
    m = PATH_LOC_RE.match(location)
    if m and not location.startswith('Section:'):
        return m.group(1), int(m.group(2))
    return paper or location or '-', None


def split_rules(field):
    """Split a Rule field into the rules that it names. Each rule is a name
    followed by its key in parentheses, and the rules may be joined by commas,
    semicolons, "and", "or", or "plus". A field without a parenthesized key is
    one rule."""
    rules = [JOINER_RE.sub('', m.group(0).strip()) for m in RULE_RE.finditer(field)]
    return rules or [field or '-']


def is_ai_typical(rule, discount_weak=False):
    """True for a catalog trope outside EDITOR_TROPES or a rule in AI_TYPICAL.
    With discount_weak, the rules in WEAK_AI do not count."""
    paren = rule.rfind('(')
    tail = rule[paren:] if paren >= 0 else ''
    m = KEY_RE.match(tail)
    if m:
        return m.group(1) in AI_TYPICAL and not (discount_weak and m.group(1) in WEAK_AI)
    name = rule[:paren].strip().strip('"').strip().lower() if paren >= 0 else ''
    return 'tropes.fyi' in tail and name not in EDITOR_TROPES


def rule_class(rule, catalog):
    """Return the class of one rule as a Rule field names it. A finding
    without a rule counts as `distracts`, the class that moves no level."""
    if rule == '-':
        return 'distracts'
    paren = rule.rfind('(')
    tail = rule[paren:] if paren >= 0 else ''
    m = KEY_RE.match(tail)
    if m:
        return KEY_CLASS.get(m.group(1), 'distracts')
    name = rule[:paren].strip().strip('"').strip().lower() if paren >= 0 else rule.lower()
    if name in TROPE_CLASS:
        return TROPE_CLASS[name]
    return TROPE_CATEGORY_CLASS.get(catalog.get(name, ''), 'delays')


def prose_lines(root, relpath):
    """Return the (lineno, text) prose lines of a file the way scan_repo.py
    extracts them, or None when the file cannot be read."""
    if relpath == COMMITS:
        return None
    path = root / relpath
    if not path.is_file():
        return None
    kind, spec = scan_repo.classify(relpath)
    if kind == 'skip':
        return None
    text = scan_repo.read_text(str(path))
    if text is None:
        return None
    if kind == 'prose':
        ext = relpath.rsplit('.', 1)[-1].lower() if '.' in relpath else ''
        pairs = scan_repo.extract_prose(text, ext in ('md', 'markdown', 'mdx'))
    else:
        pairs = scan_repo.extract_comments(text, spec)
    return [(ln, t) for ln, t in pairs if t]


def paragraphs(lines):
    """Group (lineno, text) lines into paragraphs of consecutive line numbers.
    Return a list of [first, last, words]."""
    paras = []
    for ln, t in lines:
        if paras and ln == paras[-1][1] + 1:
            paras[-1][1] = ln
            paras[-1][2] += len(t.split())
        else:
            paras.append([ln, ln, len(t.split())])
    return paras


def summarize(path, entries, root, catalog, sign_lines=()):
    """Return the output lines for one file's (rule field, line) entries, given
    the lines of its signs of unassisted writing."""
    signs = len(sign_lines)
    classes = Counter()
    rules = {}
    placed = []
    kinds = []  # per finding: (line, 'strong', 'weak', or None)
    for field, line in entries:
        named = split_rules(field)
        costs = [rule_class(r, catalog) for r in named]
        cls = min(costs, key=CLASSES.index)
        classes[cls] += 1
        placed.append((line, cls))
        strong = any(is_ai_typical(r, discount_weak=True) for r in named)
        weak = not strong and any(is_ai_typical(r) for r in named)
        kinds.append((line, 'strong' if strong else 'weak' if weak else None))
        for r, c in zip(named, costs):
            count, _ = rules.get(r, (0, c))
            rules[r] = (count + 1, c)

    lines = prose_lines(root, path)
    words = level = share = ai_rewrite = '-'
    para_out = []
    heavy = classes['obscures'] + classes['delays']
    discount = signs >= MIN_HUMAN_SIGNS
    ai_lines = [line for line, kind in kinds if kind == 'strong' or (kind == 'weak' and not discount)]
    if lines is not None:
        words = sum(len(t.split()) for _, t in lines)
        paras = paragraphs(lines)

        def para_of(line):
            return next((i for i, (first, last, _) in enumerate(paras)
                         if line is not None and first <= line <= last), None)
        signed = {para_of(line) for line in sign_lines} - {None}
        ai_lines = [line for line, kind in kinds
                    if kind == 'strong' or (kind == 'weak' and para_of(line) not in signed)]
        hits = [Counter() for _ in paras]
        for line, cls in placed:
            if line is None or cls == 'distracts':
                continue
            for i, (first, last, _) in enumerate(paras):
                if first <= line <= last:
                    hits[i][cls] += 1
                    break
        rewrite = [i for i, h in enumerate(hits)
                   if h['obscures'] + h['delays']
                   >= max(2, -(-paras[i][2] // REWRITE_WORDS))]
        prose = sum(p[2] for i, p in enumerate(paras)
                    if p[2] >= MIN_PARAGRAPH_WORDS or i in rewrite)
        ratio = sum(paras[i][2] for i in rewrite) / prose if prose else 0
        share = f"{round(100 * ratio)}%"
        level = 'None' if heavy == 0 else next(
            name for bound, name in LEVELS if ratio >= bound)
        if level in ('Major', 'Severe') and len(rewrite) < MIN_REWRITE_PARAGRAPHS:
            level = 'Moderate'
        for i in rewrite:
            para_out.append(f"para\t{path}\t{paras[i][0]}-{paras[i][1]}\t"
                            f"{hits[i]['obscures']}\t{hits[i]['delays']}")
        ai_rewrite = sum(1 for line in ai_lines if line is not None and any(
            paras[i][0] <= line <= paras[i][1] for i in rewrite))
    elif heavy == 0:
        level = 'None'

    sparse = words != '-' and len(ai_lines) < MIN_AI_DENSITY * words / PAGE_WORDS
    if len(ai_lines) < MIN_AI_FINDINGS or sparse:
        verdict = 'Little sign of AI tools'
    elif ai_rewrite == '-':
        verdict = '-'
    elif level in MODERATE_OR_ABOVE and ai_rewrite >= 1:
        verdict = 'Harder to read'
    else:
        verdict = 'Reasonable'

    out = [f"file\t{path}\t{len(entries)}\t{words}\t{classes['obscures']}\t"
           f"{classes['delays']}\t{classes['distracts']}\t{level}\t{share}\t"
           f"{len(ai_lines)}\t{ai_rewrite}\t{signs}\t{verdict}"]
    ranked = sorted(rules.items(),
                    key=lambda kv: (-kv[1][0] * WEIGHT[kv[1][1]], -kv[1][0], kv[0]))
    out += [f"rule\t{path}\t{n}\t{c}\t{r}" for r, (n, c) in ranked]
    return out + para_out


def parse_args(argv):
    """Return (report, root, tropes), or None on a usage error."""
    report, root, tropes = None, Path('.'), None
    for arg in argv[1:]:
        if arg.startswith('--root='):
            root = Path(arg.split('=', 1)[1] or '.')
        elif arg.startswith('--tropes='):
            tropes = Path(arg.split('=', 1)[1])
        elif arg.startswith('-'):
            return None
        elif report is None:
            report = Path(arg)
        else:
            return None
    return (report or Path('ai-slop-report.md'), root, tropes)


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        print("count_findings: usage: count_findings.py [REPORT] [--root=DIR] "
              "[--tropes=PATH]", file=sys.stderr)
        return 2
    report, root, tropes = parsed
    try:
        text = report.read_text(encoding='utf-8')
        catalog = parse_catalog(tropes.read_text(encoding='utf-8')) if tropes else {}
    except OSError as e:
        report_unreadable(str(e.filename or report), e)
        return 2
    paper, findings = parse_report(text)
    per_file = {}
    for rule, location in findings:
        path, line = place(location, paper)
        per_file.setdefault(path, []).append((rule, line))
    signs = {}
    for location in parse_signs(text):
        path, line = place(location, paper)
        signs.setdefault(path, []).append(line)
    order = sorted(per_file, key=lambda f: (-len(per_file[f]), f))
    out = []
    for path in order:
        out += summarize(path, per_file[path], root, catalog, signs.get(path, []))
    if out:
        sys.stdout.write('\n'.join(out) + '\n')
    print(f"counted {len(findings)} finding(s) across {len(per_file)} file(s)",
          file=sys.stderr)
    missing = sum(1 for rule, _ in findings if not rule)
    if missing:
        print(f"warning: {missing} finding(s) have no Rule field and are "
              f"counted under `-`", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
