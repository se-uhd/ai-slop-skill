#!/usr/bin/env python3
"""scan_glyphs.py <file> [<file> ...]

Deterministic recheck for the Unicode and ASCII dash "tells" the writing rules flag
mechanically. The per-section review pass is an LLM reading prose, and it
undercounts these glyphs: it will report "twelve em-dashes" when there are
fifteen, or miss one in a code comment. This scan is the ground truth. It reads
each file byte for byte and prints one tab-separated line per offending glyph to
stdout:

    <file>:<line>:<col>\\t<glyph-name>\\t<context>

`<col>` is the 1-based character column, so two em-dashes on one line produce two
distinct rows and the count is exact. `<context>` is the whole line, whitespace
collapsed and capped at 120 characters.

Categories (the codepoint -> name map in GLYPHS and the ASCII_DASH patterns are
the authoritative lists):

  - em-dash:     U+2014 (—). An editor never autocorrects `-`/`--` into `—`, so a
                 literal one in code-edited Markdown, plain text, a comment, or
                 `.tex` is a tell. Replace with the format's ASCII form (`:`, a
                 comma, a period, or `---` in LaTeX).
  - en-dash:     U+2013 (–). A tell as a `term – gloss` separator, but legitimate
                 in a numeric or page range (`pp. 12–18`); the caller judges.
  - arrow:       U+2192 → and the rest of the family (← ↔ ⇒ ⇐ ⇔). "Claude loves
                 the -> arrow"; real writers type `->`.
  - curly-quote: U+2018/2019/201C/201D and the low-9 variants (‚ „). A text editor
                 produces straight quotes; smart quotes are pasted in.
  - ellipsis:    U+2026 (…). Typed as `...`.
  - nbsp:        U+00A0, a non-breaking space. Typed as a normal space (or `~` in
                 LaTeX); a literal one is a paste artifact.
  - ascii-dash:  `--` and `---` doing a dash's work: spaced (` -- `), unspaced
                 between letters (`word--word`), or LaTeX's `---`. The general
                 layer counts the dash, not the character, so rewriting `—` as
                 `--` is not a fix and these count toward the same density
                 signal. Not matched: a command-line flag (`--fix`), a numeric
                 range (`12--18`), a table separator or thematic break, a run of
                 four or more dashes (a comment banner or rule), a fenced
                 block, the contents of an inline code span, and, in a `.tex`
                 file, anything after an unescaped `%`, so the ` -- ` separator
                 in the bundle's own `% GROUNDING:` comments never counts.

This scan is a CANDIDATE finder, not a verdict, exactly like find_citation_issues.py.
It flags every occurrence; the caller applies the documented exceptions before
reporting: an en-dash inside a range, any glyph inside quoted source material or
a code string/identifier, and a lone ASCII hyphen or minus sign, which is never
matched. The glyph in a *code comment* is still a tell and is meant to be
reported (the comment is prose).

A one-line summary is always printed to stderr, with a per-category breakdown:

    scanned 1 file(s); 15 tell(s) [em-dash=15 ascii-dash=0 en-dash=0 arrow=0 \
curly-quote=0 ellipsis=0 nbsp=0]

Exits 0 when at least one input file was read, whether or not glyphs were found.
Exits 2 on a usage error: no arguments, or none of the given paths could be read
(nothing was scanned). The exit-2 case guards the same shell-quoting mishap as
the citation scanner, namely a whole file list collapsed into one unreadable argument,
which would otherwise look like a clean "no tells" run. Non-empty stdout signals
findings; empty stdout means none.

Known limitations:
  - No format awareness for the Unicode glyphs. The scan does not parse Markdown
    fences, LaTeX verbatim, or string literals, so a glyph inside fenced code or a
    quoted string is still emitted; the `<context>` line lets the caller judge.
    (The omission is deliberate: a literal em-dash in a code *comment* must be
    caught, and distinguishing a comment from a string per language is the
    extractor's job, not this scan's.) The ASCII dash pass is the exception: it
    skips fenced blocks (nesting honored), inline code spans, and LaTeX
    comments, because `--` is ordinary syntax there and the false-positive rate
    would swamp the signal.
  - splitlines() consumes the Unicode line separators U+2028/U+2029 and U+0085, so
    a glyph that is itself a line separator is not reported as content.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_io import FenceTracker, report_unreadable  # noqa: E402

# Codepoint -> category name. Adding a glyph is a one-line edit here; the stderr
# breakdown and the smoke tests read the category names from CATEGORIES below.
GLYPHS = {
    '—': 'em-dash',
    '–': 'en-dash',
    '→': 'arrow', '←': 'arrow', '↔': 'arrow',
    '⇒': 'arrow', '⇐': 'arrow', '⇔': 'arrow',
    '‘': 'curly-quote', '’': 'curly-quote',
    '“': 'curly-quote', '”': 'curly-quote',
    '‚': 'curly-quote', '„': 'curly-quote',
    '…': 'ellipsis',
    ' ': 'nbsp',
}

# ASCII sequences doing a dash's work. A command-line flag (`--fix`) fails both
# the spaced and the letter-letter test, a numeric range (`12--18`) fails the
# letter-letter test, and a run of four or more dashes is a banner or rule, so
# none of those is matched.
ASCII_DASH = (
    re.compile(r'(?<!-)-{3}(?!-)'),
    re.compile(r'(?<=\s)--(?=\s)'),
    re.compile(r'(?<=[A-Za-z])--(?=[A-Za-z])'),
)
SEPARATOR_LINE = re.compile(r'^[\s|:+-]+$')
CODE_SPAN = re.compile(r'`[^`]*`')
TEX_COMMENT = re.compile(r'(?<!\\)%.*$')

# Display order for the stderr breakdown; every category appears once.
CATEGORIES = ('em-dash', 'ascii-dash', 'en-dash', 'arrow', 'curly-quote',
              'ellipsis', 'nbsp')


def truncate(text, limit=120):
    """Collapse runs of whitespace in `text` and cap the result at `limit`
    characters, ending with '...' on truncation."""
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + '...'


def scan_file(path, stats):
    """Scan one file for Unicode-glyph tells, print one TSV row per occurrence
    to stdout, and update `stats` in place."""
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        report_unreadable(path, e)
        return
    stats['files'] += 1
    is_tex = Path(path).suffix.lower() == '.tex'
    fences = FenceTracker()
    for line_idx, line in enumerate(text.splitlines()):
        context = None
        for col_idx, ch in enumerate(line):
            name = GLYPHS.get(ch)
            if name is None:
                continue
            if context is None:
                context = truncate(line)
            stats['counts'][name] += 1
            print(f"{path}:{line_idx + 1}:{col_idx + 1}\t{name}\t{context}")
        if fences.feed(line) or SEPARATOR_LINE.match(line):
            continue
        prose = TEX_COMMENT.sub('', line) if is_tex else line
        masked = CODE_SPAN.sub(lambda m: ' ' * len(m.group(0)), prose)
        cols = sorted({m.start() for pat in ASCII_DASH for m in pat.finditer(masked)})
        for col_idx in cols:
            if context is None:
                context = truncate(line)
            stats['counts']['ascii-dash'] += 1
            print(f"{path}:{line_idx + 1}:{col_idx + 1}\tascii-dash\t{context}")


def main(argv):
    if len(argv) < 2:
        print("usage: scan_glyphs.py <file> [<file> ...]", file=sys.stderr)
        return 2
    stats = {'files': 0, 'counts': {c: 0 for c in CATEGORIES}}
    paths = argv[1:]
    for path in paths:
        scan_file(path, stats)
    total = sum(stats['counts'].values())
    breakdown = ' '.join(f"{c}={stats['counts'][c]}" for c in CATEGORIES)
    print(
        f"scanned {stats['files']} file(s); {total} tell(s) [{breakdown}]",
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
