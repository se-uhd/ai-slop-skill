#!/usr/bin/env python3
"""find_citation_issues.py <texfile> [<texfile> ...]

Scan one or more LaTeX files for two deterministic citation issues and print
one tab-separated line per finding to stdout:

    <file>:<line>\\t<issue>\\t<keys>\\t<context>

Issues:
  - cluster:           a single \\cite-style call with three or more keys.
                       The rule asks for a per-work explanation. This only
                       flags the existence of the cluster. Judging whether
                       the surrounding prose explains each work is left to
                       the caller.
  - missing-grounding: a \\cite-style call with no `% GROUNDING:` comment on
                       the same line or on the next non-blank line.

Recognized commands (cluster + grounding checks apply):
  - natbib:   \\cite, \\citep, \\citet, \\citealp, \\citealt, \\citetext.
  - biblatex: \\parencite, \\textcite, \\autocite, \\fullcite, \\smartcite,
              \\footcite.
  - Capitalized variants of all of the above (\\Cite, \\Textcite, ...) are
    also matched.

Recognized but skipped (style-only helpers, typically paired with a grounded
cite nearby): \\citeauthor, \\citeyear, \\citeyearpar, \\citenum. Their
sentence-start capitalized variants (\\Citeauthor, \\Citeyear, ...) are
also matched and skipped.

Recognized and ignored entirely: \\nocite (BibTeX-only marker, not textual).

Other commands are not flagged. The recognized list is an allowlist.

Comment handling: lines whose code portion (before the first unescaped `%`)
contains no recognized cite call are skipped. Cite calls inside comments do
not count.

Always exits 0. Non-empty stdout signals that findings were emitted; an
empty stdout means no findings. A one-line summary is always printed to
stderr (e.g. `considered 41 cite call(s) across 1 file(s); 1 cluster(s),
41 missing-grounding`). "Considered" counts cite calls in
GROUNDED_COMMANDS that resolved to at least one parsed key. Calls in
SKIPPED_COMMANDS, IGNORED_COMMANDS, or with empty `{}` are excluded.

The `cluster` and `missing-grounding` counts are not disjoint. A cite with
three or more keys and no nearby grounding comment emits two stdout rows
(one of each kind) and increments both counters. The two should not be
summed. Both are subsets of `considered`, but a clean cite (one or two
keys, has grounding) still counts toward `considered` while contributing
to neither subset.

Known limitations:
  - Cite calls inside \\verb, listings, or other non-`%`-comment LaTeX
    constructs are still scanned. See find_latex_root.py for the same
    limitation.
  - \\input / \\include are not followed. Pass the full file list
    explicitly.
  - Multi-line cite calls (where `}` is on a different line from the
    opening `\\cite{`) are skipped silently. Restructure such calls onto a
    single logical line if you want them checked.
  - Multi-cite biblatex forms \\textcites / \\autocites / \\fullcites use
    multiple {key} groups. This script reads only the first group and
    undercounts keys.
  - "Nearby grounding" is defined as same line or the next non-blank line.
    A grounding comment placed two or more blank-separated lines after the
    cite is not credited.
"""
import re
import sys
from pathlib import Path

CITE_PATTERN = re.compile(
    r'\\([Cc]ite[a-zA-Z]*|[Pp]arencite|[Tt]extcite|[Aa]utocite'
    r'|[Ff]ullcite|[Ss]martcite|[Ff]ootcite|nocite)'
    r'\*?\s*(?:\[[^\]]*\])*\{([^}]*)\}'
)

# Cite calls that DO require a grounding comment and DO count toward the
# cluster check. Entries are stored lowercased. The regex captures both
# lower- and capitalized forms, and the lookup normalizes.
GROUNDED_COMMANDS = {
    'cite', 'citep', 'citet', 'citealp', 'citealt', 'citetext',
    'parencite', 'textcite', 'autocite', 'fullcite', 'smartcite', 'footcite',
}
# Style-only helpers, typically paired with a grounded cite nearby. Skip
# both the cluster and grounding checks for these.
SKIPPED_COMMANDS = {'citeauthor', 'citeyear', 'citeyearpar', 'citenum'}
# BibTeX-only marker, not a textual citation.
IGNORED_COMMANDS = {'nocite'}

CLUSTER_THRESHOLD = 3


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


def truncate(text, limit=120):
    """Collapse runs of whitespace in `text` and cap the result at `limit`
    characters, ending with '...' on truncation."""
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + '...'


def scan_file(path, stats):
    """Scan one .tex file for cite-cluster and missing-grounding findings,
    print one TSV row per finding to stdout, and update `stats` in place."""
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        print(f"{path}: {e}", file=sys.stderr)
        return
    stats['files'] += 1
    lines = text.splitlines()
    for idx, raw_line in enumerate(lines):
        code, comment = split_code_and_comment(raw_line)
        for match in CITE_PATTERN.finditer(code):
            command = match.group(1).lower()
            if command in IGNORED_COMMANDS:
                continue
            if command in SKIPPED_COMMANDS:
                continue
            if command not in GROUNDED_COMMANDS:
                continue  # allowlist miss, not a textual citation we check
            keys = parse_keys(match.group(2))
            if not keys:
                continue
            stats['considered'] += 1
            line_no = idx + 1
            context = truncate(raw_line)
            if len(keys) >= CLUSTER_THRESHOLD:
                stats['clusters'] += 1
                print(f"{path}:{line_no}\tcluster\t{','.join(keys)}\t{context}")
            if not has_grounding(lines, idx, comment):
                stats['missing_grounding'] += 1
                print(f"{path}:{line_no}\tmissing-grounding\t{','.join(keys)}\t{context}")


def main(argv):
    if len(argv) < 2:
        print("usage: find_citation_issues.py <texfile> [<texfile> ...]", file=sys.stderr)
        return 2
    stats = {'files': 0, 'considered': 0, 'clusters': 0, 'missing_grounding': 0}
    for path in argv[1:]:
        scan_file(path, stats)
    print(
        f"considered {stats['considered']} cite call(s) across {stats['files']} file(s); "
        f"{stats['clusters']} cluster(s), {stats['missing_grounding']} missing-grounding",
        file=sys.stderr,
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
