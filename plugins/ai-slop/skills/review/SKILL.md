---
name: review
description: Review a paper draft (LaTeX source or PDF) for AI slop and violations of the SE writing rules. Use when the user names a paper, hands you a path to a `.tex` or `.pdf`, asks to check, audit, or review a draft for AI tropes, statistical reporting, citation style, voice and tense, BibTeX correctness, or APA/IEEE/ACM conventions. Writes a structured Markdown report with concrete suggested revisions that revise mode can apply.
license: CC-BY-4.0
metadata:
  version: "2026-05_rev15"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review — Review Mode

This skill checks a paper draft for AI slop and violations of the SE writing rules and produces a structured report. The bundled files live at `../../shared/`.

**Audience and tone.** The default user is an author reviewing their own draft. Frame findings as suggestions for clearer prose, not as violations. If a co-author or reviewer invokes this skill, treat the output as a starting point for revision, not as a rejection rubric.

## When to use

Invoke this skill when the user:

1. Asks to check a paper draft for AI slop, prose tics, or rule violations.
2. Hands you a path to a `.tex` or `.pdf`, or runs `/ai-slop:review` from the paper's directory.
3. Is preparing a draft for submission and wants a final pass.

Do **not** invoke for unrelated SE work that happens to mention writing. If the user wants to apply an existing report's findings, switch to `/ai-slop:revise`.

## Inputs

The skill auto-detects the paper in the current working directory. No path argument is required.

**Auto-detection.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_latex_root.py`. Exit 0 means the printed path is the LaTeX root — use it. Exit 2 means multiple candidate roots were printed (none named `main.tex` or `paper.tex`); list them to the user and ask which to review. Exit 1 means no `.tex` root exists in the tree; fall back to listing `.pdf` files in the working directory — if exactly one is present, use it; if multiple, ask the user; if none, stop and tell the user (e.g., "No `.tex` or `.pdf` found in the current directory.").

**Reading the paper.**

- LaTeX source (`.tex`): read the root and follow `\input{}` / `\include{}` for files inside the project tree. A flattened `.tex` works the same way.
- PDF (`.pdf`): extract text using whatever tool is available in the environment (`pdftotext`, `mutool draw -F txt`, or a Python library). If no extractor is available, tell the user which one to install rather than failing silently.

When both LaTeX source and PDF are available for the same paper, prefer the LaTeX source. It exposes LaTeX-specific artifacts (e.g., commented-out disclosures, `\todo{}` notes, missing `% GROUNDING:` comments, spelled-out author names that should use `\citeauthor{}`) that get lost in the PDF.

**Optional path override.** If the user passes a path to a `.tex` or `.pdf` as an argument, use that instead of scanning.

**Trope catalog override.** `--tropes=<path>` (repeatable) replaces the default fetch with one or more user-supplied files. Paths can be absolute or relative to the working directory; each file is read as-is and the contents are concatenated in the order given to form the catalog for this run. When `--tropes` is not passed (the common case), the catalog is fetched live — see step 3.

## Workflow

1. **Resolve inputs.** Auto-detect the paper as described in Inputs (or use the path the user supplied). Parse any `--tropes=<path>` arguments from the user's message; collect them as a list. Open the paper file (or extract text from PDF) and identify its sections (e.g., Abstract, Introduction, Related Work, Method, Results, Discussion, Threats to Validity, Conclusion, Future Work). For LaTeX, follow `\section{}` and `\subsection{}` markers.

2. **Load the rule set.** Read `../../shared/rules.md` for the SE-specific rules: language conventions, the restricted-vocabulary table with alternatives, the "significant" statistical caveat, terminology consistency, voice and verb tense by section, punctuation (em-dash, colon, and semicolon caps; capitalization after a colon; the combined pause-punctuation budget), structure, tone, citation style, statistical reporting, figures and tables, threats to validity, BibTeX verification, and the 25-item self-check.

3. **Load the AI-trope catalog.** If `--tropes=<path>` was passed (one or more times), read each named file and concatenate them in the order given; that is the catalog for this run. Otherwise run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py ${CLAUDE_SKILL_DIR}/../../shared/tropes-snapshot.md` and read its stdout. The script tries the upstream Gist, then the tropes.fyi viewer, then the bundled fallback, and always emits a non-empty body; it prints one line to stderr identifying which source was used.

4. **Per-section pass.** For each paper section, scan the prose against the rules and the trope catalog. For each violation, record:
   - The rule or trope name.
   - The location (`file:line` for LaTeX; `Section: <name>` for PDF).
   - A short verbatim quote of the offending text, with enough surrounding context to make the quote unique within the paper.
   - A concrete suggested replacement that follows the rules.

5. **Cross-cutting metrics.** Compute and record:
   - Em-dash density (target: ≤ 2 per page-equivalent of ~350 words).
   - Colon density in running prose (target: ≤ 2 per page-equivalent).
   - Capitalization after a colon in running prose (flag colons whose post-colon clause is a complete sentence beginning lowercase, and flag colons whose post-colon text is a fragment or list beginning uppercase).
   - Semicolon density in running prose (target: ≤ 1 to 2 per page-equivalent).
   - Combined pause-punctuation budget (combined em-dash + colon + semicolon count per page-equivalent; target ≤ 5).
   - Restricted-word density per paragraph (flag paragraphs with more than 2 to 3 occurrences).
   - Sentence-length variance (flag stretches of three or more consecutive sentences within 5 words of each other in length).
   - Verb-tense compliance by section (compare against the table in `rules.md`).
   - American-vs-British spelling (flag British variants).
   - "Significant" audit (flag non-statistical uses).

6. **Citations and BibTeX (LaTeX only).** Scan for:
   - Citation clusters with three or more keys, and `\cite{}` calls without a nearby `% GROUNDING: "..."` comment. Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_citation_issues.py <root.tex> [<input1.tex> ...]` over the LaTeX root and any `\input`-ed files. Each stdout line is `<file>:<line>\t<issue>\t<keys>\t<context>` where `<issue>` is `cluster` or `missing-grounding`. The script prints a stderr summary (e.g. `considered 41 cite call(s) across 1 file(s); 1 cluster(s), 41 missing-grounding`). Use it to confirm the run completed. Known limitations of the scan:
     - The script does not follow `\input` / `\include`. Pass the file list explicitly.
     - Multi-line `\cite{}` calls (where `}` is on a different line from `\cite{`) are skipped.
     - Biblatex multi-cite forms (`\textcites`, `\autocites`, `\fullcites`) read only the first key group.
     - "Nearby grounding" means same line or the next non-blank line. A comment placed two or more blank-separated lines after the cite is not credited.
   - For each cluster, only flag it as a finding if the surrounding prose does not explain what each cited work contributes. A cluster followed by sentences that distinguish each work is fine.
   - For missing-grounding, the output is informational. Whether to ask the author to add `% GROUNDING:` comments is a project-internal decision.
   - Spelled-out author names that should use `\citeauthor{}`. The script does not check this. Scan manually.
   - `.bib` entries with missing required fields. To find the bib files, grep the LaTeX root (and any `\input`-ed files) for `\bibliography{...}` and `\addbibresource{...}` directives and resolve each path. If at least one is found, run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/check_bib_fields.py <bibfile1> <bibfile2> ...` and report each printed entry as a finding. The script uses standard BibTeX required-field semantics (Patashnik's `btxdoc`) and does not honor `crossref` inheritance, so sanity-check flagged entries before reporting them, and skip the check entirely if no bib files are referenced. The script always prints a one-line summary to stderr (e.g. `checked 142 entries across 1 file(s), 0 missing-field issue(s)`). Use it to confirm the run completed.

7. **Write the report.** Save the assessment as `ai-slop-report.md` in the user's current working directory.

   Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-report.md`. If the linter exits non-zero, read its stdout findings (one per line, tab-separated `<file>:<line>\t<rule>\t<message>`), revise the report in place to address each, and re-run the linter. Repeat at most three iterations; after the third pass proceed regardless of the linter's state. The lint loop is internal quality control — do not mention lint output, rule names, exit codes, or iteration counts in the user-facing summary.

   Then Read the file back and quote its contents verbatim in your reply — do **not** regenerate the report text from memory for the inline echo, which has triggered repetition glitches (duplicate disclaimer blockquotes and `## Summary` headings). Echoing the Read result keeps the printed version identical to the file. Use the report template below.

8. **Stop after the report.** Do not modify the paper. If the user wants the findings applied, route them to `/ai-slop:revise`.

## Report template

The report's schema is stable so revise mode can parse it. Each finding has `Rule`, `Location`, `Quote`, and `Suggested revision`; revise mode locates the `Quote` in the paper and replaces it with `Suggested revision`.

````markdown
# AI Slop Review

**Paper:** <path>
**Skill version:** 2026-05_rev15 <!-- maintainer: bump on every release; see README "Maintainer notes" -->
**Reviewed:** <ISO 8601 date>

> This report applies the writing rules at
> <https://github.com/se-uhd/ai-slop-skill> as a self-check.
> Findings are revision suggestions; nothing is grounds for rejection.

## Summary

<Two to four sentences. What reads well, what needs revision, headline metrics.>

## Findings by section

### <Section name, e.g., Abstract>

#### Finding <N>

- **Rule:** <rule name from rules.md, or trope name from tropes.fyi>
- **Location:** `<file:line>` or `Section: <name>` if line not available
- **Quote:** `<verbatim quote of the offending text, with enough surrounding context to be unique>`
- **Suggested revision:** `<concrete replacement text>`

<Repeat per finding within the section.>

### <Next section>
...

## Cross-cutting metrics

### Em-dash density
- Per-page-equivalent count: <N> (target: ≤ 2)
- Locations: <list>

### Colon density (running prose)
- Per-page-equivalent count: <N> (target: ≤ 2)
- Locations: <list>

### Capitalization after a colon
- Colons followed by a complete sentence with a lowercase first word: <list>
- Colons followed by a fragment or list with an uppercase first word: <list>

### Semicolon density (running prose)
- Per-page-equivalent count: <N> (target: ≤ 1 to 2)
- Locations: <list>

### Combined pause-punctuation budget
- Per-page-equivalent count (em-dash + colon + semicolon): <N> (target: ≤ 5)
- Pages over the combined cap: <list>

### Restricted-word density
- Paragraphs over threshold: <list with paragraph pointers>

### Verb-tense compliance
- Sections with non-conforming default tense: <list>

### Spelling (American vs. British)
- British variants found: <list>

### "Significant" audit
- Non-statistical uses: <list>

### Citations
- Citation clusters lacking per-work explanation: <list>
- Missing `% GROUNDING:` comments: <list>
- Spelled-out author names that should use `\citeauthor{}`: <list>

### BibTeX (if applicable)
- Entries with missing or unverifiable required fields: <list>

## Items requiring author judgment

<Findings the skill cannot resolve automatically: terminology choices, threats-to-validity specificity,
gap statements in related work, hedging that depends on evidence the skill has not assessed.
Phrase each as a suggestion, not a command. Revise mode will not act on these.>
````

## Bundled files

- `../../shared/rules.md` for the SE-specific rule set.
- `../../shared/tropes-snapshot.md` is the offline fallback the trope-fetch script falls through to when the upstream Gist and tropes.fyi viewer are both unreachable.
- `../../scripts/find_latex_root.py`, `../../scripts/fetch_tropes.py`, `../../scripts/find_citation_issues.py`, `../../scripts/check_bib_fields.py` implement the deterministic checks above; their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Quote verbatim.** The `Quote` field must match the paper text exactly, with enough surrounding context to be unique. Revise mode relies on exact-match lookup.
- **Suggest concrete revisions.** Avoid vague guidance ("rewrite to be clearer"). Where a rule has a specific replacement (a banned phrase, a restricted word, a tense correction), provide it. For judgment-call findings, put them in "Items requiring author judgment" rather than "Findings by section".
- **Do not editorialize.** Do not flag stylistic choices the rules do not address (e.g., theoretical contribution, novelty argument, narrative structure, general readability), even if you notice them.
- **Do not modify the paper.** Review mode writes only `ai-slop-report.md` in the working directory.
