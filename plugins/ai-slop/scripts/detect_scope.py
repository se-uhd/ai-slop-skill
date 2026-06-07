#!/usr/bin/env python3
"""detect_scope.py [PATH]

Detect whether the input is LaTeX source. PATH is a file or directory and
defaults to the current working directory. Prints `latex` or `general` to
stdout and exits 0. `general` is the safe default.

This drives which rule layers a skill loads:
    latex   -> rules-general.md + rules-scientific.md + rules-latex.md
               (a LaTeX paper is always a research article, so the scientific
                layer is included automatically)
    general -> rules-general.md
               (plus rules-scientific.md only when --scientific is passed, to
                treat a non-LaTeX document as a research article)

Detection:
    A file is `latex` iff its extension is `.tex`; everything else (.pdf, .md,
    .txt, ...) is `general`.
    A directory is `latex` iff it contains a LaTeX root (a .tex with an
    uncommented \\documentclass and \\begin{document}, as find_latex_root.py
    decides); otherwise `general`.

The directory check shells out to find_latex_root.py so the two agree on what
counts as a root (commented-out markers, main.tex/paper.tex preference, and the
recursive-fallback search).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIND_LATEX_ROOT = HERE / 'find_latex_root.py'


def scope_for_file(path):
    return 'latex' if path.suffix.lower() == '.tex' else 'general'


def scope_for_dir(path):
    result = subprocess.run(
        [sys.executable, str(FIND_LATEX_ROOT), str(path)],
        capture_output=True, text=True,
    )
    # rc 0: unique LaTeX root; rc 2: multiple candidate roots. Either is LaTeX.
    return 'latex' if result.returncode in (0, 2) else 'general'


def detect_scope(target):
    p = Path(target)
    if p.is_file():
        return scope_for_file(p)
    if p.is_dir():
        return scope_for_dir(p)
    # Nonexistent path: classify by extension if it looks like a file.
    if p.suffix:
        return scope_for_file(p)
    return 'general'


def main(argv):
    target = argv[1] if len(argv) > 1 else '.'
    print(detect_scope(target))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
