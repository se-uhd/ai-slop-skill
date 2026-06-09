#!/usr/bin/env python3
"""check_bib_fields.py <bibfile> [<bibfile> ...]

For each .bib file, find entries with missing required fields per the standard
BibTeX spec and print one tab-separated line per offending entry to stdout:

    <key>\\t<type>\\t<comma-separated-missing-fields>

Empty stdout means all parsed entries are clean. A one-line summary is always
printed to stderr (e.g. `checked 142 entries across 1 file(s), 0 missing-field
issue(s)`) so callers can confirm the run completed without parsing stdout.
Files that cannot be opened or entries that cannot be parsed are reported on
stderr but do not abort the run, as long as at least one file is read. The
script exits 2 on a usage error: no arguments, or none of the given paths
could be read (so nothing was checked) — this keeps a shell mishap that
collapses the file list into one unreadable argument from masquerading as a
clean run. Otherwise it exits 0.

Required-fields table is taken from Patashnik's btxdoc, the canonical BibTeX
manual on CTAN: https://mirrors.ctan.org/biblio/bibtex/base/btxdoc.tex

Notes:
  - 'editor' substitutes for 'author' on @book and @inbook (per spec). For
    @incollection / @inproceedings / @proceedings, 'editor' is optional
    alongside (not a substitute for) the required author/title fields.
  - @inbook requires 'chapter' and/or 'pages' (at least one).
  - @conference is treated as an alias of @inproceedings (Scribe-compat
    entry per btxdoc).
  - Unknown entry types are silently skipped — this avoids false positives
    on BibLaTeX-style entries (@online, @dataset, @software, @thesis,
    @report) whose required-field rules are not modeled here.
  - 'crossref' inheritance is NOT honored; an @inproceedings that
    legitimately inherits 'booktitle' from a referenced @proceedings will be
    flagged. Sanity-check flagged entries.
  - Assumes BibTeX keys contain no tabs (true in practice).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bib_parse import find_entry_blocks, parse_entry, SKIP_TYPES  # noqa: E402
from scan_io import report_unreadable  # noqa: E402

# Required-fields table from Patashnik's btxdoc (the canonical BibTeX manual):
# https://mirrors.ctan.org/biblio/bibtex/base/btxdoc.tex
# Update this table only against btxdoc, not by guessing or copying from BibLaTeX
# docs (BibLaTeX has different rules; see the module docstring).
REQUIRED = {
    'article':       ['author', 'title', 'journal', 'year'],
    'book':          ['title', 'publisher', 'year'],   # author OR editor handled separately
    'booklet':       ['title'],
    'inbook':        ['title', 'publisher', 'year'],   # author OR editor + chapter/pages handled separately
    'incollection':  ['author', 'title', 'booktitle', 'publisher', 'year'],
    'inproceedings': ['author', 'title', 'booktitle', 'year'],
    'conference':    ['author', 'title', 'booktitle', 'year'],   # btxdoc: alias of @inproceedings (Scribe-compat)
    'manual':        ['title'],
    'mastersthesis': ['author', 'title', 'school', 'year'],
    'misc':          [],   # btxdoc: no required fields
    'phdthesis':     ['author', 'title', 'school', 'year'],
    'proceedings':   ['title', 'year'],
    'techreport':    ['author', 'title', 'institution', 'year'],
    'unpublished':   ['author', 'title', 'note'],
}

# Entry splitting (find_entry_blocks), the field-name parser (parse_entry), and
# SKIP_TYPES live in bib_parse.py, shared with verify_references.py and
# extract_cites.py.


def missing_fields(etype, fields):
    """Return sorted list of missing required field names, or None if etype
    is not in the standard BibTeX table (caller skips unknown types)."""
    if etype not in REQUIRED:
        return None
    missing = {f for f in REQUIRED[etype] if f not in fields}
    if etype in ('book', 'inbook'):
        if 'author' not in fields and 'editor' not in fields:
            missing.add('author')
    if etype == 'inbook':
        if 'chapter' not in fields and 'pages' not in fields:
            missing.add('chapter')
    return sorted(missing)


def check_file(path, stats):
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        report_unreadable(path, e)
        return
    stats['files'] += 1
    try:
        entries = list(find_entry_blocks(text))
    except ValueError as e:
        print(f"{path}: {e}", file=sys.stderr)
        return
    for etype, body in entries:
        if etype in SKIP_TYPES:
            continue
        try:
            key, fields = parse_entry(body)
        except Exception as e:
            print(f"{path}: parse error in @{etype}: {e}", file=sys.stderr)
            continue
        missing = missing_fields(etype, fields)
        if missing is None:
            continue  # unknown entry type — silently skip
        stats['checked'] += 1
        if missing:
            stats['flagged'] += 1
            print(f"{key}\t{etype}\t{','.join(missing)}")


def main(argv):
    if len(argv) < 2:
        print("usage: check_bib_fields.py <bibfile> [<bibfile> ...]", file=sys.stderr)
        return 2
    stats = {'files': 0, 'checked': 0, 'flagged': 0}
    paths = argv[1:]
    for path in paths:
        check_file(path, stats)
    print(
        f"checked {stats['checked']} entries across {stats['files']} file(s), "
        f"{stats['flagged']} missing-field issue(s)",
        file=sys.stderr,
    )
    if stats['files'] == 0:
        print(
            f"error: none of the {len(paths)} path(s) given could be read; nothing was checked",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
