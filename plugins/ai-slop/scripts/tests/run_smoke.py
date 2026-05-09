#!/usr/bin/env python3
"""Smoke tests for the ai-slop scripts.

Runs each script against fixtures and asserts exit codes + stdout/stderr.
Exits 0 if all pass; non-zero on the first failure (with a summary at the end).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

LATEX_BODY = '\\documentclass{article}\n\\begin{document}\nhi\n\\end{document}\n'
COMMENTED = '% \\documentclass{article}\n% \\begin{document}\n'


def run(script, *args):
    cmd = [PYTHON, str(SCRIPTS / script)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def write(p, content):
    Path(p).write_text(content, encoding='utf-8')


# ---------- find_latex_root.py ----------

def test_find_latex_root_empty():
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 1, f"empty dir: rc={rc} out={out!r}"
        assert out == '', f"empty dir: out={out!r}"


def test_find_latex_root_single():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'paper.tex', LATEX_BODY)
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 0, f"single root: rc={rc} err={err!r}"
        assert out.strip().endswith('paper.tex'), f"single root: out={out!r}"


def test_find_latex_root_prefer_main():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex', LATEX_BODY)
        write(Path(d) / 'other.tex', LATEX_BODY)
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 0, f"prefer main: rc={rc}"
        assert out.strip().endswith('main.tex'), f"prefer main: out={out!r}"


def test_find_latex_root_prefer_paper():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'paper.tex', LATEX_BODY)
        write(Path(d) / 'other.tex', LATEX_BODY)
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 0, f"prefer paper: rc={rc}"
        assert out.strip().endswith('paper.tex'), f"prefer paper: out={out!r}"


def test_find_latex_root_ambiguous():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'a.tex', LATEX_BODY)
        write(Path(d) / 'b.tex', LATEX_BODY)
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 2, f"ambiguous: rc={rc}"
        lines = [line for line in out.strip().split('\n') if line]
        assert len(lines) == 2, f"ambiguous: lines={lines}"


def test_find_latex_root_commented_only():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'paper.tex', COMMENTED)
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 1, f"commented only: rc={rc} out={out!r}"


def test_find_latex_root_subdir():
    with tempfile.TemporaryDirectory() as d:
        sub = Path(d) / 'paper'
        sub.mkdir()
        write(sub / 'main.tex', LATEX_BODY)
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 0, f"subdir: rc={rc} out={out!r}"
        assert out.strip().endswith('main.tex'), f"subdir: out={out!r}"


def test_find_latex_root_root_with_includes():
    """Multi-file paper: root has \\documentclass; \\input-ed fragments don't."""
    with tempfile.TemporaryDirectory() as d:
        sections = Path(d) / 'sections'
        sections.mkdir()
        write(Path(d) / 'main.tex',
              '\\documentclass{article}\n\\begin{document}\n\\input{sections/intro}\n\\end{document}\n')
        write(sections / 'intro.tex', 'Some intro text.\n')
        rc, out, err = run('find_latex_root.py', d)
        assert rc == 0, f"includes: rc={rc} out={out!r}"
        assert out.strip().endswith('main.tex'), f"includes: out={out!r}"


# ---------- fetch_tropes.py ----------

def test_fetch_tropes_emits_body_and_source():
    """Verifies the script runs end-to-end and surfaces a source attribution.
    Network reachability is not required: even fully offline the bundled
    fallback path produces output."""
    with tempfile.TemporaryDirectory() as d:
        fallback = Path(d) / 'fallback.md'
        write(fallback, '# Fallback content\n\nSome bundled tropes here.\n')
        rc, out, err = run('fetch_tropes.py', str(fallback))
        assert rc == 0, f"fetch: rc={rc} err={err!r}"
        assert out, f"fetch: empty stdout"
        assert 'source:' in err, f"fetch: no 'source:' line in stderr ({err!r})"


# ---------- check_bib_fields.py ----------

BIB_FIXTURE = """
@string{ JCS = "Journal of Computer Science" }

@article{good2024,
  author = {Smith, J.},
  title = {Hello},
  journal = JCS,
  year = {2024}
}

@article{bad-article,
  author = {Doe, A.},
  title = {No Journal},
  year = {2024}
}

@inproceedings{bad-inproc,
  author = {Doe, A.},
  title = {No Booktitle},
  year = {2024}
}

@misc{some-misc,
  howpublished = {blog}
}

@book{good-book-with-editor,
  editor = {Knuth, D.},
  title = {The Art},
  publisher = {AW},
  year = {1968}
}

@online{biblatex-only,
  author = {X},
  title = {Y},
  url = {http://example.org}
}
"""


def test_check_bib_fields_flags_only_missing():
    with tempfile.TemporaryDirectory() as d:
        bib = Path(d) / 'refs.bib'
        write(bib, BIB_FIXTURE)
        rc, out, err = run('check_bib_fields.py', str(bib))
        assert rc == 0, f"bib: rc={rc} err={err!r}"
        lines = [line for line in out.strip().split('\n') if line]
        assert len(lines) == 2, f"bib: expected 2 missing-field lines, got {len(lines)}: {lines!r}"
        joined = '\n'.join(lines)
        assert 'bad-article' in joined and 'journal' in joined, f"bib: bad-article missing journal not flagged: {lines!r}"
        assert 'bad-inproc' in joined and 'booktitle' in joined, f"bib: bad-inproc missing booktitle not flagged: {lines!r}"
        # @misc has no required fields → must NOT be flagged
        assert 'some-misc' not in joined, f"bib: @misc was flagged but has no required fields: {lines!r}"
        # @book with editor satisfies author requirement → must NOT be flagged
        assert 'good-book-with-editor' not in joined, f"bib: @book with editor was flagged: {lines!r}"
        # @online is BibLaTeX, unknown to standard BibTeX → must be silently skipped
        assert 'biblatex-only' not in joined, f"bib: unknown @online was flagged: {lines!r}"
        # Fixture has 5 standard-BibTeX entries (article good/bad, inproceedings bad,
        # misc, book); @online and @string are skipped. Of those, 2 are flagged.
        assert 'checked 5 entries across 1 file(s), 2 missing-field issue(s)' in err, \
            f"bib: stderr summary missing or wrong: {err!r}"


def test_check_bib_fields_summary_on_clean_input():
    with tempfile.TemporaryDirectory() as d:
        bib = Path(d) / 'refs.bib'
        write(bib, """
@article{ok,
  author = {Smith, J.},
  title = {Hello},
  journal = {J},
  year = {2024}
}
""")
        rc, out, err = run('check_bib_fields.py', str(bib))
        assert rc == 0, f"clean bib: rc={rc} err={err!r}"
        assert out == '', f"clean bib: expected empty stdout, got {out!r}"
        assert 'checked 1 entries across 1 file(s), 0 missing-field issue(s)' in err, \
            f"clean bib: stderr summary missing or wrong: {err!r}"


# ---------- find_citation_issues.py ----------

CITE_FIXTURE = """\
Single grounded cite~\\cite{ok2024}. % GROUNDING: "ok2024 says yes"

Two-key, not a cluster~\\cite{a, b}.

Three-key cluster with no grounding~\\cite{x, y, z}.

A grounded follow-line cite~\\cite{follow2025}.
% GROUNDING: "follow2025 says foo"

A commented-out cite must not flag: % see \\cite{ghost,phantom,wraith}

\\citet{textcite-cluster, more, three} should also be a cluster.

\\citeauthor{styleonly} \\cite{styleonly} % GROUNDING: "styleonly was groundedly cited"

\\nocite{ignore} should not be scanned at all.
"""


def test_find_citation_issues_basic():
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'paper.tex'
        write(tex, CITE_FIXTURE)
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"cite: rc={rc} err={err!r}"
        lines = [line for line in out.strip().split('\n') if line]

        clusters = [l for l in lines if '\tcluster\t' in l]
        missing = [l for l in lines if '\tmissing-grounding\t' in l]

        # Two clusters: \cite{x, y, z} and \citet{textcite-cluster, more, three}.
        assert len(clusters) == 2, f"cite: expected 2 clusters, got {len(clusters)}: {clusters!r}"
        assert any('x,y,z' in c for c in clusters), f"cite: x,y,z cluster missing: {clusters!r}"
        assert any('textcite-cluster,more,three' in c for c in clusters), \
            f"cite: textcite cluster missing: {clusters!r}"

        # Missing-grounding: \cite{a, b}, \cite{x, y, z}, and \citet{textcite-cluster,...}.
        # Grounded: ok2024 (same line), follow2025 (next non-blank), styleonly (same line).
        # The commented-out cite and \nocite must not appear at all.
        for grounded_key in ('ok2024', 'follow2025', 'styleonly'):
            assert not any(grounded_key in m for m in missing), \
                f"cite: {grounded_key} should be grounded, found in missing: {missing!r}"
        for ghost_key in ('ghost', 'phantom', 'wraith', 'ignore'):
            assert not any(ghost_key in l for l in lines), \
                f"cite: {ghost_key} should be ignored, found in output: {lines!r}"
        assert any('a,b' in m for m in missing), f"cite: a,b missing-grounding not flagged: {missing!r}"
        assert any('x,y,z' in m for m in missing), f"cite: x,y,z missing-grounding not flagged: {missing!r}"

        # Stderr summary: cite count is everything except \nocite, \citeauthor, and the
        # commented-out cite. That is: ok2024, (a,b), (x,y,z), follow2025,
        # (textcite-cluster,more,three), styleonly = 6 cite calls.
        assert 'scanned 6 cite call(s) across 1 file(s); 2 cluster(s)' in err, \
            f"cite: stderr summary missing or wrong: {err!r}"


def test_find_citation_issues_no_findings():
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'clean.tex'
        write(tex, 'A clean cite~\\cite{ok}. % GROUNDING: "ok says hi"\n')
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"clean cite: rc={rc} err={err!r}"
        assert out == '', f"clean cite: expected empty stdout, got {out!r}"
        assert 'scanned 1 cite call(s) across 1 file(s); 0 cluster(s), 0 missing-grounding' in err, \
            f"clean cite: stderr summary missing or wrong: {err!r}"


def test_find_citation_issues_optional_args():
    """\\cite[opt]{key} and \\citep[see, e.g.,][p.~3]{a, b, c} parse correctly."""
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'paper.tex'
        write(tex, '\\citep[see, e.g.,][p.~3]{a, b, c}\n')
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"optargs: rc={rc} err={err!r}"
        lines = [line for line in out.strip().split('\n') if line]
        # Must detect the cluster of 3 keys; the comma-bearing optional arg
        # must not be parsed as part of the key list.
        assert any('cluster' in l and 'a,b,c' in l for l in lines), \
            f"optargs: cluster not detected: {lines!r}"


# ---------- runner ----------

TESTS = [
    test_find_latex_root_empty,
    test_find_latex_root_single,
    test_find_latex_root_prefer_main,
    test_find_latex_root_prefer_paper,
    test_find_latex_root_ambiguous,
    test_find_latex_root_commented_only,
    test_find_latex_root_subdir,
    test_find_latex_root_root_with_includes,
    test_fetch_tropes_emits_body_and_source,
    test_check_bib_fields_flags_only_missing,
    test_check_bib_fields_summary_on_clean_input,
    test_find_citation_issues_basic,
    test_find_citation_issues_no_findings,
    test_find_citation_issues_optional_args,
]


def main():
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"\n{failed}/{len(TESTS)} failure(s)", file=sys.stderr)
        return 1
    print(f"\nAll {len(TESTS)} tests passed.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
