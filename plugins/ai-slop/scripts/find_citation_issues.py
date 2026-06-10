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
  - missing-grounding: a \\cite-style call with no grounding comment attached —
                       on the same line or in the contiguous run of blank and
                       `%`-comment lines directly below it. A grounding comment
                       leads with the GROUNDING marker in any key-placement form
                       (`% GROUNDING: "..."`, `% GROUNDING: <key> -- "..."`, or
                       `% GROUNDING <key>: "..."`); see cite_scan.py. A quote-less
                       `TODO verify` stub also counts as attached (the cite is
                       marked, not missing) — filling stubs is insert_grounding's
                       job, not a finding here.

Recognized commands (cluster + grounding checks apply):
  - natbib:   \\cite, \\citep, \\citet, \\citealp, \\citealt, \\citetext.
  - biblatex: \\parencite, \\textcite, \\autocite, \\fullcite, \\smartcite,
              \\footcite, and their plural multi-cite forms (\\cites,
              \\parencites, \\textcites, ...; only the first key group is read).
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

Exits 0 when at least one input file was read, whether or not findings were
emitted. Exits 2 on a usage error: no arguments, or none of the given paths
could be read (nothing was scanned). The exit-2 case guards against a shell
mishap that collapses the whole file list into one unreadable argument — in
zsh, an unquoted variable is not word-split — which would otherwise look like
a clean "no findings" run. Non-empty stdout signals that findings were
emitted; an empty stdout means no findings. A one-line summary is always
printed to stderr (e.g. `considered 41 cite call(s) across 1 file(s);
1 cluster(s), 41 missing-grounding`). "Considered" counts cite calls in
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
  - "Nearby grounding" is the cite's attached comment block: the same line
    plus the contiguous run of blank and `%`-comment lines below it. The
    first code line ends the block, so a grounding comment placed after
    intervening code or prose is not credited. Blank lines and unrelated
    `%` comments inside the block are skipped over. The marker is matched
    in any key-placement form (`% GROUNDING:`, `% GROUNDING: <key>`, or
    `% GROUNDING <key>:`).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_scan import has_grounding, iter_cite_calls  # noqa: E402
from scan_io import report_unreadable  # noqa: E402

# The cite regex, command-classification sets, and the comment/key/grounding
# helpers live in cite_scan.py, shared with extract_cites.py.

CLUSTER_THRESHOLD = 3


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
        report_unreadable(path, e)
        return
    stats['files'] += 1
    lines = text.splitlines()
    for idx, command, keys, comment, raw_line in iter_cite_calls(lines):
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
    paths = argv[1:]
    for path in paths:
        scan_file(path, stats)
    print(
        f"considered {stats['considered']} cite call(s) across {stats['files']} file(s); "
        f"{stats['clusters']} cluster(s), {stats['missing_grounding']} missing-grounding",
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
