#!/usr/bin/env python3
"""find_citation_issues.py <texfile> [<texfile> ...]

Scan one or more LaTeX files for two deterministic citation issues and print
one tab-separated line per finding to stdout:

    <file>:<line>\\t<issue>\\t<keys>\\t<context>

Issues:
  - cluster:           a single \\cite{...} call with three or more keys
                       (the rule asks for a per-work explanation; this only
                       flags the existence of the cluster — judging whether
                       the surrounding prose explains each work is left to
                       the caller).
  - missing-grounding: a \\cite{} call with no `% GROUNDING:` comment on the
                       same line or on the next non-blank line.

Recognised cite commands (cluster + grounding): \\cite, \\citep, \\citet,
\\citealp, \\citealt, \\fullcite, \\textcite, \\autocite. The author/year-only
helpers \\citeauthor, \\citeyear, \\citeyearpar, \\citenum are recognised for
completeness but skip both checks (they are style-only and typically paired
with one of the textual cites above). \\nocite is ignored entirely.

Comment handling: lines whose code portion (before the first unescaped `%`)
contains no cite call are skipped. \\cite calls inside comments do not count.

Always exits 0; non-empty stdout is the signal. A one-line summary is always
printed to stderr (e.g. `scanned 41 cite call(s) across 1 file(s); 1 cluster(s),
41 missing-grounding`).

Known limitations:
  - Cite calls inside \\verb, listings, or other non-`%`-comment LaTeX
    constructs are still scanned (rare in paper bodies; matches the
    behaviour of find_latex_root.py).
  - \\input / \\include are not followed; pass the full file list explicitly.
  - "Nearby grounding" is defined as same line or the next non-blank line.
    A grounding comment placed two or more blank-separated lines after the
    cite is not credited.
"""
import re
import sys
from pathlib import Path

CITE_PATTERN = re.compile(
    r'\\cite([a-zA-Z]*)(?:\[[^\]]*\])*\{([^}]*)\}'
)

# Cite-command suffixes that DO require a grounding comment and count toward
# the cluster check. The empty string corresponds to bare \cite{}.
GROUNDED_SUFFIXES = {
    '', 'p', 't', 'alp', 'alt', 'paren', 'num',
    'fullcite', 'textcite', 'autocite',
}
# Recognised but skipped: style-only helpers that don't need their own
# grounding comment (typically paired with a grounded cite nearby).
SKIPPED_SUFFIXES = {'author', 'year', 'yearpar', 'authors'}
# \nocite is BibTeX-only (not a textual citation).
IGNORED_SUFFIXES = {'no'}

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
    """True iff `% GROUNDING:` appears on the same line's comment portion or
    on the next non-blank line (which must itself be a comment line)."""
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
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + '…'


def scan_file(path, stats):
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
            suffix = match.group(1).lower()
            if suffix in IGNORED_SUFFIXES or suffix in SKIPPED_SUFFIXES:
                continue
            if suffix not in GROUNDED_SUFFIXES:
                # Unknown \citeXxx — be conservative: still count it.
                pass
            keys = parse_keys(match.group(2))
            if not keys:
                continue
            stats['cites'] += 1
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
    stats = {'files': 0, 'cites': 0, 'clusters': 0, 'missing_grounding': 0}
    for path in argv[1:]:
        scan_file(path, stats)
    print(
        f"scanned {stats['cites']} cite call(s) across {stats['files']} file(s); "
        f"{stats['clusters']} cluster(s), {stats['missing_grounding']} missing-grounding",
        file=sys.stderr,
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
