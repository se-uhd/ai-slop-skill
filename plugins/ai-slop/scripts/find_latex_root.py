#!/usr/bin/env python3
"""find_latex_root.py [dir]

Locate the LaTeX root .tex file under dir (default cwd).

A file qualifies as the root iff it contains both \\documentclass and
\\begin{document} on lines that are not LaTeX comments (i.e., the marker is
not preceded by `%` on its own line). Multi-file papers using \\input{} or
\\include{} are handled implicitly: fragments lack these markers, so only
the root qualifies.

Search strategy: glob *.tex in dir non-recursively first; if no candidates
qualify, fall back to a recursive search of the same tree. The fast path
covers the common layout where the root sits in the working directory; the
fallback covers `paper/main.tex` style subdir layouts.

Exit codes:
  0 + single path on stdout: unique root, or one match after preferring
    main.tex / paper.tex when multiple candidates exist.
  1 (silent stdout): no root found anywhere in the tree.
  2 + newline-separated paths on stdout: multiple roots and none is named
    main.tex or paper.tex; caller must disambiguate.

Known limitation: matches \\documentclass / \\begin{document} that appear
inside \\verb, listings, or other non-`%`-comment LaTeX constructs. Rare in
practice for paper roots.
"""
import re
import sys
from pathlib import Path

DOC = re.compile(r'^[^%]*\\documentclass', re.M)
BEG = re.compile(r'^[^%]*\\begin\{document\}', re.M)


def is_root(path):
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return False
    return bool(DOC.search(text) and BEG.search(text))


def find_roots(directory):
    flat = sorted(directory.glob('*.tex'))
    roots = [p for p in flat if is_root(p)]
    if roots:
        return roots
    return sorted(p for p in directory.rglob('*.tex') if is_root(p))


def main(argv):
    directory = Path(argv[1] if len(argv) > 1 else '.')
    roots = find_roots(directory)
    if not roots:
        return 1
    if len(roots) == 1:
        print(roots[0])
        return 0
    for preferred in ('main.tex', 'paper.tex'):
        for r in roots:
            if r.name == preferred:
                print(r)
                return 0
    for r in roots:
        print(r)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
