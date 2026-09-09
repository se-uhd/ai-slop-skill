#!/usr/bin/env python3
"""scan_io.py: shared helpers for the ai-slop scanners.

`report_unreadable` is the stderr warning emitted when a path passed on the
command line cannot be read. It was copy-pasted, byte-identical, into the
citation, BibTeX-field, reference, and grounding scanners, and is defined here
once so the scanners share one implementation. The "several paths joined into
one" hint guards the classic unquoted-variable-in-zsh mistake that collapses a
whole file list into a single over-long, unreadable argument, which would
otherwise look like a clean "nothing to do" run.

`FenceTracker` follows Markdown fenced code blocks line by line for the
scanners that skip code (scan_glyphs.py, scan_reference.py). It honors nesting
the way scan_repo.py does: a fence closes only on a bare marker of the same
character that is at least as long as the opener, so a ``` block quoted inside
a ```` block does not end the outer block.
"""
import errno
import re
import sys


class FenceTracker:
    """Track open Markdown fences. Call `feed(line)` for every line in order.
    It returns True when the line is a fence marker or sits inside a fence,
    that is, when the line is not prose."""

    FENCE_RE = re.compile(r'^\s*(?P<fence>`{3,}|~{3,})\s*(?P<info>[^`]*)$')

    def __init__(self):
        self.stack = []

    def feed(self, line):
        m = self.FENCE_RE.match(line)
        if m:
            fence, info = m.group('fence'), m.group('info').strip()
            if (self.stack and not info and fence[0] == self.stack[-1][0]
                    and len(fence) >= len(self.stack[-1])):
                self.stack.pop()
            else:
                self.stack.append(fence)
            return True
        return bool(self.stack)


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
