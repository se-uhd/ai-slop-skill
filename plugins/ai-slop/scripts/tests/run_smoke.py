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
    test_find_citation_issues_truncate_respects_120_chars,
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
    test_version_strings_in_sync,
    test_detect_scope_file_tex,
    test_detect_scope_file_pdf,
    test_detect_scope_file_markdown,
    test_detect_scope_dir_latex,
    test_detect_scope_dir_pdf,
    test_detect_scope_dir_general,
    test_detect_scope_dir_empty_defaults_general,
    test_detect_scope_commented_tex_is_not_latex,
    test_rule_layers_exist,
    test_rule_layers_lint_clean,
    test_no_dangling_rules_md_references,
    test_verify_references_parses_bib,
    test_verify_references_compare_verdicts,
    test_verify_references_doi_paths,
    test_verify_references_offline,
    test_verify_references_no_doi_paths,
    test_verify_references_subprocess_unchecked_no_network,
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
