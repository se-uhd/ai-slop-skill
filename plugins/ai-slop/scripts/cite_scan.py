#!/usr/bin/env python3
r"""cite_scan.py: shared LaTeX citation-scanning primitives.

find_citation_issues.py (flags clusters and missing grounding comments) and
extract_cites.py (gathers per-source claims for grounding) scan the same
\cite-family macros. The regex, the command-classification sets, the
comment/key/grounding helpers, the cite-call scanner, and the \input /
\include walker are defined here so the two tools agree on what counts as a
citation, see the same set of files and calls, and neither re-implements the
parsing.

The scanner (`scan_cite_calls` / `iter_cite_calls`) works on the
comment-stripped lines joined with newlines, so a call whose key list spans
lines (`\cite{a,` / `  b}`) is found and reported with the line it starts on
and the line it ends on. Grounding comments attach to the last line of the
call, since that is where a comment below the cite sits.

Grounding-comment forms recognized by has_grounding / is_grounding_comment:
  - `% GROUNDING: "<quote>"`            marker then quote
  - `% GROUNDING: <key> -- "<quote>"`   the form insert_grounding.py writes
  - `% GROUNDING <key>: "<quote>"`      the key named before the colon, common
                                        when one sentence cites several keys and
                                        each is grounded on its own comment line
A grounding comment is any `%` comment with the GROUNDING marker as its first
word. The key placement and the colon position do not matter.

Quote-less grounding comments are TODO stubs: `% GROUNDING: TODO verify <key>`
(planted by revise mode) or `% GROUNDING: <key> -- TODO verify -- <reason>`
(written by insert_grounding.py when a source could not be retrieved). They
count as grounding comments for is_grounding_comment / has_grounding (the cite
is marked, not missing), but grounding_quality classifies them 'todo' rather
than 'quote', so a grounding run can still pick the site up and fill the quote.

A comment "belongs" to a cite when it sits on the cite's own line or in the
contiguous run of blank and `%`-comment lines directly below it; the first code
line ends that block. iter_comment_block is the single walker for this block. The
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
import bisect
import re
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_io import report_unreadable  # noqa: E402

INPUT_PATTERN = re.compile(r'\\(?:input|include)\s*\{([^}]+)\}')

# One recognized cite call. `start` and `end` are the 0-based indices of the
# first and last line the call spans (equal for the usual one-line call), `pos`
# is the offset of the call in the joined code text (see joined_code), and
# `command` is lowercased.
CiteCall = namedtuple('CiteCall', 'start end pos command keys')

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
# style-only). \nocite is excluded because it prints nothing.
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
    the cite. This function is the single definition of "attached" shared by the read
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
    double-quoted segment), that is, a completed grounding, as opposed to a quote-less
    `TODO verify` stub, which records that the quote is still owed."""
    return is_grounding_comment(comment) and '"' in comment


def grounding_quality(lines, idx, same_line_comment):
    """Classify the grounding state of the cite on line `idx`:
    'quote': a grounding comment carrying a quote is attached;
    'todo':  only quote-less grounding comments (TODO stubs) are attached;
    'none':  no grounding comment at all."""
    state = 'none'
    for _, text in iter_comment_block(lines, idx, same_line_comment):
        if is_quote_grounding(text):
            return 'quote'
        if is_grounding_comment(text):
            state = 'todo'
    return state


def has_grounding(lines, idx, same_line_comment):
    """Return True if a grounding comment (quote-backed or TODO stub, any form
    recognized by is_grounding_comment) is attached to the cite on line `idx`,
    either on its own line or in the contiguous blank/comment block below it.
    Other `%` comments in between do not break the association; the first
    code line does."""
    return grounding_quality(lines, idx, same_line_comment) != 'none'


def joined_code(lines):
    """Return (joined, line_starts): the comment-stripped lines joined with
    newlines, and the offset at which each line begins in that text, so a match
    offset maps back to a line index with bisect."""
    code_lines = [split_code_and_comment(line)[0] for line in lines]
    line_starts = []
    pos = 0
    for code in code_lines:
        line_starts.append(pos)
        pos += len(code) + 1  # +1 for the newline the join inserts
    return '\n'.join(code_lines), line_starts


def scan_cite_calls(lines, commands=GROUNDED_COMMANDS):
    """Return (joined, calls): the joined code text (for sentence splitting) and
    a CiteCall per recognized cite call whose command is in `commands` and that
    resolves to at least one key. The scan runs over the comment-stripped,
    line-joined text, so a cite inside a `%` comment does not count and a call
    whose braces span lines is found. With the default `commands`, the calls
    are exactly find_citation_issues' "considered" set: GROUNDED_COMMANDS
    resolving to at least one key, with the style-only helpers
    (SKIPPED_COMMANDS) and \\nocite (IGNORED_COMMANDS) left out."""
    joined, starts = joined_code(lines)
    calls = []
    for match in CITE_PATTERN.finditer(joined):
        command = match.group(1).lower()
        if command in IGNORED_COMMANDS or command not in commands:
            continue
        keys = parse_keys(match.group(2))
        if not keys:
            continue
        start = bisect.bisect_right(starts, match.start()) - 1
        end = bisect.bisect_right(starts, match.end() - 1) - 1
        calls.append(CiteCall(start, end, match.start(), command, keys))
    return joined, calls


def iter_cite_calls(lines):
    """Yield a CiteCall for every grounded textual cite call in `lines` (see
    scan_cite_calls for what is included)."""
    return iter(scan_cite_calls(lines)[1])


def resolve_ref(ref, including_dir, base, suffix):
    """Resolve an \\input / \\bibliography reference to an existing file, trying
    the main-file directory then the including file's directory, with and
    without the given suffix (LaTeX adds it when absent)."""
    names = [ref] if ref.lower().endswith(suffix) else [ref + suffix, ref]
    for d in (base, including_dir):
        for name in names:
            cand = d / name
            if cand.is_file():
                return cand
    return None


def gather_files(root, seen=None):
    """Return [(path, text)] for `root` plus every file it transitively pulls
    in with \\input / \\include, depth-first and de-duplicated. Include
    directives inside `%` comments are ignored. `seen` is an optional set of
    resolved paths already gathered (shared across several roots), which is
    updated in place so a file reached twice is read once."""
    root = Path(root)
    base = root.resolve().parent
    if seen is None:
        seen = set()
    order = []

    def visit(path):
        rp = path.resolve()
        if rp in seen:
            return
        seen.add(rp)
        try:
            text = rp.read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            report_unreadable(path, e)
            return
        order.append((rp, text))
        for raw_line in text.splitlines():
            code, _ = split_code_and_comment(raw_line)
            for m in INPUT_PATTERN.finditer(code):
                child = resolve_ref(m.group(1).strip(), rp.parent, base, '.tex')
                if child:
                    visit(child)

    visit(root)
    return order
