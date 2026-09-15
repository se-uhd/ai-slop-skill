#!/usr/bin/env python3
"""scan_sentences.py <file> [<file> ...]

Recall aid for the STE layer (`rules-ste.md`). The review pass is an LLM
reading prose, and it counts words as badly as it counts glyphs. A 27-word
sentence that reads smoothly does not look long. This scan splits each file
into sentences, counts their words, and lists the candidates for the STE rules
that a count or a word pattern can find. It prints one tab-separated line per
candidate to stdout:

    <file>:<line>:<col>\\t<kind>\\t<context>

`<line>` and `<col>` (1-based) point at the first character of the sentence,
or of the matched words for the pattern kinds. `<context>` starts with the
count or the matched words, then ` | `, then the sentence with whitespace
collapsed, capped at 120 characters.

Kinds:

  - long-sentence:   a sentence of more than 25 words (`T.short-sentences`).
  - uniform-run:     three or more consecutive sentences in one paragraph with
                     word counts within 5 of each other (`T.vary-length`). The
                     scan prints one row per run, at its first sentence, with
                     the counts in the context ("12/14/11 words").
  - passive:         a form of "be" followed by a past participle, with an
                     adverb such as "also" or "not" allowed in between ("is
                     generated", "was not found"). See `T.active-voice`.
  - nominalization:  a light verb followed by an action noun ("make a
                     decision", "perform an analysis", "carry out the
                     validation"). See `T.verbs-not-nouns`.

The word count leaves out what the STE layer protects. A quotation counts as
one word, and so does an inline code span, a URL, and a math span. A LaTeX
command that carries no prose (a citation, a reference, a label, a footnote, a
to-do note) counts as nothing, and any other command keeps only the text of
its arguments.

This scan is a CANDIDATE finder, not a verdict, exactly like
scan_reference.py. The caller applies each rule's test before reporting. A
passive with an unknown actor stays, and a light verb before a noun that names
a thing rather than an action is not a nominalization. A sentence that carries
the `T.keep-and-mark` marker (`[KEPT: reason]` after the sentence, inline, in
an HTML comment, or in a LaTeX comment) gets no long-sentence, passive, or
nominalization row. Its word count still takes part in the uniform-run check.

Skipped up front, because they are not running prose: fenced code blocks
(nesting honored), YAML front matter, Markdown headings, tables, block quotes,
and HTML comments, and in a `.tex` file the comments, the preamble before
\\begin{document}, the sectioning commands, and the verbatim, code, math, and
tabular environments.

A one-line summary is always printed to stderr:

    scanned 1 file(s), 42 sentence(s); 5 candidate(s) [long-sentence=1 \
uniform-run=1 passive=2 nominalization=1]

Exits 0 when at least one input file was read, whether or not candidates were
found. Exits 2 on a usage error: no arguments, or none of the given paths could
be read. Non-empty stdout signals candidates, and empty stdout means none.

Known limitations:
  - Sentence splitting is a heuristic. A period, question mark, or exclamation
    mark followed by whitespace and a capital letter or digit ends a sentence,
    unless the word before the period is a listed abbreviation (e.g., i.e., et
    al., Fig.) or a single capital initial. "etc." ends a sentence, so an
    "etc." in mid-sentence before a capitalized word splits the sentence.
  - A paragraph is a run of non-blank lines, and a list item starts a new one.
    An indented code block outside a fence is read as prose.
  - A quotation is found by its marks within one paragraph, so a stray
    straight quote can pair with the wrong partner and hide words from the
    count.
  - The list of irregular participles is closed, and an adjective ending in
    -ed after "be" ("is detailed") is listed as a passive. The reviewer
    clears it.
  - An action noun used as a sentence subject ("Validation of the input
    happens in the parser") is not scanned. Only the light-verb pattern is.
"""
import bisect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_io import FenceTracker, report_unreadable  # noqa: E402

KINDS = ('long-sentence', 'uniform-run', 'passive', 'nominalization')

MAX_WORDS = 25   # T.short-sentences, the ASD-STE100 limit for descriptive text
RUN_LENGTH = 3   # T.vary-length, the same test as G.sentence-length:
RUN_SPREAD = 5   # three sentences in a row within 5 words of each other

# ---------- sentence splitting ----------

# Sentence-final punctuation, any closing quote or bracket, then whitespace and
# the start of the next sentence. The lookahead leaves the whitespace unread.
BOUNDARY_RE = re.compile(r'[.!?]+["\')\]]*(?=\s+["\'(\[]*[A-Z0-9])')
WORD_BEFORE_RE = re.compile(r'([A-Za-z][A-Za-z.]*)$')
ABBREVIATIONS = frozenset("""
e.g i.e al vs cf fig figs sec secs eq eqs ch chap pp approx resp incl
dr mr mrs ms prof vol vols eds
""".split())
WORD_CHAR_RE = re.compile(r'[A-Za-z0-9]')

# ---------- normalization (every substitution keeps the length) ----------

KEPT_RE = re.compile(r'(?:<!--\s*)?\[KEPT:[^\]\n]*\](?:\s*-->)?')
QUOTE_RE = re.compile(r'"[^"]*"|\u201c[^\u201d]*\u201d')
URL_RE = re.compile(r'https?://[^\s)>\]]+')

MD_CODE_RE = re.compile(r'``[^`]+``|`[^`]+`')
MD_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)')
MD_LINK_RE = re.compile(r'\[([^\]]*)\]\([^)]*\)')
HTML_COMMENT_RE = re.compile(r'<!--.*?-->')
HTML_TAG_RE = re.compile(r'</?[A-Za-z][^>]*>')
MD_EMPHASIS_RE = re.compile(r'\*+|(?<![A-Za-z0-9])_+|_+(?![A-Za-z0-9])')

TEX_VERB_RE = re.compile(r'\\verb\*?(.)(.*?)\1')
TEX_ESCAPED_DOLLAR_RE = re.compile(r'\\\$')
TEX_MATH_RE = re.compile(r'\$\$.*?\$\$|\$[^$]*\$|\\\(.*?\\\)|\\\[.*?\\\]')
TEX_ESCAPE_RE = re.compile(r'\\[^A-Za-z]')
TEX_COMMAND_RE = re.compile(r'\\([A-Za-z]+)\*?')
TEX_BRACE_RE = re.compile(r'[{}~]')
# Commands dropped with all their arguments: no prose in them, or prose that
# is not part of the sentence (a footnote, a to-do note). Any name containing
# "cite" or ending in "ref" is dropped too (see is_dropped_command).
TEX_DROPPED = frozenset("""
label url includegraphics input include footnote footnotetext todo
bibliography bibliographystyle addbibresource vspace hspace newcommand
renewcommand setlength usepackage documentclass
""".split())

# ---------- paragraph structure ----------

MD_HEADING_RE = re.compile(r'^\s{0,3}#{1,6}(?:\s|$)')
MD_BREAK_RE = re.compile(r'^\s{0,3}(?:[-*_=]\s*){3,}$')
MD_TABLE_RE = re.compile(r'^\s*\|')
MD_QUOTE_RE = re.compile(r'^\s{0,3}>')
MD_LIST_RE = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+')
MD_COMMENT_LINE_RE = re.compile(r'^\s*<!--.*-->\s*$')

TEX_COMMENT_RE = re.compile(r'(?<!\\)%.*$')
TEX_SKIP_ENVS = (
    'verbatim', 'lstlisting', 'minted', 'comment', 'equation', 'align',
    'gather', 'multline', 'displaymath', 'eqnarray', 'tabular', 'tabularx',
    'tikzpicture', 'algorithm', 'algorithmic',
)
TEX_SKIP_BEGIN_RE = re.compile(r'\\begin\{(?:' + '|'.join(TEX_SKIP_ENVS) + r')\*?\}')
TEX_SKIP_END_RE = re.compile(r'\\end\{(?:' + '|'.join(TEX_SKIP_ENVS) + r')\*?\}')
TEX_DOC_BEGIN_RE = re.compile(r'\\begin\{document\}')
TEX_DOC_END_RE = re.compile(r'\\end\{document\}')
TEX_STRUCTURE_RE = re.compile(
    r'^\s*\\(?:part|chapter|section|subsection|subsubsection|paragraph|subparagraph'
    r'|begin|end)\*?(?![A-Za-z])')
TEX_ITEM_RE = re.compile(r'^\s*\\(?:item|caption)(?![A-Za-z])')

# ---------- word patterns ----------

BE = r'(?:am|is|are|was|were|be|been|being)'
ADVERBS = (
    'not|also|often|then|usually|always|never|only|already|still|typically|'
    'generally|automatically|currently|now|first|later|easily|directly|rarely|'
    'largely|widely|mostly|fully|partly|simply|just|commonly|frequently|further|'
    'thus|therefore|explicitly|implicitly|manually|separately|once|previously|'
    'originally|properly|correctly|silently|internally|actually|all|both|each'
)
# The lookahead keeps the match on the "be" form, so "is being reviewed" still
# finds "being reviewed" after "is being" fails the participle test.
PASSIVE_RE = re.compile(
    r'\b' + BE + r'(?=((?:\s+(?:' + ADVERBS + r'))*\s+(?P<part>[A-Za-z]+))\b)', re.I)
IRREGULAR_PARTICIPLES = frozenset("""
built done made given taken written shown known seen found set put kept held
sent left lost met paid read said sold told thought brought bought caught
taught chosen driven drawn broken spoken frozen hidden forgotten begun
overridden rewritten withdrawn understood split cut run spread bound fed led
spent meant dealt felt heard laid struck thrown grown torn worn shaken ridden
fallen beaten proven won shut hit stuck shot lit hung swept upheld withheld
mistaken undertaken forbidden rebuilt reset rerun
""".split())
EED_PARTICIPLES = frozenset('agreed freed guaranteed decreed refereed'.split())
NOT_PARTICIPLES = frozenset("""
embed hundred naked wicked sacred kindred rugged ragged crooked jagged
wretched beloved shred
""".split())

LIGHT_VERBS = (
    'make|makes|made|making|perform|performs|performed|performing|'
    'conduct|conducts|conducted|conducting|carry out|carries out|carried out|'
    'carrying out|undertake|undertakes|undertook|undertaken|undertaking|'
    'give|gives|gave|giving|provide|provides|provided|providing|'
    'offer|offers|offered|offering|take|takes|took|taken|taking|'
    'reach|reaches|reached|reaching|achieve|achieves|achieved|achieving|doing'
)
MAKE_FORMS = frozenset('make makes made making'.split())
DETERMINERS = (
    'a|an|the|some|any|this|that|these|those|its|their|our|another|further|'
    'final|full|quick|brief|careful|detailed|thorough|initial|first|second|'
    'manual|automatic|regular|explicit|proper|separate|new'
)
ACTION_NOUNS = (
    r'[a-z]+(?:tion|sion|ment|ance|ence|ancy|ency|ysis|yses)s?'
    r'|use|choice|attempt|change|changes|check|checks|search|review|request'
    r'|reply|comparison|look|update|fix|test|tests|estimate|guess|mention'
    r'|approval|removal|proposal|refusal|denial|renewal|withdrawal|reversal'
    r'|retrieval|disposal|referral'
)
NOMINAL_RE = re.compile(
    r'\b(?P<verb>' + LIGHT_VERBS + r')(?P<det>(?:\s+(?:' + DETERMINERS + r'))*)'
    r'\s+(?P<noun>' + ACTION_NOUNS + r')\b', re.I)
# Nouns with a suffix that marks an action but that name a thing, a state, or a
# fixed phrase ("takes precedence"), so a light verb before them is plain use.
THING_NOUNS = frozenset("""
environment government department apartment moment element segment fragment
instrument equipment document sentence science audience evidence sequence
instance distance substance presence absence difference silence confidence
section function option caption position portion version session dimension
extension condition question application documentation information attention
tradition edition division mission tension precedence impression performance
experience relevance importance significance maintenance balance entrance
circumstance conference consequence intelligence independence existence
""".split())


def blank(m):
    """Replacement that removes a match and keeps the length."""
    return ' ' * len(m.group(0))


def one_word(m):
    """Replacement that turns a match into one word and keeps the length."""
    return 'X' + ' ' * (len(m.group(0)) - 1)


def one_quote(m):
    """Turn a quotation into one word. Sentence-final punctuation inside the
    closing mark stays at its offset, so "... are." still ends a sentence."""
    s = m.group(0)
    out = ['Q'] + [' '] * (len(s) - 1)
    inner = s[1:-1].rstrip()
    if inner and inner[-1] in '.!?':
        out[len(inner)] = inner[-1]
    return ''.join(out)


def link_text(m):
    """Keep the text of a Markdown link and blank its brackets and target."""
    text = m.group(1)
    return ' ' + text + ' ' * (len(m.group(0)) - len(text) - 1)


def group_end(text, i):
    """Return the index after the bracket or brace group opening at text[i],
    or -1 when the group does not close."""
    open_ch = text[i]
    close_ch = ']' if open_ch == '[' else '}'
    depth = 0
    j = i
    while j < len(text):
        c = text[j]
        if c == '\\':
            j += 2
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return -1


def is_dropped_command(name):
    low = name.lower()
    return 'cite' in low or low.endswith('ref') or name in TEX_DROPPED


def blank_tex_commands(text):
    """Blank every LaTeX command name with its optional arguments. A dropped
    command loses its brace arguments too. Any other command keeps them, and
    TEX_BRACE_RE later blanks the braces alone."""
    chars = list(text)
    i = 0
    while True:
        m = TEX_COMMAND_RE.search(text, i)
        if not m:
            break
        end = m.end()
        dropped = is_dropped_command(m.group(1))
        while end < len(text) and (text[end] == '[' or (dropped and text[end] == '{')):
            close = group_end(text, end)
            if close < 0:
                break
            end = close
        chars[m.start():end] = ' ' * (end - m.start())
        i = end
    return ''.join(chars)


def normalize(ptext, is_tex):
    """Return (norm, markers). `norm` is `ptext` with everything the word count
    leaves out replaced by blanks or a single-letter word of the same length,
    so offsets into `norm` are offsets into `ptext`. `markers` lists the offsets
    of the `[KEPT: ...]` markers that were removed."""
    s = ptext
    if is_tex:
        s = TEX_VERB_RE.sub(one_word, s)
        s = TEX_ESCAPED_DOLLAR_RE.sub(blank, s)
        s = TEX_MATH_RE.sub(one_word, s)
        s = TEX_ESCAPE_RE.sub(blank, s)
        s = blank_tex_commands(s)
        s = s.replace('``', '" ').replace("''", '" ')
        s = TEX_BRACE_RE.sub(blank, s)
    else:
        s = MD_CODE_RE.sub(one_word, s)
    markers = [m.start() for m in KEPT_RE.finditer(s)]
    s = KEPT_RE.sub(blank, s)
    if not is_tex:
        s = HTML_COMMENT_RE.sub(blank, s)
        s = MD_IMAGE_RE.sub(one_word, s)
        s = MD_LINK_RE.sub(link_text, s)
        s = HTML_TAG_RE.sub(blank, s)
        s = MD_EMPHASIS_RE.sub(blank, s)
    s = URL_RE.sub(one_word, s)
    s = QUOTE_RE.sub(one_quote, s)
    return s, markers


def is_abbreviation(norm, i):
    """True when the period at norm[i] closes an abbreviation or an initial."""
    m = WORD_BEFORE_RE.search(norm[max(0, i - 20):i])
    if not m:
        return False
    word = m.group(1)
    if len(word) == 1 and word.isupper():
        return True
    return word.lower() in ABBREVIATIONS


def split_sentences(norm):
    """Yield (start, end) spans of the sentences in a normalized paragraph."""
    start = 0
    for m in BOUNDARY_RE.finditer(norm):
        if norm[m.start()] == '.' and is_abbreviation(norm, m.start()):
            continue
        yield start, m.end()
        start = m.end()
    yield start, len(norm)


def count_words(text):
    return sum(1 for token in text.split() if WORD_CHAR_RE.search(token))


def is_participle(word):
    w = word.lower()
    if w in IRREGULAR_PARTICIPLES:
        return True
    if not w.endswith('ed') or len(w) < 4 or w in NOT_PARTICIPLES:
        return False
    return not w.endswith('eed') or w in EED_PARTICIPLES


def uniform_runs(counts):
    """Return (first, last) index pairs of the maximal runs of at least
    RUN_LENGTH counts that lie within RUN_SPREAD of each other."""
    runs, i = [], 0
    while i < len(counts):
        j, lo, hi = i, counts[i], counts[i]
        while j + 1 < len(counts) and max(hi, counts[j + 1]) - min(lo, counts[j + 1]) <= RUN_SPREAD:
            j += 1
            lo, hi = min(lo, counts[j]), max(hi, counts[j])
        if j - i + 1 >= RUN_LENGTH:
            runs.append((i, j))
            i = j + 1
        else:
            i += 1
    return runs


def truncate(text, limit=120):
    """Collapse runs of whitespace in `text` and cap the result at `limit`
    characters, ending with '...' on truncation."""
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + '...'


def markdown_paragraphs(text):
    """Return the paragraphs of a Markdown or plain-text file. Each paragraph
    is a list of (line_idx, col, text) segments, one per source line."""
    lines = text.splitlines()
    paragraphs, para = [], []

    def flush():
        if para:
            paragraphs.append(list(para))
            para.clear()

    start = 0
    if lines and lines[0].strip() == '---':
        for j in range(1, len(lines)):
            if lines[j].strip() in ('---', '...'):
                start = j + 1
                break
    fences = FenceTracker()
    in_comment = False
    for idx in range(start, len(lines)):
        line = lines[idx]
        if fences.feed(line):
            flush()
            continue
        if in_comment:
            in_comment = '-->' not in line
            continue
        stripped = line.strip()
        if (not stripped or MD_HEADING_RE.match(line) or MD_BREAK_RE.match(line)
                or MD_TABLE_RE.match(line) or MD_QUOTE_RE.match(line)):
            flush()
            continue
        if stripped.startswith('<!--'):
            if '-->' not in line:
                flush()
                in_comment = True
                continue
            if MD_COMMENT_LINE_RE.match(line):
                if para and KEPT_RE.search(line):
                    para.append((idx, 0, line))
                else:
                    flush()
                continue
        m = MD_LIST_RE.match(line)
        if m:
            flush()
            para.append((idx, m.end(), line[m.end():]))
            continue
        para.append((idx, 0, line))
    flush()
    return paragraphs


def tex_paragraphs(text):
    """Return the paragraphs of a LaTeX file in the same shape as
    markdown_paragraphs. A `[KEPT: ...]` marker found in a comment is appended
    as a segment of its own, after the prose it follows."""
    lines = text.splitlines()
    paragraphs, para = [], []

    def flush():
        if para:
            paragraphs.append(list(para))
            para.clear()

    start = 0
    for i, line in enumerate(lines):
        if TEX_DOC_BEGIN_RE.search(TEX_COMMENT_RE.sub('', line)):
            start = i + 1
            break
    in_env = False
    for idx in range(start, len(lines)):
        line = lines[idx]
        cm = TEX_COMMENT_RE.search(line)
        prose = line[:cm.start()] if cm else line
        marker = KEPT_RE.search(cm.group(0)) if cm else None
        if in_env:
            in_env = not TEX_SKIP_END_RE.search(prose)
            continue
        if TEX_SKIP_BEGIN_RE.search(prose):
            flush()
            in_env = not TEX_SKIP_END_RE.search(prose)
            continue
        if TEX_DOC_END_RE.search(prose):
            flush()
            break
        if not prose.strip():
            if not line.strip():
                flush()
            elif marker and para:
                para.append((idx, cm.start() + marker.start(), marker.group(0)))
            continue
        sm = TEX_STRUCTURE_RE.match(prose)
        if sm:
            flush()
            rest = sm.end()
            while rest < len(prose) and prose[rest] in '[{':
                close = group_end(prose, rest)
                if close < 0:
                    break
                rest = close
            if prose[rest:].strip():
                para.append((idx, rest, prose[rest:]))
        else:
            if TEX_ITEM_RE.match(prose):
                flush()
            para.append((idx, 0, prose))
        if marker:
            para.append((idx, cm.start() + marker.start(), marker.group(0)))
    flush()
    return paragraphs


def scan_paragraph(segments, is_tex, stats):
    """Return the candidate rows of one paragraph as (line, col, kind, context)
    tuples and add its sentences to `stats`."""
    starts, pos = [], 0
    for _, _, seg in segments:
        starts.append(pos)
        pos += len(seg) + 1
    ptext = ' '.join(seg for _, _, seg in segments)
    norm, markers = normalize(ptext, is_tex)

    def locate(offset):
        i = bisect.bisect_right(starts, offset) - 1
        line_idx, col, _ = segments[i]
        return line_idx + 1, col + offset - starts[i] + 1

    def context(label, s, e):
        return truncate(f"{label} | {ptext[s:e]}")

    spans = []
    for s, e in split_sentences(norm):
        chunk = norm[s:e]
        s2 = s + len(chunk) - len(chunk.lstrip())
        e2 = s + len(chunk.rstrip())
        words = count_words(norm[s2:e2])
        if words:
            spans.append((s2, e2, words))
    stats['sentences'] += len(spans)

    kept = set()
    for k in markers:
        ended = [i for i, (_, e, _) in enumerate(spans) if e <= k]
        if ended:
            kept.add(ended[-1])

    rows = []
    for i, (s, e, words) in enumerate(spans):
        if i in kept:
            continue
        if words > MAX_WORDS:
            rows.append((*locate(s), 'long-sentence', context(f"{words} words", s, e)))
        sentence = norm[s:e]
        for m in PASSIVE_RE.finditer(sentence):
            if is_participle(m.group('part')):
                a, b = s + m.start(), s + m.end() + len(m.group(1))
                rows.append((*locate(a), 'passive', context(' '.join(ptext[a:b].split()), s, e)))
        for m in NOMINAL_RE.finditer(sentence):
            det = m.group('det').split()
            if m.group('verb').lower() in MAKE_FORMS and any(d.lower() not in ('a', 'an') for d in det):
                continue  # "makes the configuration easier" is causative
            if m.group('noun').lower().rstrip('s') in THING_NOUNS or m.group('noun').lower() in THING_NOUNS:
                continue
            a, b = s + m.start(), s + m.end()
            rows.append((*locate(a), 'nominalization', context(' '.join(ptext[a:b].split()), s, e)))
    for first, last in uniform_runs([w for _, _, w in spans]):
        s, e, _ = spans[first]
        counts = '/'.join(str(spans[j][2]) for j in range(first, last + 1))
        rows.append((*locate(s), 'uniform-run', context(f"{counts} words", s, e)))
    return rows


def scan_file(path, stats):
    """Scan one file, print one TSV row per candidate to stdout, and update
    `stats` in place."""
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        report_unreadable(path, e)
        return
    stats['files'] += 1
    is_tex = Path(path).suffix.lower() == '.tex'
    paragraphs = tex_paragraphs(text) if is_tex else markdown_paragraphs(text)
    rows = []
    for segments in paragraphs:
        rows.extend(scan_paragraph(segments, is_tex, stats))
    for line, col, kind, context in sorted(rows, key=lambda r: (r[0], r[1], KINDS.index(r[2]))):
        stats['counts'][kind] += 1
        print(f"{path}:{line}:{col}\t{kind}\t{context}")


def main(argv):
    if len(argv) < 2:
        print("usage: scan_sentences.py <file> [<file> ...]", file=sys.stderr)
        return 2
    stats = {'files': 0, 'sentences': 0, 'counts': {k: 0 for k in KINDS}}
    paths = argv[1:]
    for path in paths:
        scan_file(path, stats)
    total = sum(stats['counts'].values())
    breakdown = ' '.join(f"{k}={stats['counts'][k]}" for k in KINDS)
    print(
        f"scanned {stats['files']} file(s), {stats['sentences']} sentence(s); "
        f"{total} candidate(s) [{breakdown}]",
        file=sys.stderr,
    )
    if stats['files'] == 0:
        print(
            f"error: none of the {len(paths)} path(s) given could be read; nothing was scanned",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
