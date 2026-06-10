#!/usr/bin/env python3
r"""cite_scan.py — shared LaTeX citation-scanning primitives.

find_citation_issues.py (flags clusters and missing grounding comments) and
extract_cites.py (gathers per-source claims for grounding) scan the same
\cite-family macros. The regex, the command-classification sets, and the
comment/key/grounding helpers live here so the two tools agree on what counts as
a citation and neither re-implements the parsing.

Grounding-comment forms recognized by has_grounding / is_grounding_comment:
  - `% GROUNDING: "<quote>"`            marker then quote
  - `% GROUNDING: <key> -- "<quote>"`   the form insert_grounding.py writes
  - `% GROUNDING <key>: "<quote>"`      the key named before the colon, common
                                        when one sentence cites several keys and
                                        each is grounded on its own comment line
A grounding comment is any `%` comment whose first word is the GROUNDING marker;
the key placement and the colon position do not matter.

Quote-less grounding comments are TODO stubs — `% GROUNDING: TODO verify <key>`
(planted by revise mode) or `% GROUNDING: <key> -- TODO verify -- <reason>`
(written by insert_grounding.py when a source could not be retrieved). They
count as grounding comments for is_grounding_comment / has_grounding (the cite
is marked, not missing), but grounding_quality classifies them 'todo' rather
than 'quote', so a grounding run can still pick the site up and fill the quote.

A comment "belongs" to a cite when it sits on the cite's own line or in the
contiguous run of blank and `%`-comment lines directly below it; the first code
line ends that block. iter_comment_block is the single walker for this — the
read side (has_grounding / grounding_quality, used by find_citation_issues.py
and extract_cites.py) and the write side (insert_grounding.py) both use it, so
they cannot drift on which comments count.

Recognized commands:
  - natbib:   \cite, \citep, \citet, \citealp, \citealt, \citetext.
  - biblatex: \parencite, \textcite, \autocite, \fullcite, \smartcite,
              \footcite, and their plural multi-cite forms (\cites,
              \parencites, \textcites, \autocites, \fullcites, \smartcites,
              \footcites).
  - style-only helpers (typically paired with a grounded cite nearby):
              \citeauthor, \citeyear, \citeyearpar, \citenum.
  - \nocite is a BibTeX-only print marker, ignored entirely.

Capitalized sentence-start variants (\Cite, \Textcite, \Citeauthor, ...) are
matched too; the command is lowercased before any set lookup.

Limitations inherited by both callers:
  - Plural multi-cite forms (\textcites, \autocites, ...) use several {key}
    groups; only the first group is read, so their keys are undercounted.
  - Cite calls inside \verb, listings, or other non-`%`-comment constructs are
    still scanned (only `%` comments are stripped).
"""
import re

CITE_PATTERN = re.compile(
    r'\\([Cc]ite[a-zA-Z]*|[Pp]arencites?|[Tt]extcites?|[Aa]utocites?'
    r'|[Ff]ullcites?|[Ss]martcites?|[Ff]ootcites?|nocite)'
    r'\*?\s*(?:\[[^\]]*\])*\{([^}]*)\}'
)

# Cite calls that DO require a grounding comment and DO count toward the cluster
# check. Stored lowercased; the regex captures both lower- and capitalized forms
# and the lookup normalizes. The plural multi-cite forms (cites, parencites, ...)
# are included; only their first key group is read (see Limitations above).
GROUNDED_COMMANDS = {
    'cite', 'citep', 'citet', 'citealp', 'citealt', 'citetext', 'cites',
    'parencite', 'textcite', 'autocite', 'fullcite', 'smartcite', 'footcite',
    'parencites', 'textcites', 'autocites', 'fullcites', 'smartcites', 'footcites',
}
# Style-only helpers, typically paired with a grounded cite nearby. The cluster
# and missing-grounding checks skip these, but they still name a source, so
# extract_cites gathers the claims around them.
SKIPPED_COMMANDS = {'citeauthor', 'citeyear', 'citeyearpar', 'citenum'}
# BibTeX-only marker, not a textual citation.
IGNORED_COMMANDS = {'nocite'}
# Every command that names a bibliography key in running text (grounded plus
# style-only). \nocite is excluded — it prints nothing.
CITATION_COMMANDS = GROUNDED_COMMANDS | SKIPPED_COMMANDS


# A grounding comment leads with the GROUNDING marker. The key (if named) may
# sit either after the colon (`% GROUNDING: <key> -- ...`) or before it
# (`% GROUNDING <key>: ...`); detection only needs the leading marker word, so
# neither the colon position nor the presence of a key matters here. Anchored at
# the start of the comment (after the `%`), so a stray lowercase "grounding"
# mention inside a prose comment is not mistaken for the marker.
GROUNDING_MARKER = re.compile(r'%+\s*GROUNDING\b')


def is_grounding_comment(comment):
    """True if `comment` (a string beginning with `%`) leads with the GROUNDING
    marker, in any of the recognized key-placement forms (see module docstring).
    An empty string or a non-grounding comment returns False."""
    return GROUNDING_MARKER.match(comment.lstrip()) is not None


def split_code_and_comment(line):
    """Return (code, comment) splitting at the first unescaped `%`."""
    i = 0
    n = len(line)
    while i < n:
        if line[i] == '\\' and i + 1 < n:
            i += 2
            continue
        if line[i] == '%':
            return line[:i], line[i:]
        i += 1
    return line, ''


def parse_keys(key_blob):
    """Split a `{a, b, c}` cite payload into a list of keys, dropping empties."""
    return [k.strip() for k in key_blob.split(',') if k.strip()]


def iter_comment_block(lines, idx, same_line_comment):
    """Yield (line_index, comment_text) for every comment attached to the cite
    on line `idx`: the same-line comment portion first (with index `idx`), then
    each `%` comment line in the contiguous run of blank or comment lines that
    follows. The first non-blank, non-comment line ends the block, so a
    grounding comment beyond intervening code or prose is not associated with
    the cite. This is the single definition of "attached" shared by the read
    side (has_grounding / grounding_quality) and the write side
    (insert_grounding.already_grounded), so the two cannot drift."""
    if same_line_comment and same_line_comment.strip():
        yield idx, same_line_comment
    j = idx + 1
    while j < len(lines):
        stripped = lines[j].strip()
        if not stripped:
            j += 1
            continue
        if not stripped.startswith('%'):
            break
        yield j, stripped
        j += 1


def is_quote_grounding(comment):
    """True if `comment` is a grounding comment carrying a quote (a
    double-quoted segment) — a completed grounding, as opposed to a quote-less
    `TODO verify` stub, which records that the quote is still owed."""
    return is_grounding_comment(comment) and '"' in comment


def grounding_quality(lines, idx, same_line_comment):
    """Classify the grounding state of the cite on line `idx`:
    'quote' — a grounding comment carrying a quote is attached;
    'todo'  — only quote-less grounding comments (TODO stubs) are attached;
    'none'  — no grounding comment at all."""
    state = 'none'
    for _, text in iter_comment_block(lines, idx, same_line_comment):
        if is_quote_grounding(text):
            return 'quote'
        if is_grounding_comment(text):
            state = 'todo'
    return state


def has_grounding(lines, idx, same_line_comment):
    """Return True if a grounding comment (quote-backed or TODO stub, any form
    recognized by is_grounding_comment) is attached to the cite on line `idx` —
    on its own line or in the contiguous blank/comment block below it. Other
    `%` comments in between do not break the association; the first code line
    does."""
    return grounding_quality(lines, idx, same_line_comment) != 'none'


def iter_cite_calls(lines):
    """Yield (line_index, command, keys, comment, raw_line) for every grounded
    textual cite call across `lines`.

    Comments are stripped before scanning, so a cite inside a `%` comment does
    not count. Style-only helpers (SKIPPED_COMMANDS), the \\nocite marker
    (IGNORED_COMMANDS), commands outside the allowlist, and calls whose `{}`
    parses to zero keys are all filtered out — the yielded set is exactly
    find_citation_issues' "considered" set (GROUNDED_COMMANDS resolving to at
    least one key)."""
    for idx, raw_line in enumerate(lines):
        code, comment = split_code_and_comment(raw_line)
        for match in CITE_PATTERN.finditer(code):
            command = match.group(1).lower()
            if command in IGNORED_COMMANDS or command in SKIPPED_COMMANDS:
                continue
            if command not in GROUNDED_COMMANDS:
                continue
            keys = parse_keys(match.group(2))
            if not keys:
                continue
            yield idx, command, keys, comment, raw_line
