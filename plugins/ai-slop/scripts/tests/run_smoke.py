#!/usr/bin/env python3
"""Smoke tests for the ai-slop scripts.

Runs each script against fixtures and asserts exit codes + stdout/stderr.
Exits 0 if all pass; non-zero on the first failure (with a summary at the end).
"""
import os
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


def test_check_bib_fields_all_unreadable_exits_2():
    # No path can be read -> the run scanned nothing and must fail loudly (rc 2),
    # not report a clean "0 issues" with rc 0.
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('check_bib_fields.py', str(Path(d) / 'missing.bib'))
        assert rc == 2, f"unreadable bib: rc={rc} err={err!r}"
        assert 'none of the 1 path(s)' in err, f"unreadable bib: no error line: {err!r}"


def test_check_bib_fields_partial_read_exits_0():
    # One readable + one missing file is partial success: exit 0, file count 1.
    # Guards against a regression that counts given paths instead of files read.
    with tempfile.TemporaryDirectory() as d:
        bib = Path(d) / 'refs.bib'
        write(bib, '@article{ok,\n  author = {A},\n  title = {T},\n  journal = {J},\n  year = {2024}\n}\n')
        rc, out, err = run('check_bib_fields.py', str(bib), str(Path(d) / 'gone.bib'))
        assert rc == 0, f"partial bib: rc={rc} err={err!r}"
        assert 'across 1 file(s)' in err, f"partial bib: wrong file count: {err!r}"


# ---------- find_citation_issues.py ----------

CITE_FIXTURE = """\
Single grounded cite~\\cite{ok2024}. % GROUNDING: "ok2024 says yes"

Two-key, not a cluster~\\cite{a, b}.

Three-key cluster with no grounding~\\cite{x, y, z}.

A grounded follow-line cite~\\cite{follow2025}.
% GROUNDING: "follow2025 says foo"

A commented-out cite must not flag: % see \\cite{ghost,phantom,wraith}

\\citet{textcite-cluster, more, three} should also be a cluster.

\\citeauthor{styleonly} \\cite{styleonly} % GROUNDING: "styleonly says hi"

\\nocite{ignore} should not be scanned at all.

A biblatex \\textcite{bib1, bib2, bib3} cluster.

\\fullcite{biblatex-grounded}. % GROUNDING: "biblatex-grounded says hi"

A capitalized sentence-starter \\Citet{cap1, cap2, cap3} cluster.

A starred natbib form~\\citet*{star1, star2, star3} should also be a cluster.

\\Citeauthor{capskip} is a capitalized style-only helper and must be skipped.

A non-cite command \\textbf{not, a, cite} must not flag.
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

        # Five clusters: \cite{x,y,z}, \citet{textcite-cluster,...},
        # \textcite{bib1,bib2,bib3}, \Citet{cap1,cap2,cap3}, \citet*{star1,star2,star3}.
        assert len(clusters) == 5, f"cite: expected 5 clusters, got {len(clusters)}: {clusters!r}"
        for expected in ('x,y,z', 'textcite-cluster,more,three', 'bib1,bib2,bib3',
                         'cap1,cap2,cap3', 'star1,star2,star3'):
            assert any(expected in c for c in clusters), \
                f"cite: cluster {expected} missing: {clusters!r}"

        # Grounded (must NOT appear in missing): ok2024, follow2025, styleonly, biblatex-grounded.
        # Ignored entirely (must NOT appear anywhere): ghost, phantom, wraith, ignore, \textbf args.
        for grounded_key in ('ok2024', 'follow2025', 'styleonly', 'biblatex-grounded'):
            assert not any(grounded_key in m for m in missing), \
                f"cite: {grounded_key} should be grounded, found in missing: {missing!r}"
        for ghost_key in ('ghost', 'phantom', 'wraith', 'ignore', 'not,a,cite', 'capskip'):
            assert not any(ghost_key in l for l in lines), \
                f"cite: {ghost_key} should not be detected, found in output: {lines!r}"
        for missing_key in ('a,b', 'x,y,z', 'bib1,bib2,bib3', 'cap1,cap2,cap3', 'star1,star2,star3'):
            assert any(missing_key in m for m in missing), \
                f"cite: missing-grounding {missing_key} not flagged: {missing!r}"

        # Considered: every cite call in GROUNDED_COMMANDS that resolved to >=1 key.
        # ok2024, (a,b), (x,y,z), follow2025, (textcite-cluster,more,three), styleonly,
        # (bib1,bib2,bib3), biblatex-grounded, (cap1,cap2,cap3), (star1,star2,star3) = 10.
        # Missing-grounding: every considered cite without a grounding comment.
        # (a,b), (x,y,z), (textcite-cluster,more,three), (bib1,bib2,bib3),
        # (cap1,cap2,cap3), (star1,star2,star3) = 6.
        assert ('considered 10 cite call(s) across 1 file(s); 5 cluster(s), '
                '6 missing-grounding') in err, \
            f"cite: stderr summary missing or wrong: {err!r}"


def test_find_citation_issues_no_findings():
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'clean.tex'
        write(tex, 'A clean cite~\\cite{ok}. % GROUNDING: "ok says hi"\n')
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"clean cite: rc={rc} err={err!r}"
        assert out == '', f"clean cite: expected empty stdout, got {out!r}"
        assert 'considered 1 cite call(s) across 1 file(s); 0 cluster(s), 0 missing-grounding' in err, \
            f"clean cite: stderr summary missing or wrong: {err!r}"


def test_find_citation_issues_per_key_grounding_not_flagged():
    """The per-key `% GROUNDING <key>: "..."` convention (key before the colon,
    incl. DBLP keys with internal colons) must count as grounded, on the same
    line and the next line — not reported as missing-grounding."""
    fixture = (
        'Same-line per-key~\\cite{alpha}. % GROUNDING alpha: "alpha says yes"\n'
        '\n'
        'Next-line per-key~\\cite{beta}.\n'
        '% GROUNDING beta: "beta says foo"\n'
        '\n'
        'DBLP-style key~\\cite{DBLP:conf/icse/BanoGH25}.\n'
        '% GROUNDING DBLP:conf/icse/BanoGH25: "internal colons in the key"\n'
        '\n'
        'Multi-key sentence~\\cite{one, two}.\n'
        '% GROUNDING one: "one says a"\n'
        '% GROUNDING two: "two says b"\n'
    )
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'paper.tex'
        write(tex, fixture)
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"per-key grounding: rc={rc} err={err!r}"
        missing = [l for l in out.strip().split('\n') if '\tmissing-grounding\t' in l]
        assert missing == [], f"per-key grounding falsely flagged missing: {missing!r}"
        assert '0 missing-grounding' in err, f"per-key grounding: stderr summary: {err!r}"


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


def test_find_citation_issues_truncate_respects_120_chars():
    long_line = 'A long line with text ' * 20 + '\\cite{a, b, c}'
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'paper.tex'
        write(tex, long_line + '\n')
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"truncate: rc={rc} err={err!r}"
        lines = [line for line in out.strip().split('\n') if line]
        assert lines, f"truncate: no findings, expected cluster + missing-grounding"
        for line in lines:
            parts = line.split('\t')
            assert len(parts) == 4, f"truncate: bad TSV ({len(parts)} cols): {line!r}"
            context = parts[3]
            assert len(context) <= 120, \
                f"truncate: context exceeds 120 chars ({len(context)}): {context!r}"
            assert context.endswith('...'), \
                f"truncate: long line should end with ...: {context!r}"


def test_find_citation_issues_all_unreadable_exits_2():
    # The original footgun: a whole file list collapsed into one over-long,
    # unreadable argument. Nothing gets scanned, so the run must exit 2 (with a
    # shell-quoting hint), not exit 0 with a misleading "0 findings" summary.
    joined = ' '.join(f'file{i}.tex' for i in range(60))
    rc, out, err = run('find_citation_issues.py', joined)
    assert rc == 2, f"unreadable cite arg: rc={rc} err={err!r}"
    assert 'none of the 1 path(s)' in err, f"unreadable cite arg: no error line: {err!r}"
    assert 'hint:' in err, f"unreadable cite arg: missing shell-quoting hint: {err!r}"


def test_find_citation_issues_partial_read_exits_0():
    # One readable file plus one missing file is a partial success: the missing
    # path is warned about, but the run still exits 0 because something was read.
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'paper.tex'
        write(tex, 'A clean cite~\\cite{ok}. % GROUNDING: "ok"\n')
        rc, out, err = run('find_citation_issues.py', str(tex), str(Path(d) / 'gone.tex'))
        assert rc == 0, f"partial read: rc={rc} err={err!r}"
        assert 'across 1 file(s)' in err, f"partial read: wrong file count: {err!r}"


# ---------- lint_markdown.py ----------

def _write_md(d, name, content_bytes):
    p = Path(d) / name
    p.write_bytes(content_bytes)
    return p


def test_lint_markdown_clean_file():
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# Title\n\nbody\n")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 0, f"clean: rc={rc} out={out!r} err={err!r}"
        assert out == '', f"clean: stdout should be empty, got {out!r}"


def test_lint_markdown_trailing_whitespace():
    # PyMarkdown MD009 default allows 0 or 2 trailing spaces (markdown
    # hard-break syntax), so use 3 to provoke the rule.
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# Title\n\nbody   \n")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"trail: rc={rc} out={out!r}"
        assert 'md009' in out, f"trail: md009 missing: {out!r}"


def test_lint_markdown_eof_newline_missing():
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# Title\n\nbody")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"eof missing: rc={rc}"
        assert 'md047' in out, f"eof missing: md047 missing: {out!r}"


def test_lint_markdown_multiple_blank_lines():
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# Title\n\n\n\nbody\n")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"blanks: rc={rc}"
        assert 'md012' in out, f"blanks: md012 missing: {out!r}"


def test_lint_markdown_heading_level_jump():
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# Title\n\n### Subsection\n\nbody\n")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"jump: rc={rc}"
        assert 'md001' in out, f"jump: md001 missing: {out!r}"


def test_lint_markdown_multiple_h1():
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# One\n\nbody\n\n# Two\n\nmore\n")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"h1: rc={rc}"
        assert 'md025' in out, f"h1: md025 missing: {out!r}"


def test_check_baseline_passes_on_bundled_yaml():
    # check_baseline.py is synced from the upstream pymarkdown-skill repo
    # (alongside lint_markdown.py and refresh_vendor.py) and asserts that
    # lint_markdown.yaml still carries the upstream baseline lint config.
    # Run it here so the sync-owned guard stays exercised and a yaml edit
    # that drops the baseline fails the suite.
    rc, out, err = run('check_baseline.py')
    assert rc == 0, f"check_baseline: rc={rc} out={out!r} err={err!r}"
    assert 'baseline ok' in err, f"check_baseline: unexpected output: {err!r}"


def test_lint_markdown_blanks_around_headings():
    # MD022 — the rule that flags headings without blank lines around them.
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', b"# Title\nimmediately after H1\n")
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"md022: rc={rc}"
        assert 'md022' in out, f"md022: missing: {out!r}"


def test_lint_markdown_finding_block_missing_label():
    content = (b"# AI Slop Review\n\n## Findings by section\n\n"
               b"### Abstract\n\n#### Finding 1\n"
               b"- **Rule:** test\n- **Location:** foo.tex:1\n"
               b"- **Quote:** bar\n")
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'ai-slop-report.md', content)
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"finding: rc={rc}"
        assert 'finding-block-missing-label' in out, \
            f"finding: rule missing: {out!r}"
        assert 'Suggested revision' in out, \
            f"finding: missing label name not mentioned: {out!r}"


def test_lint_markdown_finding_block_clean_passes():
    # Heading-to-list spacing satisfies MD022/MD032 (blank lines around
    # headings and lists); only the schema check is under test here.
    content = (b"# AI Slop Review\n\n## Findings by section\n\n"
               b"### Abstract\n\n#### Finding 1\n\n"
               b"- **Rule:** test\n- **Location:** foo.tex:1\n"
               b"- **Quote:** bar\n- **Suggested revision:** baz\n")
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'ai-slop-report.md', content)
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 0, f"clean finding: rc={rc} out={out!r}"


def test_lint_markdown_writing_md_h1_in_tropes_section():
    content = (b"# Writing rules for this paper\n\n"
               b"## AI Writing Tropes to Avoid\n\nintro\n\n"
               b"# Spurious\n\nbody\n")
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'WRITING.md', content)
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"writing h1-in-trope: rc={rc}"
        assert 'writing-md-structure' in out, \
            f"writing h1-in-trope: rule missing: {out!r}"


def test_lint_markdown_writing_md_no_tropes_section():
    content = b"# Writing rules for this paper\n\n## Language\n\nrules\n"
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'WRITING.md', content)
        rc, out, err = run('lint_markdown.py', str(p))
        assert rc == 1, f"writing no-tropes: rc={rc}"
        assert 'writing-md-structure' in out, \
            f"writing no-tropes: rule missing: {out!r}"
        assert 'no `## AI Writing Tropes to Avoid` section' in out, \
            f"writing no-tropes: wrong message: {out!r}"


def test_lint_markdown_fix_mode_normalizes():
    # Run of 4 blank lines, missing trailing newline. PyMarkdown's `fix`
    # collapses md012 (multiple blanks) and inserts the trailing newline
    # for md047. Lines with trailing whitespace under MD009's 2-space
    # hard-break allowance are normalised to 0 or 2.
    content = b"# Title\n\n\n\n\nbody   \nmore"
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', content)
        rc, out, err = run('lint_markdown.py', '--fix', str(p))
        assert rc == 0, f"fix: rc={rc} out={out!r} err={err!r}"
        fixed = p.read_bytes()
        assert fixed.endswith(b'\n'), f"fix: missing trailing newline: {fixed!r}"
        import re as _re
        assert not _re.search(rb'\n{4,}', fixed), \
            f"fix: still has >2 consecutive blank lines: {fixed!r}"


def test_lint_markdown_fix_mode_preserves_structural_findings():
    # MD025 (multiple top-level headings) is not auto-fixable, so it
    # survives `--fix` and is still reported on the rescan.
    content = b"# One\n\nbody\n\n# Two\n\nmore\n"
    with tempfile.TemporaryDirectory() as d:
        p = _write_md(d, 'doc.md', content)
        rc, out, err = run('lint_markdown.py', '--fix', str(p))
        assert rc == 1, f"fix-structural: rc={rc}"
        assert 'md025' in out, \
            f"fix-structural: structural finding lost: {out!r}"


def test_lint_markdown_unreadable_exits_2():
    # A missing path must fail with the documented exit code 2 ("could not read
    # or run the linter"), not a silent pass. Locks in the existing contract.
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('lint_markdown.py', str(Path(d) / 'missing.md'))
        assert rc == 2, f"missing md: rc={rc} err={err!r}"
        assert 'cannot read' in err, f"missing md: no error line: {err!r}"


# ---------- version-string consistency ----------

def test_version_strings_in_sync():
    """All version references — both manifests, every SKILL.md frontmatter, the
    report-template `**Skill version:**` line in review/SKILL.md, and the
    `skill version <X>` reference in the WRITING.md header in init/SKILL.md —
    must equal the canonical version in plugins/ai-slop/.claude-plugin/plugin.json.

    Guards against the rev7-style drift where SKILL.md files got bumped but the
    two manifests were left behind. See README "Maintainer notes" for the list
    of files this enforces.
    """
    import json
    import re

    plugin_root = SCRIPTS.parent           # plugins/ai-slop
    repo_root = plugin_root.parent.parent  # repo root

    canonical = json.loads(
        (plugin_root / '.claude-plugin' / 'plugin.json').read_text(encoding='utf-8')
    )['version']

    mismatches = []
    def check(label, value):
        if value != canonical:
            mismatches.append(f"{label}: {value!r} != canonical {canonical!r}")

    mp = json.loads(
        (repo_root / '.claude-plugin' / 'marketplace.json').read_text(encoding='utf-8')
    )
    ai_slop_entries = [e for e in mp.get('plugins', []) if e.get('name') == 'ai-slop']
    assert ai_slop_entries, "marketplace.json: no plugins[] entry named 'ai-slop'"
    for entry in ai_slop_entries:
        check("marketplace.json plugins[ai-slop].version", entry.get('version'))

    skills_dir = plugin_root / 'skills'
    skill_files = sorted(skills_dir.glob('*/SKILL.md'))
    assert skill_files, f"no SKILL.md files found under {skills_dir}"
    for skill_md in skill_files:
        text = skill_md.read_text(encoding='utf-8')
        m = re.search(r'^\s*version:\s*"([^"]+)"', text, re.MULTILINE)
        rel = skill_md.relative_to(repo_root)
        check(f"{rel} frontmatter version", m.group(1) if m else None)

    review_text = (skills_dir / 'review' / 'SKILL.md').read_text(encoding='utf-8')
    m = re.search(r'\*\*Skill version:\*\*\s*(\S+)', review_text)
    check("review/SKILL.md report-template **Skill version:** line",
          m.group(1) if m else None)

    init_text = (skills_dir / 'init' / 'SKILL.md').read_text(encoding='utf-8')
    m = re.search(r'skill version\s+([^\s)]+)\)', init_text)
    check("init/SKILL.md WRITING.md header `skill version <X>` reference",
          m.group(1) if m else None)

    assert not mismatches, (
        "Version drift detected (see README \"Maintainer notes\"):\n  "
        + "\n  ".join(mismatches)
    )


# ---------- detect_scope.py ----------

def test_detect_scope_file_tex():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'paper.tex'
        write(p, LATEX_BODY)
        rc, out, err = run('detect_scope.py', str(p))
        assert rc == 0 and out.strip() == 'latex', f"tex file: rc={rc} out={out!r}"


def test_detect_scope_file_pdf():
    # A PDF is not LaTeX source, so it detects as general; --scientific is what
    # pulls in the research-article rules for a non-LaTeX paper.
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'paper.pdf'
        write(p, 'pdf')
        rc, out, err = run('detect_scope.py', str(p))
        assert out.strip() == 'general', f"pdf file: out={out!r}"


def test_detect_scope_file_markdown():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 'notes.md'
        write(p, '# hi\n')
        rc, out, err = run('detect_scope.py', str(p))
        assert out.strip() == 'general', f"md file: out={out!r}"


def test_detect_scope_dir_latex():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex', LATEX_BODY)
        rc, out, err = run('detect_scope.py', d)
        assert out.strip() == 'latex', f"latex dir: out={out!r}"


def test_detect_scope_dir_pdf():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'draft.pdf', 'pdf')
        rc, out, err = run('detect_scope.py', d)
        assert out.strip() == 'general', f"pdf dir: out={out!r}"


def test_detect_scope_dir_general():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'README.md', '# hi\n')
        rc, out, err = run('detect_scope.py', d)
        assert out.strip() == 'general', f"general dir: out={out!r}"


def test_detect_scope_dir_empty_defaults_general():
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('detect_scope.py', d)
        assert out.strip() == 'general', f"empty dir: out={out!r}"


def test_detect_scope_commented_tex_is_not_latex():
    # find_latex_root ignores commented-out \documentclass, so a dir whose only
    # .tex is fully commented out is not LaTeX and resolves to general.
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'stub.tex', COMMENTED)
        rc, out, err = run('detect_scope.py', d)
        assert out.strip() == 'general', f"commented tex: out={out!r}"


# ---------- scan_repo.py ----------

def _scan_lines(out):
    return [line for line in out.split('\n') if line]


def _scan_text(out):
    # join just the <text> field of each `relpath:line:text` output line
    return '\n'.join(line.split(':', 2)[2] for line in _scan_lines(out))


def _scan_paths(out):
    return {line.split(':', 1)[0] for line in _scan_lines(out)}


def test_scan_repo_prose_markdown_skips_code_fences():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'doc.md',
              '# Title\n\nReal prose line.\n\n```\ncode_in_fence();\n```\n\nMore prose.\n')
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"md: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'Real prose line.' in text and 'More prose.' in text, f"md prose missing: {out!r}"
        assert '# Title' in text, f"md heading missing: {out!r}"
        assert 'code_in_fence' not in text, f"md fenced code not skipped: {out!r}"


def test_scan_repo_extracts_only_comments_from_source():
    src = ('package x\n'
           '/** A KDoc comment about coffee. */\n'
           'fun brew() {\n'
           '  // a line comment here\n'
           '  val url = "https://example.com/not-a-comment"\n'
           '  println(url)\n'
           '}\n')
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'A.kt', src)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"kt: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'A KDoc comment about coffee.' in text, f"kt KDoc missing: {out!r}"
        assert 'a line comment here' in text, f"kt line comment missing: {out!r}"
        assert 'fun brew' not in text and 'println' not in text, f"kt code leaked: {out!r}"
        # the // inside the URL string literal must NOT be read as a comment
        assert 'example.com' not in text, f"kt string-// leaked as a comment: {out!r}"


def test_scan_repo_hash_comments_not_values():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'config.yml', '# a config comment\nkey: value  # trailing note\nother: 3\n')
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"yaml: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'a config comment' in text, f"yaml comment missing: {out!r}"
        assert 'trailing note' in text, f"yaml trailing comment missing: {out!r}"
        assert 'value' not in text, f"yaml value leaked as prose: {out!r}"


def test_scan_repo_skips_generated_file():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'gen.ts',
              '/* eslint-disable */\n/**\n * Do not edit the class manually.\n */\n'
              'export const x = 1; // a real comment\n')
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"generated: rc={rc} err={err!r}"
        assert 'a real comment' not in out and 'Do not edit' not in out, \
            f"generated file not skipped: {out!r}"


def test_scan_repo_skips_lockfile_and_binary():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'package-lock.json', '{"x": "// not prose"}\n')
        (Path(d) / 'blob.bin').write_bytes(b'\x00\x01binary // text')
        write(Path(d) / 'ok.md', 'real prose\n')
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"skip: rc={rc} err={err!r}"
        paths = _scan_paths(out)
        assert 'ok.md' in paths, f"prose missing: {paths!r}"
        assert 'package-lock.json' not in paths, f"lockfile scanned: {paths!r}"
        assert 'blob.bin' not in paths, f"binary scanned: {paths!r}"


def test_scan_repo_walk_prunes_denylisted_dirs():
    # A plain temp dir is not a git work tree, so list_files falls back to os.walk
    # and must prune build/ and node_modules/.
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'keep.md', 'kept prose\n')
        (Path(d) / 'build').mkdir()
        write(Path(d) / 'build' / 'skip.md', 'build artifact prose\n')
        (Path(d) / 'node_modules').mkdir()
        write(Path(d) / 'node_modules' / 'dep.md', 'dependency prose\n')
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"walk: rc={rc} err={err!r}"
        paths = _scan_paths(out)
        assert 'keep.md' in paths, f"keep.md missing: {paths!r}"
        assert not any('build' in p or 'node_modules' in p for p in paths), \
            f"denylisted dir scanned: {paths!r}"


def test_scan_repo_respects_gitignore():
    import subprocess as sp
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'tracked.md', 'tracked prose\n')
        write(Path(d) / 'ignored.md', 'ignored prose\n')
        write(Path(d) / '.gitignore', 'ignored.md\n')
        sp.run(['git', 'init', '-q'], cwd=d, check=True)
        sp.run(['git', 'add', '-A'], cwd=d, check=True)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"gitignore: rc={rc} err={err!r}"
        paths = _scan_paths(out)
        assert 'tracked.md' in paths, f"tracked file missing: {paths!r}"
        assert 'ignored.md' not in paths, f"gitignored file scanned: {paths!r}"


def test_scan_repo_excludes_committed_vendor_dir():
    # A vendored/third-party directory that is committed (so `git ls-files` lists
    # it) must still be excluded: it is not the repository's own prose.
    import subprocess as sp
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'own.md', 'first-party prose\n')
        (Path(d) / '_vendor').mkdir()
        write(Path(d) / '_vendor' / 'lib.py', '# vendored upstream comment\n')
        sp.run(['git', 'init', '-q'], cwd=d, check=True)
        sp.run(['git', 'add', '-A'], cwd=d, check=True)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"vendor: rc={rc} err={err!r}"
        paths = _scan_paths(out)
        assert 'own.md' in paths, f"first-party file missing: {paths!r}"
        assert not any('_vendor' in p for p in paths), f"committed vendor dir scanned: {paths!r}"


def test_scan_repo_not_a_directory_exits_2():
    rc, out, err = run('scan_repo.py', '/nonexistent/path/xyzzy')
    assert rc == 2, f"missing dir: rc={rc} err={err!r}"
    assert 'not a directory' in err, f"missing dir: err={err!r}"


def test_scan_repo_summary_on_stderr():
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'a.md', 'one\ntwo\n')
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"summary: rc={rc} err={err!r}"
        assert 'scanned' in err and 'line(s)' in err, f"summary missing: {err!r}"


def test_scan_repo_python_docstring_and_hash():
    src = ('def f():\n'
           '    """A module docstring about brewing."""\n'
           '    label = "value # not a comment"\n'
           '    # a real comment\n'
           '    return label\n')
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'm.py', src)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"py: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'A module docstring about brewing.' in text, f"py docstring missing: {out!r}"
        assert 'a real comment' in text, f"py hash comment missing: {out!r}"
        assert 'not a comment' not in text, f"py string-# leaked: {out!r}"
        assert 'return label' not in text, f"py code leaked: {out!r}"


def test_scan_repo_shell_comments_skip_shebang():
    src = '#!/usr/bin/env bash\n# a real shell comment\necho "# not a comment"\n'
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 's.sh', src)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"sh: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'a real shell comment' in text, f"sh comment missing: {out!r}"
        assert 'usr/bin/env' not in text, f"sh shebang not skipped: {out!r}"
        assert 'not a comment' not in text, f"sh string-# leaked: {out!r}"


def test_scan_repo_java_javadoc_and_line():
    src = ('/**\n'
           ' * A Javadoc paragraph about beans.\n'
           ' */\n'
           'public class A { // a trailing note\n'
           '}\n')
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'A.java', src)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"java: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'A Javadoc paragraph about beans.' in text, f"java javadoc missing: {out!r}"
        assert 'a trailing note' in text, f"java line comment missing: {out!r}"
        assert 'public class A' not in text, f"java code leaked: {out!r}"


def test_scan_repo_js_ts_block_and_line():
    ts = ('// a TS line comment\n'
          '/* a TS\n'
          '   block comment */\n'
          'const x: number = 1;\n')
    js = ('function g() {} // a JS line comment\n')
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 't.ts', ts)
        write(Path(d) / 'j.js', js)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"jsts: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'a TS line comment' in text, f"ts line missing: {out!r}"
        assert 'block comment' in text, f"ts block (multiline) missing: {out!r}"
        assert 'a JS line comment' in text, f"js line missing: {out!r}"
        assert 'const x' not in text and 'function g' not in text, f"js/ts code leaked: {out!r}"


def test_scan_repo_latex_body_and_comments():
    # repo mode reviews .tex as prose: the document body AND its % comments (the
    # latter are content too, just as comments are in source files).
    src = ('\\documentclass{article}\n'
           '\\begin{document}\n'
           'The results are seamless and robust.  % TODO fix this wording\n'
           '% a standalone note about the phrasing\n'
           '\\end{document}\n')
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'paper.tex', src)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"tex: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'The results are seamless and robust.' in text, f"tex body missing: {out!r}"
        assert 'TODO fix this wording' in text, f"tex inline comment dropped: {out!r}"
        assert 'a standalone note about the phrasing' in text, f"tex standalone comment dropped: {out!r}"


def _git_repo_with_commit(d, subject, body):
    import subprocess as sp
    env = {**os.environ, 'GIT_AUTHOR_NAME': 'T', 'GIT_AUTHOR_EMAIL': 't@e.x',
           'GIT_COMMITTER_NAME': 'T', 'GIT_COMMITTER_EMAIL': 't@e.x'}
    write(Path(d) / 'f.txt', 'tracked file prose\n')
    sp.run(['git', 'init', '-q'], cwd=d, check=True, env=env)
    sp.run(['git', 'add', '-A'], cwd=d, check=True, env=env)
    sp.run(['git', 'commit', '-q', '-m', subject, '-m', body],
           cwd=d, check=True, env=env)


def test_scan_repo_commit_messages_scanned():
    # A commit's subject and body are reviewed under a `commit <sha>` pseudo-path;
    # the trailer line is metadata and must be dropped.
    body = ('This delivers a comprehensive solution.\n\n'
            'Co-authored-by: Someone <s@e.x>')
    with tempfile.TemporaryDirectory() as d:
        _git_repo_with_commit(d, 'Add a robust and seamless feature', body)
        rc, out, err = run('scan_repo.py', d)
        assert rc == 0, f"commit: rc={rc} err={err!r}"
        text = _scan_text(out)
        assert 'Add a robust and seamless feature' in text, f"commit subject missing: {out!r}"
        assert 'This delivers a comprehensive solution.' in text, f"commit body missing: {out!r}"
        assert 'Co-authored-by' not in text, f"trailer line leaked: {out!r}"
        assert any(p.startswith('commit ') for p in _scan_paths(out)), \
            f"commit pseudo-path missing: {out!r}"
        assert 'commit message(s)' in err, f"commit count missing from summary: {err!r}"


def test_scan_repo_no_commits_flag_suppresses():
    with tempfile.TemporaryDirectory() as d:
        _git_repo_with_commit(d, 'A slop-laden subject', 'body text here')
        rc, out, err = run('scan_repo.py', d, '--no-commits')
        assert rc == 0, f"no-commits: rc={rc} err={err!r}"
        assert not any(p.startswith('commit ') for p in _scan_paths(out)), \
            f"--no-commits still scanned commits: {out!r}"
        assert 'tracked file prose' in _scan_text(out), f"file prose dropped: {out!r}"
        assert 'and 0 commit message(s)' in err, f"summary count not zero: {err!r}"


def test_scan_repo_commits_count_selector():
    rc, out, err = run('scan_repo.py', '/nonexistent/zz', '--commits=5')
    # a count spec is accepted (the dir error, not a usage error, is what trips)
    assert rc == 2 and 'not a directory' in err, f"count selector: rc={rc} err={err!r}"


def test_scan_repo_bad_commits_value_is_usage_error():
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('scan_repo.py', d, '--commits=')
        assert rc == 2 and 'usage' in err, f"empty --commits: rc={rc} err={err!r}"


# ---------- verify_references.py ----------

sys.path.insert(0, str(SCRIPTS))
import verify_references as vref  # noqa: E402

_REC = {'title': 'A Study of Code Review', 'year': '2020', 'venue': 'ICSE'}


def test_verify_references_parses_bib():
    text = ('@inproceedings{smith2020,\n'
            '  title = {A Study of Code Review},\n'
            '  author = {Smith, Jane},\n'
            '  booktitle = {ICSE},\n'
            '  year = {2020},\n'
            '  doi = {10.1145/1234.5678}\n}\n')
    entries = list(vref.bib_entries(text))
    assert len(entries) == 1, entries
    e = entries[0]
    assert e['key'] == 'smith2020' and e['doi'] == '10.1145/1234.5678', e
    assert e['title'] == 'A Study of Code Review' and e['year'] == '2020', e
    assert e['venue'] == 'ICSE', e


def test_verify_references_compare_verdicts():
    ok = vref.compare_entry({'title': 'a study of code review', 'year': '2020', 'venue': 'ICSE'}, _REC)
    assert ok[0] == 'ok', ok
    assert vref.compare_entry({'title': 'totally different work', 'year': '2020'}, _REC)[0] == 'title-mismatch'
    assert vref.compare_entry({'title': 'a study of code review', 'year': '2019'}, _REC)[0] == 'year-mismatch'
    assert vref.compare_entry({'title': 'a study of code review', 'year': '2020', 'venue': 'NeurIPS'}, _REC)[0] == 'venue-mismatch'


def test_verify_references_doi_paths():
    def hit(_):
        return dict(_REC)

    def miss(_):
        return None
    assert vref.verify_entry({'doi': '10.1/x', 'title': 'a study of code review'},
                             hit, lambda t: [], lambda t: [])[0] == 'ok'
    assert vref.verify_entry({'doi': '10.1/x', 'title': 'foo'},
                             miss, lambda t: [], lambda t: [])[0] == 'doi-not-found'


def test_verify_references_offline():
    def boom(*_a):
        raise vref.NetworkError('no network')
    assert vref.verify_entry({'doi': '10.1/x'}, boom, lambda t: [], lambda t: [])[0] == 'unchecked-offline'
    assert vref.verify_entry({'title': 'something'}, lambda d: None, boom, boom)[0] == 'unchecked-offline'


def test_verify_references_no_doi_paths():
    assert vref.verify_entry({'title': 'a study of code review', 'year': '2020'},
                             lambda d: None, lambda t: [dict(_REC)], lambda t: [])[0] == 'ok'
    assert vref.verify_entry({'title': 'an unmatched unique title zzz'},
                             lambda d: None, lambda t: [], lambda t: [])[0] == 'not-found'


def test_verify_references_subprocess_unchecked_no_network():
    # An entry with neither DOI nor title needs no lookup, so the script runs
    # fully offline and reports `unchecked`.
    with tempfile.TemporaryDirectory() as d:
        bib = Path(d) / 'refs.bib'
        write(bib, '@misc{nodata,\n  note = {placeholder}\n}\n')
        rc, out, err = run('verify_references.py', str(bib))
        assert rc == 0, f"rc={rc} err={err!r}"
        assert 'nodata\tunchecked' in out, f"out={out!r}"
        assert 'checked 1 reference' in err, f"err={err!r}"


def test_verify_references_all_unreadable_exits_2():
    # An unreadable bib file is distinct from "offline": there is nothing to
    # verify, so the run exits 2 rather than the offline-tolerant 0.
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('verify_references.py', str(Path(d) / 'missing.bib'))
        assert rc == 2, f"unreadable refs: rc={rc} err={err!r}"
        assert 'none of the 1 bib file(s)' in err, f"unreadable refs: no error line: {err!r}"


def test_verify_references_partial_read_exits_0():
    # One readable bib (no DOI/title -> no network needed) plus one missing file
    # is partial success: exit 0. Guards against counting given paths vs reads.
    with tempfile.TemporaryDirectory() as d:
        bib = Path(d) / 'refs.bib'
        write(bib, '@misc{nodata,\n  note = {placeholder}\n}\n')
        rc, out, err = run('verify_references.py', str(bib), str(Path(d) / 'gone.bib'))
        assert rc == 0, f"partial refs: rc={rc} err={err!r}"
        assert 'checked 1 reference' in err, f"partial refs: wrong count: {err!r}"


# ---------- rule-layer structure ----------

RULE_LAYERS = ('rules-general.md', 'rules-scientific.md', 'rules-latex.md')


def test_rule_layers_exist():
    """The rules ship as three layered files plus a rationale doc; the old
    monolithic rules.md must be gone so nothing loads a stale path."""
    shared = SCRIPTS.parent / 'shared'
    for name in RULE_LAYERS + ('rules-rationale.md',):
        assert (shared / name).is_file(), f"missing rule layer: {name}"
    assert not (shared / 'rules.md').exists(), \
        "rules.md still present; it was split into the three layer files"


def test_rule_layers_lint_clean():
    """Each rule layer and the rationale doc must pass the Markdown linter."""
    shared = SCRIPTS.parent / 'shared'
    for name in RULE_LAYERS + ('rules-rationale.md',):
        rc, out, err = run('lint_markdown.py', str(shared / name))
        assert rc == 0, f"{name}: lint rc={rc} out={out!r} err={err!r}"


def test_no_dangling_rules_md_references():
    """No first-party doc may reference the removed monolithic rules.md. The
    layer filenames (rules-general.md, etc.) do not contain the substring
    'rules.md', so a plain substring scan flags only stale references."""
    plugin_root = SCRIPTS.parent
    repo_root = plugin_root.parent.parent
    docs = [repo_root / 'README.md']
    docs += sorted(plugin_root.glob('commands/*.md'))
    docs += sorted(plugin_root.glob('skills/*/SKILL.md'))
    docs += [plugin_root / 'shared' / n
             for n in RULE_LAYERS + ('rules-rationale.md',)]
    offenders = [str(d.relative_to(repo_root)) for d in docs
                 if d.is_file() and 'rules.md' in d.read_text(encoding='utf-8')]
    assert not offenders, f"stale 'rules.md' references in: {offenders}"


# ---------- shared helper modules (cite_scan.py, bib_parse.py) ----------

def test_cite_scan_iter_cite_calls():
    import cite_scan
    lines = [
        'A~\\cite{x}. % GROUNDING: "x"',
        'Cluster~\\cite{a, b, c}.',
        '% \\cite{ghost}',
        '\\citeauthor{styleonly} text',
        '\\nocite{ignore}',
    ]
    calls = [(cmd, keys) for _, cmd, keys, _, _ in cite_scan.iter_cite_calls(lines)]
    assert ('cite', ['x']) in calls, f"iter: x missing: {calls!r}"
    assert ('cite', ['a', 'b', 'c']) in calls, f"iter: cluster missing: {calls!r}"
    assert all('ghost' not in keys for _, keys in calls), f"iter: commented cite leaked: {calls!r}"
    assert not any(cmd == 'citeauthor' for cmd, _ in calls), f"iter: style-only leaked: {calls!r}"
    assert not any('ignore' in keys for _, keys in calls), f"iter: nocite leaked: {calls!r}"


def test_cite_scan_recognizes_plural_forms():
    import cite_scan
    calls = list(cite_scan.iter_cite_calls([
        r'See \textcites{aa}{bb} and \parencites{cc}{dd}.',
        r'Also \cites{ee} and \autocites{ff}{gg}.',
    ]))
    cmds = {cmd for _, cmd, _, _, _ in calls}
    for plural in ('textcites', 'parencites', 'cites', 'autocites'):
        assert plural in cmds, f"plural form {plural} not recognized: {cmds!r}"
    keys = [k for _, _, ks, _, _ in calls for k in ks]
    # Documented limitation: only the first {key} group is read.
    assert {'aa', 'cc', 'ee', 'ff'} <= set(keys), f"plural first-group keys missing: {keys!r}"
    assert not ({'bb', 'dd', 'gg'} & set(keys)), f"plural second group should be undercounted: {keys!r}"


def test_cite_scan_recognizes_grounding_comment_forms():
    import cite_scan
    grounded = [
        '% GROUNDING: "marker then quote"',
        '% GROUNDING: smith2020 -- "the form insert_grounding writes"',
        '% GROUNDING smith2020: "key before the colon"',
        '% GROUNDING DBLP:conf/icse/BanoGH25: "key with internal colons"',
        '%% GROUNDING foo: "double-percent still counts"',
    ]
    for c in grounded:
        assert cite_scan.is_grounding_comment(c), f"should be grounding: {c!r}"
    not_grounded = [
        '',
        '% a prose comment that merely mentions grounding the claim',
        '% TODO: add a grounding quote here',
        '% GROUNDINGS are plural and not the marker',
    ]
    for c in not_grounded:
        assert not cite_scan.is_grounding_comment(c), f"should NOT be grounding: {c!r}"
    # has_grounding credits the per-key form on the same line and the next line.
    assert cite_scan.has_grounding(
        ['A~\\cite{k}. % GROUNDING k: "x"'], 0, '% GROUNDING k: "x"'), "per-key same-line not credited"
    assert cite_scan.has_grounding(
        ['A~\\cite{k}.', '% GROUNDING k: "x"'], 0, ''), "per-key next-line not credited"


def test_insert_grounding_grounds_key_recognizes_per_key_form():
    import insert_grounding as ig
    # Form this script writes (key after the colon).
    assert ig.grounds_key('% GROUNDING: alpha -- "q"', 'alpha')
    # Per-key form (key before the colon), incl. a DBLP key with internal colons.
    assert ig.grounds_key('% GROUNDING alpha: "q"', 'alpha')
    assert ig.grounds_key('% GROUNDING DBLP:conf/icse/BanoGH25: "q"', 'DBLP:conf/icse/BanoGH25')
    # A key named only inside the quote body does not count as grounding it.
    assert not ig.grounds_key('% GROUNDING alpha: "beta also matters"', 'beta')
    # A non-grounding comment never grounds anything.
    assert not ig.grounds_key('% just a note about alpha', 'alpha')


def test_bib_parse_iter_entries():
    import bib_parse
    text = ('@string{ J = "Journal" }\n'
            '@article{k1, title={T}, author={A}, journal=J, year={2020}, doi={10.1/x}}\n')
    entries = list(bib_parse.iter_entries(text))
    assert len(entries) == 1, f"iter_entries: @string not skipped: {entries!r}"
    key, etype, fields = entries[0]
    assert key == 'k1' and etype == 'article', f"iter_entries: head: {entries!r}"
    assert fields['title'] == 'T' and fields['doi'] == '10.1/x', f"iter_entries: fields: {fields!r}"


# ---------- extract_cites.py ----------

EXTRACT_TEX = (
    "\\documentclass{article}\n"
    "\\bibliography{refs}\n"
    "\\begin{document}\n"
    "Code review reduces defects~\\cite{smith2020}.\n"
    "As shown by \\citet{jones2019}, adoption is slow.\n"
    "A cluster of tools~\\cite{a, b, c}.\n"
    "% commented: \\cite{ghost}\n"
    "Per \\citeauthor{smith2020}, the effect holds.\n"
    "Already noted~\\cite{done2021}. % GROUNDING: done2021 -- \"x\"\n"
    "\\end{document}\n"
)
EXTRACT_BIB = (
    "@inproceedings{smith2020,\n"
    "  title = {A Study of Code Review},\n"
    "  author = {Smith, Jane},\n"
    "  booktitle = {ICSE},\n"
    "  year = {2020},\n"
    "  doi = {10.1145/1234.5678}\n}\n"
)


def test_extract_cites_basic():
    import json
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex', EXTRACT_TEX)
        write(Path(d) / 'refs.bib', EXTRACT_BIB)
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"extract: rc={rc} err={err!r}"
        data = json.loads(out)
        sites = data['sites']
        # 5 sites: smith cite, jones citet, a/b/c cluster, citeauthor, done2021. ghost excluded.
        assert len(sites) == 5, f"extract: expected 5 sites, got {len(sites)}: {sites!r}"
        assert not any('ghost' in s['keys'] for s in sites), f"extract: commented cite leaked: {sites!r}"
        cluster = [s for s in sites if s['keys'] == ['a', 'b', 'c']]
        assert cluster and cluster[0]['groundable'], f"extract: cluster missing/not groundable: {sites!r}"
        author = [s for s in sites if s['command'] == 'citeauthor']
        assert author and author[0]['groundable'] is False, \
            f"extract: citeauthor should be non-groundable: {sites!r}"
        done = [s for s in sites if s['keys'] == ['done2021']]
        assert done and done[0]['grounded'] is True, f"extract: existing grounding not detected: {sites!r}"
        # by_key aggregates smith2020 across its cite + citeauthor sites
        assert len(data['by_key']['smith2020']['sites']) == 2, \
            f"extract: smith2020 should have 2 sites: {data['by_key']['smith2020']!r}"
        # metadata pulled from the .bib for used keys
        assert data['meta']['smith2020']['doi'] == '10.1145/1234.5678', f"extract: meta doi: {data['meta']!r}"
        assert 'Code Review' in data['meta']['smith2020']['title'], f"extract: meta title: {data['meta']!r}"
        assert 'extracted 5 cite site(s)' in err, f"extract: summary: {err!r}"


def test_extract_cites_follows_input():
    import json
    with tempfile.TemporaryDirectory() as d:
        sub = Path(d) / 'sections'
        sub.mkdir()
        write(Path(d) / 'main.tex',
              "\\documentclass{article}\n\\begin{document}\n\\input{sections/intro}\n\\end{document}\n")
        write(sub / 'intro.tex', "A claim~\\cite{deep2023}.\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"extract input: rc={rc} err={err!r}"
        data = json.loads(out)
        assert 'deep2023' in data['by_key'], f"extract input: \\input not followed: {data['by_key']!r}"
        site = data['sites'][0]
        assert site['file'].endswith('intro.tex') and site['line'] == 1, \
            f"extract input: wrong file/line for \\input-ed cite: {site!r}"


def test_extract_cites_no_root_exits_2():
    with tempfile.TemporaryDirectory() as d:
        rc, out, err = run('extract_cites.py', d)
        assert rc == 2, f"extract no-root: rc={rc} out={out!r}"
        assert 'no LaTeX root' in err, f"extract no-root: err={err!r}"


def test_extract_cites_sentence_split_abbrev_aware():
    import extract_cites as ec
    text = 'Smith et al. found gains. The next claim cites other work.'
    bounds = ec.sentence_boundaries(text)
    # "et al." must NOT count as a sentence end; the period after "al" is mid-claim.
    after_al = text.index('al.') + len('al.')
    assert after_al not in bounds, f"sentence split: abbreviation split at 'al.': bounds={bounds}"
    # The real boundary is after "gains." (where "The" begins).
    assert text.index('The') in bounds, f"sentence split: missed real boundary: bounds={bounds}"
    s = ec.enclosing_sentence(text, text.index('et al'), bounds)
    assert s == 'Smith et al. found gains.', f"enclosing sentence: {s!r}"


def test_extract_cites_claim_excludes_preamble_and_structure():
    import json
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex',
              "\\documentclass{article}\n\\usepackage{natbib}\n\\title{My Paper}\n\\author{Me}\n"
              "\\begin{document}\n\\maketitle\n\\section{Related Work}\n\\label{sec:related}\n"
              "Recent advances in deep learning have transformed the field~\\citep{lecun2015}.\n"
              "\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"claim: rc={rc} err={err!r}"
        claim = json.loads(out)['sites'][0]['claim']
        # The first cite of the section must NOT swallow the preamble or heading.
        assert claim == 'Recent advances in deep learning have transformed the field.', \
            f"claim leaked preamble/structural markup: {claim!r}"


def test_extract_cites_claim_stops_at_paragraph_break():
    import json
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex',
              "\\documentclass{a}\n\\begin{document}\nFirst paragraph ends here.\n\n"
              "Second paragraph cites work~\\cite{p}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"para: rc={rc} err={err!r}"
        claim = json.loads(out)['sites'][0]['claim']
        assert claim == 'Second paragraph cites work.', f"claim crossed paragraph break: {claim!r}"


def test_extract_cites_multiline_cite():
    # A \cite whose keys span lines is caught by the joined-text scan (unlike the
    # line-based find_citation_issues); the line maps to the macro's line.
    import json
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex',
              "\\documentclass{a}\n\\begin{document}\nText here~\\cite{m1,\n m2}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"multiline: rc={rc} err={err!r}"
        sites = json.loads(out)['sites']
        assert len(sites) == 1 and sites[0]['keys'] == ['m1', 'm2'], f"multiline: {sites!r}"
        assert sites[0]['line'] == 3, f"multiline: line should be the macro's line: {sites!r}"


def test_extract_cites_addbibresource_and_missing_key_meta():
    import json
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex',
              "\\documentclass{a}\n\\addbibresource{one.bib}\n\\begin{document}\n"
              "Has meta~\\cite{inbib}. No meta~\\cite{notinbib}.\n\\end{document}\n")
        write(Path(d) / 'one.bib',
              "@article{inbib, title={T}, author={A}, journal={J}, year={2020}}\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"addbib: rc={rc} err={err!r}"
        data = json.loads(out)
        assert 'inbib' in data['meta'], f"addbib: \\addbibresource not resolved: {data['meta']!r}"
        assert 'notinbib' not in data['meta'], f"addbib: phantom meta for missing key: {data['meta']!r}"
        assert 'metadata for 1/2 key(s)' in err, f"addbib: summary: {err!r}"


def test_extract_cites_commented_input_skipped():
    # A commented-out \input must not be followed (ghost.tex does not exist; if it
    # were followed the file count would differ).
    import json
    with tempfile.TemporaryDirectory() as d:
        write(Path(d) / 'main.tex',
              "\\documentclass{a}\n\\begin{document}\n% \\input{ghost}\nReal claim~\\cite{k}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"commented input: rc={rc} err={err!r}"
        assert 'scanned 1 file(s)' in err, f"commented input: ghost followed: {err!r}"
        assert 'k' in json.loads(out)['by_key'], "commented input: real cite missing"


def test_extract_cites_ambiguous_roots_exits_2():
    with tempfile.TemporaryDirectory() as d:
        body = "\\documentclass{a}\n\\begin{document}\nx\n\\end{document}\n"
        write(Path(d) / 'aa.tex', body)
        write(Path(d) / 'bb.tex', body)
        rc, out, err = run('extract_cites.py', d)
        assert rc == 2, f"ambiguous: rc={rc} out={out!r}"
        assert 'multiple candidate roots' in err, f"ambiguous: err={err!r}"


# ---------- insert_grounding.py ----------

INSERT_TEX = (
    "\\documentclass{article}\n"
    "\\begin{document}\n"
    "Claim one~\\cite{alpha}.\n"
    "Claim two~\\cite{beta}.\n"
    "\\end{document}\n"
)


def test_insert_grounding_inserts_quote_and_todo_idempotently():
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, INSERT_TEX)
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"insert/extract: rc={rc} err={err!r}"
        extract = Path(d) / 'extract.json'
        write(extract, out)
        quotes = Path(d) / 'quotes.json'
        write(quotes, json.dumps({
            'alpha': {'quote': 'Alpha reduces defects by half.'},
            'beta': {'todo': 'paywalled'},
        }))
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes))
        assert rc == 0, f"insert: rc={rc} err={err!r}"
        body = tex.read_text(encoding='utf-8')
        assert '% GROUNDING: alpha -- "Alpha reduces defects by half."' in body, \
            f"insert: quote not inserted: {body!r}"
        assert '% GROUNDING: beta -- TODO verify -- paywalled' in body, \
            f"insert: TODO not inserted: {body!r}"
        # Anti-fabrication: the unretrieved key gets a TODO, never a quote.
        beta_line = [ln for ln in body.splitlines() if 'GROUNDING: beta' in ln][0]
        assert '"' not in beta_line, f"insert: beta got a fabricated quote: {beta_line!r}"
        assert 'inserted 2 grounding comment(s) (1 quote(s), 1 TODO(s))' in err, f"insert: summary: {err!r}"
        # Re-extract over the now-grounded file and re-insert -> nothing changes.
        rc, out, err = run('extract_cites.py', d)
        write(extract, out)
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes))
        assert rc == 0, f"insert idem: rc={rc} err={err!r}"
        assert 'inserted 0 grounding comment(s)' in err, f"insert idem: re-run changed something: {err!r}"


def test_insert_grounding_dry_run_does_not_write():
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, INSERT_TEX)
        before = tex.read_text(encoding='utf-8')
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'extract.json'
        write(extract, out)
        quotes = Path(d) / 'quotes.json'
        write(quotes, json.dumps({'alpha': {'quote': 'x'}, 'beta': {'todo': 'source-does-not-support'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes), '--dry-run')
        assert rc == 0, f"dry: rc={rc} err={err!r}"
        assert tex.read_text(encoding='utf-8') == before, "dry-run must not modify the file"
        assert 'would insert 2 grounding comment(s)' in err, f"dry: summary: {err!r}"
        assert 'GROUNDING: alpha' in out, f"dry: stdout preview missing: {out!r}"
        # source-does-not-support is surfaced as a likely miscitation.
        assert 'source-does-not-support' in err, f"dry: reason breakdown missing: {err!r}"


def test_insert_grounding_bad_json_exits_2():
    with tempfile.TemporaryDirectory() as d:
        extract = Path(d) / 'extract.json'
        write(extract, '{not valid json')
        quotes = Path(d) / 'quotes.json'
        write(quotes, '{}')
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes))
        assert rc == 2, f"bad json: rc={rc} err={err!r}"
        assert 'not valid JSON' in err, f"bad json: err={err!r}"


def test_insert_grounding_non_dict_extract_exits_2():
    # Well-formed JSON of the wrong shape (a list) must exit 2, not crash with 1.
    with tempfile.TemporaryDirectory() as d:
        extract = Path(d) / 'e.json'
        write(extract, '[]')
        quotes = Path(d) / 'q.json'
        write(quotes, '{}')
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes))
        assert rc == 2, f"non-dict extract: rc={rc} err={err!r}"
        assert 'not a JSON object' in err, f"non-dict extract: err={err!r}"


def test_insert_grounding_blank_quote_becomes_todo():
    # Anti-fabrication: a whitespace-only (or non-string) quote must not produce
    # an empty quoted comment; it is routed to a TODO instead.
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{article}\n\\begin{document}\nA claim~\\cite{wk}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        quotes = Path(d) / 'q.json'
        write(quotes, json.dumps({'wk': {'quote': '   \t  '}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes))
        assert rc == 0, f"blank quote: rc={rc} err={err!r}"
        body = tex.read_text(encoding='utf-8')
        assert '% GROUNDING: wk -- TODO verify' in body, f"blank quote: not routed to TODO: {body!r}"
        assert 'wk -- ""' not in body, f"blank quote: emitted an empty quoted comment: {body!r}"
        assert '0 quote(s), 1 TODO(s)' in err, f"blank quote: miscounted as a quote: {err!r}"


def test_insert_grounding_key_match_ignores_quote_body():
    # grounds_key must look only at the comment header, not the quote body: a key
    # named inside another key's quote must still be groundable on a later run.
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{article}\n\\begin{document}\n"
                   "Both works agree~\\citep{bar2021, foo2020}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        # Ground only bar2021, with a quote that names foo2020.
        write(Path(d) / 'q1.json', json.dumps({'bar2021': {'quote': 'Following foo2020 we extend it.'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q1.json'))
        assert rc == 0, f"key-body/1: rc={rc} err={err!r}"
        # Re-extract, then ground foo2020: it must NOT be treated as already grounded.
        rc, out, err = run('extract_cites.py', d)
        write(extract, out)
        write(Path(d) / 'q2.json', json.dumps({'foo2020': {'quote': 'foo2020 reports a gain.'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q2.json'))
        assert rc == 0, f"key-body/2: rc={rc} err={err!r}"
        body = tex.read_text(encoding='utf-8')
        assert '% GROUNDING: foo2020 -- "foo2020 reports a gain."' in body, \
            f"key-body: foo2020 wrongly skipped (matched inside bar2021's quote): {body!r}"


def test_insert_grounding_preserves_crlf():
    # A CRLF source must stay CRLF after insertion (minimal diff, no LF rewrite).
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        crlf = ("\\documentclass{article}\r\n\\begin{document}\r\n"
                "A claim~\\cite{wk}.\r\n\\end{document}\r\n")
        Path(tex).write_bytes(crlf.encode('utf-8'))
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        quotes = Path(d) / 'q.json'
        write(quotes, json.dumps({'wk': {'quote': 'Supporting evidence.'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(quotes))
        assert rc == 0, f"crlf: rc={rc} err={err!r}"
        raw = Path(tex).read_bytes()
        assert b'% GROUNDING: wk -- "Supporting evidence."\r\n' in raw, \
            f"crlf: inserted comment not CRLF-terminated: {raw!r}"
        # Every newline is part of a CRLF; no bare LF was introduced.
        assert raw.replace(b'\r\n', b'').count(b'\n') == 0, f"crlf: stray LF introduced: {raw!r}"


def test_insert_grounding_cluster_one_comment_per_key_preserves_indent():
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{a}\n\\begin{document}\n    Indented~\\cite{a, b, c}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'q.json',
              json.dumps({'a': {'quote': 'qa'}, 'b': {'todo': 'paywalled'}, 'c': {'quote': 'qc'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0, f"cluster: rc={rc} err={err!r}"
        comments = [ln for ln in tex.read_text(encoding='utf-8').splitlines() if 'GROUNDING:' in ln]
        assert len(comments) == 3, f"cluster: expected one comment per key: {comments!r}"
        assert all(ln.startswith('    %') for ln in comments), \
            f"cluster: indentation not preserved: {comments!r}"
        for frag in ('a -- "qa"', 'b -- TODO verify -- paywalled', 'c -- "qc"'):
            assert any(frag in ln for ln in comments), f"cluster: missing {frag}: {comments!r}"


def test_insert_grounding_resumable_over_absent_keys():
    # A key absent from quotes is left untouched (counted as 'no result'), so a
    # later run fills it — the documented resumability over still-ungrounded sites.
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{a}\n\\begin{document}\nClaim~\\cite{r1}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'empty.json', '{}')
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'empty.json'))
        assert rc == 0 and 'inserted 0' in err and '1 key(s) with no result' in err, f"resume/1: {err!r}"
        assert 'GROUNDING' not in tex.read_text(encoding='utf-8'), "resume/1: file should be untouched"
        rc, out, err = run('extract_cites.py', d)
        write(extract, out)
        write(Path(d) / 'q.json', json.dumps({'r1': {'quote': 'later'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0 and 'inserted 1' in err, f"resume/2: {err!r}"
        assert '% GROUNDING: r1 -- "later"' in tex.read_text(encoding='utf-8'), "resume/2: not filled"


def test_insert_grounding_preserves_missing_final_newline():
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        Path(tex).write_bytes(b"\\documentclass{a}\n\\begin{document}\nClaim~\\cite{k}.\n\\end{document}")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'q.json', json.dumps({'k': {'quote': 'q'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0, f"eofnl: rc={rc} err={err!r}"
        assert not Path(tex).read_bytes().endswith(b'\n'), "eofnl: a trailing newline was added"


def test_insert_grounding_same_line_comment_idempotent():
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{a}\n\\begin{document}\n"
                   "Claim~\\cite{k}. % GROUNDING: k -- \"x\"\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'q.json', json.dumps({'k': {'quote': 'new'}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0 and 'inserted 0' in err and '1 already grounded' in err, f"same-line: {err!r}"
        assert tex.read_text(encoding='utf-8').count('GROUNDING:') == 1, "same-line: grounding duplicated"


def test_insert_grounding_non_string_quote_becomes_todo():
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{a}\n\\begin{document}\nClaim~\\cite{k}.\n\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'q.json', json.dumps({'k': {'quote': ['x', 'y']}}))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0, f"non-str: rc={rc} err={err!r}"
        body = tex.read_text(encoding='utf-8')
        assert '% GROUNDING: k -- TODO verify' in body, f"non-str: not routed to TODO: {body!r}"
        assert "['x', 'y']" not in body, f"non-str: a repr leaked as a quote: {body!r}"


def test_insert_grounding_replaces_todo_stubs():
    # A quote-less TODO stub — the revise-mode form (`% GROUNDING: TODO verify
    # <key>`) or the reasoned form an earlier run wrote — must not block the
    # fill: extract_cites reports the site ungrounded, and insert_grounding
    # replaces the stub line in place with the retrieved quote. Re-running
    # with the same quotes is then a no-op.
    import json
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'main.tex'
        write(tex, "\\documentclass{a}\n\\begin{document}\n"
                   "Claim one~\\cite{rk}.\n"
                   "% GROUNDING: TODO verify rk\n"
                   "Claim two~\\cite{pk}.\n"
                   "% GROUNDING: pk -- TODO verify -- paywalled\n"
                   "\\end{document}\n")
        rc, out, err = run('extract_cites.py', d)
        assert rc == 0, f"stub/extract: rc={rc} err={err!r}"
        sites = json.loads(out)['sites']
        assert all(s['grounded'] is False for s in sites), \
            f"stub/extract: TODO stubs must count as ungrounded: {sites!r}"
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'q.json', json.dumps({
            'rk': {'quote': 'rk evidence.'},
            'pk': {'quote': 'pk evidence from the local PDF.'},
        }))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0, f"stub/insert: rc={rc} err={err!r}"
        assert '2 TODO stub(s) replaced' in err, f"stub/insert: summary: {err!r}"
        body = tex.read_text(encoding='utf-8')
        assert '% GROUNDING: rk -- "rk evidence."' in body, f"stub/insert: rk: {body!r}"
        assert '% GROUNDING: pk -- "pk evidence from the local PDF."' in body, \
            f"stub/insert: pk: {body!r}"
        assert 'TODO verify' not in body, f"stub/insert: a stub survived: {body!r}"
        assert body.count('GROUNDING') == 2, f"stub/insert: comment duplicated: {body!r}"
        # Idempotent: re-extract over the now-grounded file, re-insert -> no-op.
        rc, out, err = run('extract_cites.py', d)
        write(extract, out)
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0 and 'inserted 0 grounding comment(s)' in err, f"stub/idem: {err!r}"


def test_grounding_comment_block_read_write_agree():
    # The read side (find_citation_issues / extract_cites) and the write side
    # (insert_grounding) share one definition of the cite's attached comment
    # block: an unrelated % comment between the cite and its grounding comment
    # does not hide the grounding, a TODO stub marks the cite as not-missing
    # but still fillable, and a comment beyond intervening code is not credited.
    import json
    fixture = (
        'Stubbed~\\cite{sk}.\n'
        '% GROUNDING: TODO verify sk\n'
        '\n'
        'Interleaved~\\cite{ik}.\n'
        '% see also the appendix\n'
        '% GROUNDING: ik -- "ik says yes"\n'
        '\n'
        'Truly missing~\\cite{mk}.\n'
        'Another sentence of prose.\n'
        '% GROUNDING: mk -- "beyond code, not attached"\n'
    )
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / 'paper.tex'
        write(tex, fixture)
        rc, out, err = run('find_citation_issues.py', str(tex))
        assert rc == 0, f"block/issues: rc={rc} err={err!r}"
        missing = [l for l in out.strip().split('\n') if l and '\tmissing-grounding\t' in l]
        assert len(missing) == 1 and '\tmk\t' in missing[0], \
            f"block/issues: expected exactly mk missing: {missing!r}"
        rc, out, err = run('extract_cites.py', str(tex))
        assert rc == 0, f"block/extract: rc={rc} err={err!r}"
        grounded = {s['keys'][0]: s['grounded'] for s in json.loads(out)['sites']}
        assert grounded == {'sk': False, 'ik': True, 'mk': False}, f"block/extract: {grounded!r}"
        extract = Path(d) / 'e.json'
        write(extract, out)
        write(Path(d) / 'q.json', json.dumps({
            'sk': {'quote': 'sk quote'},
            'ik': {'quote': 'new ik quote'},
            'mk': {'quote': 'mk quote'},
        }))
        rc, out, err = run('insert_grounding.py', str(extract), str(Path(d) / 'q.json'))
        assert rc == 0, f"block/insert: rc={rc} err={err!r}"
        assert '1 already grounded' in err, f"block/insert: ik should be left alone: {err!r}"
        assert '1 TODO stub(s) replaced' in err, f"block/insert: sk stub not replaced: {err!r}"
        body = tex.read_text(encoding='utf-8')
        assert '% GROUNDING: sk -- "sk quote"' in body, f"block/insert: sk: {body!r}"
        assert 'new ik quote' not in body, f"block/insert: ik wrongly rewritten: {body!r}"
        assert '% GROUNDING: mk -- "mk quote"' in body, f"block/insert: mk: {body!r}"


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
    test_check_bib_fields_all_unreadable_exits_2,
    test_check_bib_fields_partial_read_exits_0,
    test_find_citation_issues_basic,
    test_find_citation_issues_no_findings,
    test_find_citation_issues_per_key_grounding_not_flagged,
    test_find_citation_issues_optional_args,
    test_find_citation_issues_truncate_respects_120_chars,
    test_find_citation_issues_all_unreadable_exits_2,
    test_find_citation_issues_partial_read_exits_0,
    test_lint_markdown_clean_file,
    test_lint_markdown_trailing_whitespace,
    test_lint_markdown_eof_newline_missing,
    test_lint_markdown_multiple_blank_lines,
    test_lint_markdown_heading_level_jump,
    test_lint_markdown_multiple_h1,
    test_lint_markdown_blanks_around_headings,
    test_lint_markdown_finding_block_missing_label,
    test_lint_markdown_finding_block_clean_passes,
    test_lint_markdown_writing_md_h1_in_tropes_section,
    test_lint_markdown_writing_md_no_tropes_section,
    test_lint_markdown_fix_mode_normalizes,
    test_lint_markdown_fix_mode_preserves_structural_findings,
    test_lint_markdown_unreadable_exits_2,
    test_version_strings_in_sync,
    test_check_baseline_passes_on_bundled_yaml,
    test_detect_scope_file_tex,
    test_detect_scope_file_pdf,
    test_detect_scope_file_markdown,
    test_detect_scope_dir_latex,
    test_detect_scope_dir_pdf,
    test_detect_scope_dir_general,
    test_detect_scope_dir_empty_defaults_general,
    test_detect_scope_commented_tex_is_not_latex,
    test_scan_repo_prose_markdown_skips_code_fences,
    test_scan_repo_extracts_only_comments_from_source,
    test_scan_repo_hash_comments_not_values,
    test_scan_repo_skips_generated_file,
    test_scan_repo_skips_lockfile_and_binary,
    test_scan_repo_walk_prunes_denylisted_dirs,
    test_scan_repo_respects_gitignore,
    test_scan_repo_excludes_committed_vendor_dir,
    test_scan_repo_not_a_directory_exits_2,
    test_scan_repo_summary_on_stderr,
    test_scan_repo_python_docstring_and_hash,
    test_scan_repo_shell_comments_skip_shebang,
    test_scan_repo_java_javadoc_and_line,
    test_scan_repo_js_ts_block_and_line,
    test_scan_repo_latex_body_and_comments,
    test_scan_repo_commit_messages_scanned,
    test_scan_repo_no_commits_flag_suppresses,
    test_scan_repo_commits_count_selector,
    test_scan_repo_bad_commits_value_is_usage_error,
    test_rule_layers_exist,
    test_rule_layers_lint_clean,
    test_no_dangling_rules_md_references,
    test_verify_references_parses_bib,
    test_verify_references_compare_verdicts,
    test_verify_references_doi_paths,
    test_verify_references_offline,
    test_verify_references_no_doi_paths,
    test_verify_references_subprocess_unchecked_no_network,
    test_verify_references_all_unreadable_exits_2,
    test_verify_references_partial_read_exits_0,
    test_cite_scan_iter_cite_calls,
    test_cite_scan_recognizes_plural_forms,
    test_cite_scan_recognizes_grounding_comment_forms,
    test_insert_grounding_grounds_key_recognizes_per_key_form,
    test_bib_parse_iter_entries,
    test_extract_cites_basic,
    test_extract_cites_follows_input,
    test_extract_cites_no_root_exits_2,
    test_extract_cites_sentence_split_abbrev_aware,
    test_extract_cites_claim_excludes_preamble_and_structure,
    test_extract_cites_claim_stops_at_paragraph_break,
    test_extract_cites_multiline_cite,
    test_extract_cites_addbibresource_and_missing_key_meta,
    test_extract_cites_commented_input_skipped,
    test_extract_cites_ambiguous_roots_exits_2,
    test_insert_grounding_inserts_quote_and_todo_idempotently,
    test_insert_grounding_dry_run_does_not_write,
    test_insert_grounding_bad_json_exits_2,
    test_insert_grounding_non_dict_extract_exits_2,
    test_insert_grounding_blank_quote_becomes_todo,
    test_insert_grounding_key_match_ignores_quote_body,
    test_insert_grounding_preserves_crlf,
    test_insert_grounding_cluster_one_comment_per_key_preserves_indent,
    test_insert_grounding_resumable_over_absent_keys,
    test_insert_grounding_preserves_missing_final_newline,
    test_insert_grounding_same_line_comment_idempotent,
    test_insert_grounding_non_string_quote_becomes_todo,
    test_insert_grounding_replaces_todo_stubs,
    test_grounding_comment_block_read_write_agree,
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
