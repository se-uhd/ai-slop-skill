#!/usr/bin/env python3
"""scan_glyphs.py <file> [<file> ...]

Deterministic recheck for the Unicode "tells" the writing rules flag
mechanically. The per-section review pass is an LLM eyeballing prose, and it
undercounts these glyphs: it will report "twelve em-dashes" when there are
fifteen, or miss one in a code comment. This scan is the ground truth. It reads
each file byte for byte and prints one tab-separated line per offending glyph to
stdout:

    <file>:<line>:<col>\\t<glyph-name>\\t<context>

`<col>` is the 1-based character column, so two em-dashes on one line produce two
distinct rows and the count is exact. `<context>` is the whole line, whitespace
collapsed and capped at 120 characters.

Glyph categories (the codepoint -> name map in GLYPHS is the authoritative list):

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

This is a CANDIDATE finder, not a verdict, exactly like find_citation_issues.py.
It flags every occurrence; the caller applies the documented exceptions before
reporting: an en-dash inside a range, any glyph inside quoted source material or
a code string/identifier, and the fact that an ASCII hyphen, `--`, or minus sign
is never matched (only the non-ASCII glyphs above are). The glyph in a *code
comment* is still a tell and is meant to be reported (the comment is prose).

A one-line summary is always printed to stderr, with a per-category breakdown:

    scanned 1 file(s); 15 Unicode tell(s) [em-dash=15 en-dash=0 arrow=0 \
curly-quote=0 ellipsis=0 nbsp=0]

Exits 0 when at least one input file was read, whether or not glyphs were found.
Exits 2 on a usage error: no arguments, or none of the given paths could be read
(nothing was scanned). The exit-2 case guards the same shell-quoting mishap as
the citation scanner — a whole file list collapsed into one unreadable argument,
which would otherwise look like a clean "no tells" run. Non-empty stdout signals
findings; empty stdout means none.

Known limitations:
  - No format awareness. The scan does not parse Markdown fences, LaTeX verbatim,
    or string literals, so a glyph inside fenced code or a quoted string is still
    emitted; the `<context>` line lets the caller judge. (This is deliberate: a
    literal em-dash in a code *comment* must be caught, and distinguishing a
    comment from a string per language is the extractor's job, not this scan's.)
  - splitlines() consumes the Unicode line separators U+2028/U+2029 and U+0085, so
    a glyph that is itself a line separator is not reported as content.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_io import report_unreadable  # noqa: E402

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

# Display order for the stderr breakdown; every category in GLYPHS appears once.
CATEGORIES = ('em-dash', 'en-dash', 'arrow', 'curly-quote', 'ellipsis', 'nbsp')


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
        f"scanned {stats['files']} file(s); {total} Unicode tell(s) [{breakdown}]",
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
