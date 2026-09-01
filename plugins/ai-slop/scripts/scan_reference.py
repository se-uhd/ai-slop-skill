#!/usr/bin/env python3
"""scan_reference.py <file> [<file> ...]

Recall aid for the general layer's **Reference** rules. The per-section review
pass is an LLM reading prose, and it walks past unanchored references the same
way it undercounts Unicode glyphs: a sentence-initial "This shows that ..." reads
fluently, so the eye does not stop. This scan lists every candidate so the
reviewer applies the rule's test ("the [noun] just mentioned") to each one. It
prints one tab-separated line per candidate to stdout:

    <file>:<line>:<col>\\t<kind>\\t<context>

`<col>` is the 1-based character column of the pronoun or of "such", so two
candidates on one line are two rows. `<context>` is the whole line, whitespace
collapsed and capped at 120 characters.

Kinds:

  - bare-demonstrative: a sentence-initial This / These / That / It followed
                        directly by a verb (an auxiliary, a modal, or one of the
                        closed list of commentary verbs in VERBS, optionally after
                        an adverb such as "also" or "in turn"). A demonstrative
                        followed by a noun ("These tests were") is anchored and
                        is not listed. The verb list is closed on purpose: an
                        "-s means verb" heuristic would list "These tests".
  - such-noun:          "such" + noun anywhere in running prose ("such tools",
                        "such an approach"). Whether the text has instantiated
                        the category is the reviewer's judgment; the scan only
                        guarantees recall. "such as" and "such that" are not
                        matched.
  - stand-in:           a word standing in for a noun the sentence could name
                        (ones, the former, the latter, respectively, do / did so, and
                        "those" followed by of / that / which / with). "one" is
                        not scanned: the numeral and the generic "one" would
                        swamp the list.

This is a CANDIDATE finder, not a verdict, exactly like scan_glyphs.py. The
caller applies the rule's test and exceptions before reporting. Skipped up
front, because they are never findings: LaTeX comment lines and trailing `%`
comments in `.tex` files, fenced code blocks, LaTeX verbatim / lstlisting /
minted / comment environments, and the common dummy-it frames ("It is possible
that", "It is unclear whether", "It follows that", "It turns out", "It remains to
be seen"; the cue list is DUMMY_IT_CUES). "That is," and "That said," are
connectives, not references, and are skipped too.

A one-line summary is always printed to stderr:

    scanned 1 file(s); 5 reference candidate(s) [bare-demonstrative=3 such-noun=1 stand-in=1]

Exits 0 when at least one input file was read, whether or not candidates were
found. Exits 2 on a usage error: no arguments, or none of the given paths could
be read. Non-empty stdout signals candidates; empty stdout means none.

Known limitations:
  - Matching is case-sensitive on the capitalized forms, and a sentence start is
    detected from punctuation on the same line (or the line start). A "This" at
    the start of a hard-wrapped LaTeX line mid-sentence is therefore listed; the
    test applies to it either way, so this costs the reviewer one glance.
  - A dummy "it" outside the cue list ("It remains an open question whether")
    is listed; the reviewer skips it.
  - A past participle used as an adjective after a demonstrative ("This limited
    scope") can be listed as a verb, and "the latter" as an adjective ("the
    latter half") is listed like the stand-in; the reviewer clears both.
  - First-mention definite articles (the third Reference rule) are not scanned:
    telling a first mention from an anaphoric "the" needs discourse tracking, and
    "the + noun + to/that" alone is too noisy to list.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_io import report_unreadable  # noqa: E402

KINDS = ('bare-demonstrative', 'such-noun', 'stand-in')

# Verbs that follow a bare demonstrative, by form. Third-person singular forms
# follow This / That / It; base forms follow These; past forms follow any.
VERBS_3SG = frozenset("""
shows suggests indicates means makes allows enables leads highlights underscores
reflects raises implies demonstrates confirms matters holds follows requires
reduces increases limits affects explains results poses introduces motivates
supports illustrates contrasts aligns echoes helps creates opens calls ensures
prevents causes gives provides offers yields points differs applies involves
corresponds seems appears remains becomes represents constitutes stems arises
occurs depends relies hinges turns comes goes works fails
is was has does did can could may might must shall should will would
""".split())
VERBS_BASE = frozenset("""
show suggest indicate mean make allow enable lead highlight underscore reflect
raise imply demonstrate confirm matter hold follow require reduce increase limit
affect explain result pose introduce motivate support illustrate contrast align
echo help create open call ensure prevent cause give provide offer yield point
differ apply involve correspond seem appear remain become represent constitute
stem arise occur depend rely hinge turn come go work fail
are were have do did can could may might must shall should will would
""".split())
VERBS_PAST = frozenset("""
showed suggested indicated meant made allowed enabled led highlighted underscored
reflected raised implied demonstrated confirmed mattered held followed required
reduced increased limited affected explained resulted posed introduced motivated
supported illustrated contrasted aligned echoed helped created opened called
ensured prevented caused gave provided offered yielded pointed differed applied
involved corresponded seemed appeared remained became represented constituted
stemmed arose occurred depended relied hinged turned came went worked failed
""".split())

# Adverbs that may sit between the pronoun and its verb ("This also shows",
# "This, in turn, makes"), and between a dummy "It is" and its cue ("It is also
# worth noting").
ADVERBS = (
    'also', 'thus', 'then', 'therefore', 'however', 'still', 'in turn', 'alone',
    'clearly', 'likely', 'partly', 'largely', 'mainly', 'often', 'only',
    'ultimately', 'directly', 'further', 'already', 'again', 'indeed', 'arguably',
    'certainly', 'perhaps', 'not', 'now', 'generally', 'widely', 'well', 'quite',
    'rather', 'very', 'entirely', 'hardly', 'no longer',
)
ADVERB_RE = '|'.join(re.escape(a) for a in ADVERBS)

# Words that mark an extraposition or weather "it" when they follow the verb:
# "It is possible that", "It is unclear whether", "It turns out", "It follows that".
DUMMY_IT_CUES = (
    'that', 'whether', 'to', 'out', 'possible', 'impossible', 'likely', 'unlikely',
    'clear', 'unclear', 'worth', 'important', 'necessary', 'essential', 'hard',
    'difficult', 'easy', 'plausible', 'tempting', 'reasonable', 'surprising',
    'unsurprising', 'notable', 'noteworthy', 'obvious', 'evident', 'true', 'false',
    'the case', 'no surprise', 'an open question', 'unknown', 'uncertain',
    'natural', 'common', 'rare', 'useful', 'helpful', 'instructive', 'interesting',
    'striking', 'remarkable', 'crucial', 'conceivable', 'doubtful', 'questionable',
    'known', 'well known', 'well-known', 'time', 'raining',
)
DUMMY_RE = re.compile(
    r'^(?:(?:' + ADVERB_RE + r'),?\s+)*(?:' + '|'.join(re.escape(c) for c in DUMMY_IT_CUES) + r')\b'
)

# A sentence start: line start (optionally a Markdown list marker or heading, or
# a LaTeX \item), or sentence-final punctuation plus any closing quote/bracket
# and whitespace. Then optional opening quotes/brackets, the pronoun, optional
# adverbs, and the candidate verb.
SENTENCE_START = (
    r'(?:^\s*(?:[-*+]\s+|\d+[.)]\s+|#+\s+)?|\\item\s+|[.!?;:]["\')\]]*\s+)'
)
DEMONSTRATIVE_RE = re.compile(
    SENTENCE_START
    + r'[(\["\'`]*'
    + r'(?P<pron>This|These|That|It)\b'
    + r'(?P<adv>(?:,?\s*(?:' + ADVERB_RE + r'),?)*)'
    + r'\s+(?P<verb>[A-Za-z]+)\b'
)
SUCH_RE = re.compile(r'\b(?P<such>[Ss]uch)\s+(?:an?\s+)?(?!as\b|that\b)[A-Za-z][\w-]*')
STAND_IN_RE = re.compile(
    r'\b(?P<standin>[Oo]nes|[Tt]he former|[Tt]he latter|[Rr]espectively|(?:[Dd]o|[Dd]oes|[Dd]id|[Dd]oing|[Dd]one) so'
    r'|[Tt]hose (?:of|that|which|with))\b'
)

LATEX_SKIP_ENVS = ('verbatim', 'lstlisting', 'minted', 'comment')
LATEX_BEGIN_RE = re.compile(r'\\begin\{(' + '|'.join(LATEX_SKIP_ENVS) + r')\*?\}')
LATEX_END_RE = re.compile(r'\\end\{(' + '|'.join(LATEX_SKIP_ENVS) + r')\*?\}')
LATEX_COMMENT_RE = re.compile(r'(?<!\\)%.*$')


def truncate(text, limit=120):
    """Collapse runs of whitespace in `text` and cap the result at `limit`
    characters, ending with '...' on truncation."""
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + '...'


def verb_fits(pron, verb):
    """True when `verb` is a listed form that agrees with `pron`."""
    if verb in VERBS_PAST:
        return True
    if pron == 'These':
        return verb in VERBS_BASE
    return verb in VERBS_3SG


def is_dummy_it(pron, verb, rest):
    """True for the listed extraposition frames ("It is possible that ...")."""
    if pron != 'It':
        return False
    return bool(DUMMY_RE.match(rest.lstrip()))


def is_connective(pron, verb, rest):
    """'That is,' and 'That said,' are connectives, not references."""
    if pron != 'That':
        return False
    if verb == 'said':
        return True
    return verb == 'is' and rest.lstrip().startswith((',', 'to say'))


def prose_lines(path, text):
    """Yield (line_idx, line, prose) for lines to scan, where `prose` is the
    line with any LaTeX comment removed. Skips fenced code and skip-listed LaTeX
    environments; `line` is the original for context and column numbers."""
    is_tex = Path(path).suffix.lower() == '.tex'
    in_fence = False
    in_env = False
    for idx, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if stripped.startswith('```') or stripped.startswith('~~~'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if is_tex:
            if in_env:
                if LATEX_END_RE.search(line):
                    in_env = False
                continue
            if LATEX_BEGIN_RE.search(line):
                in_env = True
                continue
            prose = LATEX_COMMENT_RE.sub('', line)
            if not prose.strip():
                continue
        else:
            prose = line
        yield idx, line, prose


def scan_file(path, stats):
    """Scan one file, print one TSV row per candidate to stdout, and update
    `stats` in place."""
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        report_unreadable(path, e)
        return
    stats['files'] += 1
    for line_idx, line, prose in prose_lines(path, text):
        rows = []
        for m in DEMONSTRATIVE_RE.finditer(prose):
            pron, verb, rest = m.group('pron'), m.group('verb'), prose[m.end():]
            if not verb_fits(pron, verb):
                continue
            if is_dummy_it(pron, verb, rest) or is_connective(pron, verb, rest):
                continue
            rows.append((m.start('pron'), 'bare-demonstrative'))
        for m in SUCH_RE.finditer(prose):
            rows.append((m.start('such'), 'such-noun'))
        for m in STAND_IN_RE.finditer(prose):
            rows.append((m.start('standin'), 'stand-in'))
        if not rows:
            continue
        context = truncate(line)
        for col, kind in sorted(rows):
            stats['counts'][kind] += 1
            print(f"{path}:{line_idx + 1}:{col + 1}\t{kind}\t{context}")


def main(argv):
    if len(argv) < 2:
        print("usage: scan_reference.py <file> [<file> ...]", file=sys.stderr)
        return 2
    stats = {'files': 0, 'counts': {k: 0 for k in KINDS}}
    paths = argv[1:]
    for path in paths:
        scan_file(path, stats)
    total = sum(stats['counts'].values())
    breakdown = ' '.join(f"{k}={stats['counts'][k]}" for k in KINDS)
    print(
        f"scanned {stats['files']} file(s); {total} reference candidate(s) [{breakdown}]",
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
