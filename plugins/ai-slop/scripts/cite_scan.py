#!/usr/bin/env python3
r"""cite_scan.py — shared LaTeX citation-scanning primitives.

find_citation_issues.py (flags clusters and missing `% GROUNDING:` comments) and
extract_cites.py (gathers per-source claims for grounding) scan the same
\cite-family macros. The regex, the command-classification sets, and the
comment/key/grounding helpers live here so the two tools agree on what counts as
a citation and neither re-implements the parsing.

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


def has_grounding(lines, idx, same_line_comment):
    """Return True if `% GROUNDING:` appears on the cite's same-line comment
    portion or on the next non-blank line (which must itself be a comment
    line)."""
    if 'GROUNDING:' in same_line_comment:
        return True
    j = idx + 1
    while j < len(lines):
        stripped = lines[j].strip()
        if not stripped:
            j += 1
            continue
        if stripped.startswith('%') and 'GROUNDING:' in stripped:
            return True
        return False
    return False


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
