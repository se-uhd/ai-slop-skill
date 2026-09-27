#!/usr/bin/env python3
"""count_findings.py [REPORT] [--root=DIR] [--tropes=PATH] [--scope=PATH:RANGES ...]

Count the findings of the catalog-only review that `/ai-slop:tldr` runs, per
file, and rank each file's patterns by what they cost the reader. A count taken
by eye from a long report drifts, and two readers of the same findings classify
and rank them differently, so the skill takes every count and ranking from this
script.

REPORT defaults to `ai-slop-report.md`. Only the `#### Finding <N>` blocks under
a `## Findings by ...` heading are counted. Items requiring author judgment and
the metric sections are not findings.

Each finding is assigned to a file by its `**Location:**` field:

    `<path>:<line>` (or a line range)   the file at <path>
    `commit <sha>:<line>`                the group `commit messages`
    `Section: <name>`, or anything else  the file named in the `**Paper:**`
                                         header (a PDF has no line numbers)

Each rule that a finding's `**Rule:**` field names falls into one of three
classes. A catalog trope, which the field names as `<name> (tropes.fyi,
<status>)`, is classed by the category that the catalog gives it (see
TROPE_CATEGORY_CLASS), with the exceptions in TROPE_CLASS. A trope that neither
the catalog given with --tropes nor TROPE_CLASS names counts as `delays`. Any
other rule, such as a pattern that the user's instructions added, counts as
`distracts`.

    obscures   the reader cannot tell what is meant
    delays     the reader has to get through text that adds nothing
    distracts  the meaning comes through, but the wording draws attention

A finding that names several rules takes the costliest of their classes. Trope
names are compared in lowercase and without quotation marks, since a Rule field
may write `"Delve" and friends` with or without them.

The tropes of characters and formatting in PER_LINE_TROPES count once per line,
so a line with a pair of curly quotes and an apostrophe is one finding of
Unicode decoration, and a bold lead-in counts once per list item. A report may
record them per character, per pair, or per line, and the counts and the
ranking come out the same.

A finding affects readability when it names a rule that is not minor. The
minor rules are the catalog tropes that only distract, which cover formatting
and the choice of single words, and the tropes in MINOR_TROPES, which restate a
point just made, reuse a word or a filler phrase, or add a short phrase after a
comma. They are nit-picks rather
than feedback: the report keeps them, but they neither count nor rank. A rule
that is not a catalog trope, such as a pattern that the user's instructions
added, is never minor, since the user asked for it.

Output (stdout), tab-separated. Per file with findings, ordered by finding
count, highest first, then by path:

    file\\t<path>\\t<findings>\\t<words>\\t<obscures>\\t<delays>\\t<distracts>\\t<patterns>\\t<feedback>
    rule\\t<path>\\t<count>\\t<affecting>\\t<class>\\t<rule>
    bullet\\t<path>\\t<affecting>\\t<label>\\t<quote>

<words> is the file's prose word count as the reviews extract it with
`scan_repo.py`: every non-blank line of a Markdown, plain-text, or LaTeX file
(so LaTeX markup and form text count too, and the figure is approximate) and
only the comments of a source or config file. The `%` comments of a LaTeX file
do not count, since they hold notes and quoted grounding sources rather than the
text that the reader sees. <words> is `-` where the script cannot read the
file, as for a PDF, a path that does not exist under DIR, or the commit
messages. The three class columns count findings.

<patterns> is the number of findings in the file that affect readability.
<feedback> is `yes` when there are at least MIN_FEEDBACK_PATTERNS of them and
`n/a` otherwise, since one isolated pattern does not warrant feedback.
<affecting> is the number of the rule's findings that affect readability, which
is 0 for a minor rule.

The `rule` lines rank the file's rules by cost, which is WEIGHT of the class
times <affecting>, so the minor rules rank last.

The `bullet` lines are the TL;DR's bullets: the first MAX_BULLETS rules that
affect readability, in the order of the ranking, each with the plain label of
LABELS and the quote of its first finding that no earlier bullet quotes, so
that two bullets never show the same passage. A rule whose findings are all
quoted by earlier bullets gets no bullet. The quote loses its Markdown marks. A
quote longer than MAX_QUOTE_WORDS words is cut at a word boundary and ends in
"...", and a shorter quote that ends in a fragment of a further sentence ends
at its last complete sentence. A pattern that the
instructions added is labeled with its name. A fixed label keeps the TL;DR from
naming one pattern in several ways. Ties break by count, then by catalog status in the order of
STATUS_RANK, since `new` and `rising` name the patterns that the catalog finds
most often in current text, and then by the normalized name. A field that names
several rules counts once for each of them, so the `rule` counts can add up to
more than the findings.

--root=DIR is the directory that the Location paths are relative to. It defaults
to the current working directory. --tropes=PATH is the trope catalog that the
review used. --scope=PATH:RANGES limits the words of the file at PATH to the
lines that the review covered, as comma-separated ranges such as
`12-80,140-190`, when the user's instructions narrowed it to some of its
sections. The option can be given once per file.

The `**Rule:**`, `**Location:**`, and `**Quote:**` labels are also read without
the bullet or the bold, as a model sometimes writes them. A one-line summary is
always printed to stderr, followed by a warning when a finding block has no
rule:

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
# Catalog tropes (normalized names) outside the class `distracts` that are
# minor too: a closing restatement of the points just made, a reused word, a
# filler phrase, and a short phrase after a comma cost the reader a sentence
# at most.
MINOR_TROPES = {
    'fractal summaries', 'the tie-back', 'signposted conclusion', 'self-echo',
    "it's worth noting", 'comma-clipped trailing phrase',
}
# A file needs feedback when it has at least this many findings that affect
# readability, so that a pattern recurs.
MIN_FEEDBACK_PATTERNS = 2
MAX_BULLETS = 5
MAX_QUOTE_WORDS = 25
# Plain labels of the catalog tropes that are not minor (normalized names).
LABELS = {
    'negative parallelism': 'Contrast with a claim that nobody made',
    'short punchy fragments': 'Very short sentences set apart for emphasis',
    'reasoning leak': "Remark about the text's own wording",
    'premise stacking': 'Question or point stated twice in a row',
    'preamble (announce-then-answer)': 'Sentence that announces a point instead of making it',
    'grandiose stakes inflation': 'Inflated claims of importance',
    'compulsive counting': 'Count announced before a list',
    'invented concept labels': 'Invented label used as an established term',
    'rule of three pattern': 'Three words or phrases where one would do',
    'belaboring the unnecessary': 'Defense against an objection that nobody raised',
    'vague attributions': 'Claim attributed to unnamed sources',
    'quotable one-liners': 'Slogan-like sentence without information',
    'forced figurative language': 'Metaphor or simile in place of a plain statement',
    'never-ending conclusion': 'Conclusion that keeps adding clauses',
    'synonym cycling': 'One term replaced by several synonyms',
    'appeal to familiarity': 'Claim of common knowledge without a source',
    'promotional language': 'Promotional wording',
    'collaborative communication': 'Collective "we" for a single writer',
    'not x. not y. just z.': 'Negations stacked before the point',
    "here's the kicker": 'Announced reveal before an ordinary point',
    'excessive enumeration': 'List written as numbered paragraphs',
    'the x? a y.': 'Question answered right away for effect',
    'anaphora abuse': 'Same opening repeated in consecutive sentences',
    'think of it as...': 'Analogy where a plain statement would do',
    'rapid-fire historical analogies': 'String of historical examples offered as proof',
    'imagine a world where...': '"Imagine" scenario in place of an argument',
    'false vulnerability': 'Staged admission',
    'false ranges': '"From X to Y" range with unrelated ends',
    'one-point dilution': 'One point restated at length',
    'content duplication': 'Passage repeated from earlier in the text',
    "let's break this down": 'Explanation of what the reader already knows',
    'superficial analyses': 'Claim of significance added without support',
    'despite its challenges...': 'Problems named and then dismissed',
}
MARKUP_RE = re.compile(r'\*\*|__|`')
# The end of a sentence inside a quote: a period, a question mark, or an
# exclamation mark, with any closing quotation mark or bracket, before a space.
SENTENCE_END_RE = re.compile('(?<!\\be\\.g)(?<!\\bi\\.e)(?<!\\bal)(?<!\\betc)(?<!\\bvs)(?<!\\bcf)'
                             '(?<!\\bFig)(?<!\\bSec)(?<!\\bEq)(?<!\\bTab)(?<!\\bNo)'
                             '[.!?][\'"\u2019\u201d)\\]]*(?=\\s)')
# A quote cut at its last sentence keeps at least this many words.
MIN_SENTENCE_WORDS = 4

# Catalog tropes (normalized names) that count once per line of a file.
PER_LINE_TROPES = {
    'unicode decoration', 'em-dash addiction', 'bold-first bullets',
    'title case headings', 'where / what / why headers',
}
# Catalog statuses in the order that breaks a tie in the ranking.
STATUS_RANK = ('new', 'rising', 'consistent', 'fading')

# Catalog tropes by the category under their heading, with the tropes whose
# cost differs from their category's named in TROPE_CLASS (normalized names).
# The formatting and word-choice tropes are named there too, so they keep their
# class when no catalog is given.
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
    'quietly and other magic adverbs': 'distracts',
    'tapestry and landscape': 'distracts',
    'where it actually lives': 'distracts',
    'the serves as dodge': 'distracts',
    'delve and friends': 'distracts',
}

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
FINDING_RE = re.compile(r'^####\s+Finding\s+\d+')
FIELD_RE = re.compile(
    r'^\s*(?:[-*]\s+)?(?:\*\*)?(Rule|Location|Quote)(?:\*\*)?:(?:\*\*)?\s*(.*?)\s*$')
PAPER_RE = re.compile(r'^\*\*Paper:\*\*\s*(.*?)\s*$')
COMMIT_LOC_RE = re.compile(r'^commit\s+[0-9a-fA-F]{4,40}\b')
PATH_LOC_RE = re.compile(r'^(.+?):(\d+)(?:[-:,]\d+)*\b')
RULE_RE = re.compile(r'[^(),;]+?\s*\([^()]*\)')
# Words that a model puts between two rules in one Rule field, as in
# "Semicolons (G.semicolons), matching \"Self-echo\" (tropes.fyi, new)".
JOINER_RE = re.compile(r'^(?:(?:and|or|plus|also|matching|via|see|as|with|i\.e\.|e\.g\.),?\s+)+', re.IGNORECASE)
QUOTES_RE = re.compile('["\u201c\u201d]')
# A LaTeX comment: an unescaped `%` and the rest of its line.
TEX_COMMENT_RE = re.compile(r'(?<!\\)%.*$')
TROPE_HEADING_RE = re.compile(r'^##\s+(.*?)\s*$')
TROPE_META_RE = re.compile(r'^`(?:new|rising|consistent|fading)`\s*·\s*(.+?)\s*$')


def strip_code(value):
    """Drop the backticks around a field value."""
    return value.strip().strip('`').strip()


def parse_report(text):
    """Return (paper, findings) for a report. `paper` is the `**Paper:**`
    header value or None, and each finding is a (rule, location, quote)
    triple, any of which may be ''."""
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
                current = {'Rule': '', 'Location': '', 'Quote': ''}
            continue
        if current is not None:
            f = FIELD_RE.match(line)
            if f and not current[f.group(1)]:
                current[f.group(1)] = strip_code(f.group(2))
    if current is not None:
        findings.append(current)
    return paper, [(f['Rule'], f['Location'], f['Quote']) for f in findings]


def normalize(name):
    """Return a trope name in lowercase, without quotation marks, and with its
    spaces collapsed, so that `"Delve" and friends` and `Delve and friends`
    match."""
    return ' '.join(QUOTES_RE.sub('', name).lower().split())


def parse_catalog(text):
    """Return {normalized trope name: lowercase category} for a trope catalog."""
    categories = {}
    name = None
    for line in text.splitlines():
        h = TROPE_HEADING_RE.match(line)
        if h:
            name = normalize(h.group(1))
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
    semicolons, "and", "or", or "plus". A parenthesized group without a name
    belongs to the rule before it, as in `Preamble (announce-then-answer)
    (tropes.fyi, new)`. A field without a parenthesized key is one rule."""
    rules = []
    for m in RULE_RE.finditer(field):
        rule = JOINER_RE.sub('', m.group(0).strip())
        if rules and rule.startswith('('):
            rules[-1] += ' ' + rule
        else:
            rules.append(rule)
    return rules or [field or '-']


def trope(rule):
    """Return (normalized name, status) for a rule that names a catalog trope,
    as in `Negative parallelism (tropes.fyi, consistent)`, or None for any
    other rule."""
    paren = rule.rfind('(')
    if paren < 0 or 'tropes.fyi' not in rule[paren:]:
        return None
    return normalize(rule[:paren]), rule[paren:].lower()


def rank_key(rule, count, units, cls):
    """Return the sort key of a rule in a file's ranking: cost, count, catalog
    status, and name. `units` is the number of its findings that affect
    readability."""
    found = trope(rule)
    status = next((i for i, s in enumerate(STATUS_RANK) if found and s in found[1]),
                  len(STATUS_RANK))
    return (-units * WEIGHT[cls], -count, status, found[0] if found else normalize(rule))


def label(rule):
    """Return the plain label of a rule for a TL;DR bullet."""
    found = trope(rule)
    if found is None:
        return re.sub(r'\s*\([^()]*\)\s*$', '', rule).strip() or rule
    return LABELS.get(found[0], rule[:rule.rfind('(')].strip())


def short_quote(quote):
    """Return a quote without its Markdown marks. A quote longer than
    MAX_QUOTE_WORDS words is cut at a word boundary and marked with "...". A
    shorter quote that ends in a fragment of a further sentence, which a report
    adds so that /ai-slop:revise finds the passage, ends at its last complete
    sentence instead."""
    text = ' '.join(MARKUP_RE.sub('', quote).split())
    words = text.split()
    if len(words) > MAX_QUOTE_WORDS:
        return ' '.join(words[:MAX_QUOTE_WORDS]) + ' ...'
    ends = [m.end() for m in SENTENCE_END_RE.finditer(text + ' ')]
    if ends and ends[-1] < len(text) and len(text[:ends[-1]].split()) >= MIN_SENTENCE_WORDS:
        return text[:ends[-1]]
    return text



def affects(rule, cls):
    """Tell whether a finding of this rule, of class `cls`, affects
    readability, which a minor rule does not."""
    found = trope(rule)
    return found is None or not (cls == 'distracts' or found[0] in MINOR_TROPES)


def rule_class(rule, catalog):
    """Return the class of one rule as a Rule field names it. A rule that is
    not a catalog trope, and a finding without a rule, count as `distracts`."""
    found = trope(rule)
    if found is None:
        return 'distracts'
    name = found[0]
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
        if ext == 'tex':
            return [(ln, TEX_COMMENT_RE.sub('', t).strip()) for ln, t in pairs if t]
    else:
        pairs = scan_repo.extract_comments(text, spec)
    return [(ln, t) for ln, t in pairs if t]


def summarize(path, entries, root, catalog, scope=None):
    """Return the output lines for one file's (rule field, line, quote)
    entries, given the (first, last) line ranges that the review covered when
    it covered only part of the file."""
    classes = Counter()
    rules = {}  # rule: [count, affecting, class]
    seen = set()  # (trope, line) of the PER_LINE_TROPES already counted
    counted = 0
    patterns = 0
    quotes = {}  # rule: [(finding index, quote), ...] of its findings that affect readability
    for index, (field, line, quote) in enumerate(entries):
        named = []
        for r in split_rules(field):
            found = trope(r)
            if found and found[0] in PER_LINE_TROPES and line is not None:
                if (found[0], line) in seen:
                    continue
                seen.add((found[0], line))
            named.append(r)
        if not named:
            continue
        counted += 1
        costs = [rule_class(r, catalog) for r in named]
        classes[min(costs, key=CLASSES.index)] += 1
        effects = [affects(r, c) for r, c in zip(named, costs)]
        patterns += any(effects)
        for r, c, e in zip(named, costs, effects):
            entry = rules.setdefault(r, [0, 0, c])
            entry[0] += 1
            entry[1] += e
            if e:
                quotes.setdefault(r, []).append((line or 0, index, quote))

    lines = prose_lines(root, path)
    if lines is not None and scope:
        lines = [(ln, t) for ln, t in lines if any(a <= ln <= b for a, b in scope)]
    words = '-' if lines is None else sum(len(t.split()) for _, t in lines)
    feedback = 'yes' if patterns >= MIN_FEEDBACK_PATTERNS else 'n/a'

    out = [f"file\t{path}\t{counted}\t{words}\t{classes['obscures']}\t"
           f"{classes['delays']}\t{classes['distracts']}\t{patterns}\t{feedback}"]
    ranked = sorted(rules.items(), key=lambda kv: rank_key(kv[0], kv[1][0], kv[1][1], kv[1][2]))
    out += [f"rule\t{path}\t{n}\t{a}\t{c}\t{r}" for r, (n, a, c) in ranked]
    used = set()  # finding indexes that an earlier bullet quotes
    bullets = 0
    for r, (_, a, _) in ranked:
        if not a or bullets == MAX_BULLETS:
            continue
        free = [(ln, i, q) for ln, i, q in sorted(quotes.get(r, [])) if i not in used and q]
        if not free:
            continue
        used.add(free[0][1])
        bullets += 1
        out.append(f"bullet\t{path}\t{a}\t{label(r)}\t{short_quote(free[0][2])}")
    return out


SCOPE_RE = re.compile(r'^(.+):((?:\d+-\d+)(?:,\d+-\d+)*)$')


def parse_args(argv):
    """Return (report, root, tropes, scopes), or None on a usage error.
    `scopes` maps a path to its list of (first, last) line ranges."""
    report, root, tropes, scopes = None, Path('.'), None, {}
    for arg in argv[1:]:
        if arg.startswith('--scope='):
            m = SCOPE_RE.match(arg.split('=', 1)[1])
            if not m or m.group(1) in scopes:
                return None
            ranges = [tuple(int(n) for n in r.split('-')) for r in m.group(2).split(',')]
            if any(a > b for a, b in ranges):
                return None
            scopes[m.group(1)] = ranges
        elif arg.startswith('--root='):
            root = Path(arg.split('=', 1)[1] or '.')
        elif arg.startswith('--tropes='):
            tropes = Path(arg.split('=', 1)[1])
        elif arg.startswith('-'):
            return None
        elif report is None:
            report = Path(arg)
        else:
            return None
    return (report or Path('ai-slop-report.md'), root, tropes, scopes)


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        print("count_findings: usage: count_findings.py [REPORT] [--root=DIR] "
              "[--tropes=PATH] [--scope=PATH:FIRST-LAST[,FIRST-LAST...] ...]",
              file=sys.stderr)
        return 2
    report, root, tropes, scopes = parsed
    try:
        text = report.read_text(encoding='utf-8')
        catalog = parse_catalog(tropes.read_text(encoding='utf-8')) if tropes else {}
    except OSError as e:
        report_unreadable(str(e.filename or report), e)
        return 2
    paper, findings = parse_report(text)
    per_file = {}
    for rule, location, quote in findings:
        path, line = place(location, paper)
        per_file.setdefault(path, []).append((rule, line, quote))
    order = sorted(per_file, key=lambda f: (-len(per_file[f]), f))
    out = []
    for path in order:
        out += summarize(path, per_file[path], root, catalog, scopes.get(path))
    if out:
        sys.stdout.write('\n'.join(out) + '\n')
    print(f"counted {len(findings)} finding(s) across {len(per_file)} file(s)",
          file=sys.stderr)
    missing = sum(1 for rule, _, _ in findings if not rule)
    if missing:
        print(f"warning: {missing} finding(s) have no Rule field and are "
              f"counted under `-`", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
