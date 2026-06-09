#!/usr/bin/env python3
"""scan_io.py — shared command-line I/O helpers for the ai-slop scanners.

`report_unreadable` is the stderr warning emitted when a path passed on the
command line cannot be read. It was copy-pasted, byte-identical, into the
citation, BibTeX-field, reference, and grounding scanners; it lives here once so
the scanners share one implementation. The "several paths joined into one" hint
guards the classic unquoted-variable-in-zsh mistake that collapses a whole file
list into a single over-long, unreadable argument — which would otherwise look
like a clean "nothing to do" run.
"""
import errno
import sys


def report_unreadable(path, err):
    """Print a friendly stderr warning for an unreadable path. Truncates the
    path so a runaway argument cannot flood the terminal, and adds a hint when
    the argument looks like several paths collapsed into one (the classic
    unquoted-variable-in-zsh mistake)."""
    shown = str(path)
    if len(shown) > 80:
        shown = shown[:77] + '...'
    print(f"warning: cannot read {shown!r}: {err.strerror or err}", file=sys.stderr)
    if getattr(err, 'errno', None) == errno.ENAMETOOLONG or '\n' in str(path):
        print(
            "  hint: this argument looks like several paths joined into one. "
            "Pass each file as a separate argument (in zsh, unquoted variables "
            "are not split on spaces; use an array or xargs).",
            file=sys.stderr,
        )
