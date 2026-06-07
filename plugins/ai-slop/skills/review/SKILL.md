---
name: review
description: Review a document (LaTeX, PDF, or plain prose) for AI slop and rule violations. Use when the user names a draft, hands you a path to a `.tex`, `.pdf`, or text file, or asks to check, audit, or review prose for AI tropes — and, for research papers, statistical reporting, citations, BibTeX correctness, and hallucinated references. The general rules apply by default; `--scientific` adds the scientific layer and LaTeX source loads all three. Writes a structured Markdown report with concrete suggested revisions that revise mode can apply.
license: CC-BY-4.0
metadata:
  version: "2026-05_rev21"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review — Review Mode

This skill checks a document (LaTeX, PDF, or plain prose) for AI slop and rule violations and produces a structured report. The bundled files live at `../../shared/`.

**Audience and tone.** The default user is an author reviewing their own draft. Frame findings as suggestions for clearer prose, not as violations. If a co-author or reviewer invokes this skill, treat the output as a starting point for revision, not as a rejection rubric.

## When to use

Invoke this skill when the user:

1. Asks to check a draft for AI slop, prose tics, or rule violations.
2. Hands you a path to a `.tex`, `.pdf`, or text file, or runs `/ai-slop:review` from the project directory.
3. Is preparing a draft for submission and wants a final pass.

Do **not** invoke for unrelated SE work that happens to mention writing. If the user wants to apply an existing report's findings, switch to `/ai-slop:revise`.

## Inputs

The skill auto-detects the paper in the current working directory. No path argument is required.

**Auto-detection.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_latex_root.py`. Exit 0 means the printed path is the LaTeX root — use it. Exit 2 means multiple candidate roots were printed (none named `main.tex` or `paper.tex`); list them to the user and ask which to review. Exit 1 means no `.tex` root exists in the tree; fall back to listing `.pdf` files in the working directory — if exactly one is present, use it; if multiple, ask the user; if none, stop and tell the user (e.g., "No `.tex` or `.pdf` found in the current directory.").

**Reading the paper.**

- LaTeX source (`.tex`): read the root and follow `\input{}` / `\include{}` for files inside the project tree. A flattened `.tex` works the same way.
- PDF (`.pdf`): extract text using whatever tool is available in the environment (`pdftotext`, `mutool draw -F txt`, or a Python library). If no extractor is available, tell the user which one to install rather than failing silently.

When both LaTeX source and PDF are available for the same paper, prefer the LaTeX source. It exposes LaTeX-specific artifacts (e.g., commented-out disclosures, `\todo{}` notes, missing `% GROUNDING:` comments, spelled-out author names that should use `\citeauthor{}`) that get lost in the PDF.

**Optional path override.** If the user passes a path to a `.tex` or `.pdf` as an argument, use that instead of scanning. A path to a plain-text file (`.md`, `.txt`, or similar) is also accepted and reviewed with the general layer (add `--scientific` to include the research-article rules; see step 2), so the skill works on prose that is not a LaTeX or PDF paper.

**Trope catalog override.** `--tropes=<path>` (repeatable) replaces the default fetch with one or more user-supplied files. Paths can be absolute or relative to the working directory; each file is read as-is and the contents are concatenated in the order given to form the catalog for this run. When `--tropes` is not passed (the common case), the catalog is fetched live — see step 3.

## Workflow

1. **Resolve inputs.** Auto-detect the paper as described in Inputs (or use the path the user supplied). Parse any `--tropes=<path>` arguments from the user's message; collect them as a list. Open the paper file (or extract text from PDF) and identify its sections (e.g., Abstract, Introduction, Related Work, Method, Results, Discussion, Threats to Validity, Conclusion, Future Work). For LaTeX, follow `\section{}` and `\subsection{}` markers.

2. **Determine which rule layers to load.** Three layers live under `../../shared/`:
   - `rules-general.md` — always loaded (language, restricted vocabulary, terminology, active voice, punctuation, structure, tone, prose self-check).
   - `rules-scientific.md` — research-article conventions (research-coded phrases, the "significant" caveat, verb tense by section, citations, numbers and statistics, figures and tables, threats to validity).
   - `rules-latex.md` — LaTeX-source mechanics (LaTeX quotes, run-in caption punctuation, cross-reference and `\citeauthor` macros, `% GROUNDING` comments, BibTeX).

   Decide as follows:
   - **Is it LaTeX?** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/detect_scope.py <resolved-paper-path>`. Output `latex` means LaTeX source: load all three layers (a LaTeX paper is a research article, so the scientific layer comes along automatically). Output `general` means anything else — Markdown, plain text, or PDF.
   - **Research article?** For `general` input, also load `rules-scientific.md` when the user passed `--scientific`, to treat a non-LaTeX manuscript (a Markdown or PDF paper) as a research article. Without the flag, load `rules-general.md` only.

   Read each selected layer file. Each contributes its own rules and its own self-check section; apply them together. A finding's `Rule` name comes from whichever layer defines it.

3. **Load the AI-trope catalog.** If `--tropes=<path>` was passed (one or more times), read each named file and concatenate them in the order given; that is the catalog for this run. Otherwise run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py ${CLAUDE_SKILL_DIR}/../../shared/tropes-snapshot.md` and read its stdout. The script tries the upstream Gist, then the tropes.fyi viewer, then the bundled fallback, and always emits a non-empty body; it prints one line to stderr identifying which source was used.

4. **Per-section pass.** For each paper section, scan the prose against the rules and the trope catalog. For each violation, record:
   - The rule or trope name.
   - The location (`file:line` for LaTeX; `Section: <name>` for PDF).
   - A short verbatim quote of the offending text, with enough surrounding context to make the quote unique within the paper.
   - A concrete suggested replacement that follows the rules.

5. **Cross-cutting metrics.** Compute and record the metrics whose layer is in scope (skip the scientific ones — verb-tense compliance, the "significant" audit — when only the general layer is loaded):
   - Em-dash density (target: ≤ 2 per page-equivalent of ~350 words).
   - Colon density in running prose (target: ≤ 2 per page-equivalent).
   - Capitalization after a colon in running prose (flag colons whose post-colon clause is a complete sentence beginning lowercase, and flag colons whose post-colon text is a fragment or list beginning uppercase).
   - Semicolon density in running prose (target: ≤ 1 to 2 per page-equivalent).
   - Combined pause-punctuation signal (combined em-dash + colon + semicolon count per page-equivalent; a page near all three caps at once is over-punctuated).
   - Restricted-word density per paragraph (flag paragraphs with more than 2 to 3 occurrences).
   - Sentence-length variance (flag stretches of three or more consecutive sentences within 5 words of each other in length).
   - Verb-tense compliance by section (compare against the table in the scientific layer; only when that layer is in scope).
   - American-vs-British spelling (flag British variants).
   - "Significant" audit (flag non-statistical uses).

   These counts are secondary signals, not the findings. A page can sit within every target above and still contain an individual mark that is the wrong choice. When a specific em-dash, colon, or semicolon should be a different mark, record it as a per-section finding under step 4 (with the corrected punctuation as the suggested revision), regardless of the per-page count. The most common case is a semicolon joining two independent clauses that a period would separate, especially when the second clause opens with we, it, this, they, or these. An em-dash standing in for a period, and a colon used as a generic mid-sentence pause, are promoted the same way.

6. **Citations and BibTeX (LaTeX only).** Scan for:
   - Citation clusters with three or more keys, and `\cite{}` calls without a nearby `% GROUNDING: "..."` comment. Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_citation_issues.py <root.tex> [<input1.tex> ...]` over the LaTeX root and any `\input`-ed files. Each stdout line is `<file>:<line>\t<issue>\t<keys>\t<context>` where `<issue>` is `cluster` or `missing-grounding`. The script prints a stderr summary (e.g. `considered 41 cite call(s) across 1 file(s); 1 cluster(s), 41 missing-grounding`). Use it to confirm the run completed. Known limitations of the scan:
     - The script does not follow `\input` / `\include`. Pass the file list explicitly.
     - Multi-line `\cite{}` calls (where `}` is on a different line from `\cite{`) are skipped.
     - Biblatex multi-cite forms (`\textcites`, `\autocites`, `\fullcites`) read only the first key group.
     - "Nearby grounding" means same line or the next non-blank line. A comment placed two or more blank-separated lines after the cite is not credited.
   - For each cluster, only flag it as a finding if the surrounding prose does not explain what each cited work contributes. A cluster followed by sentences that distinguish each work is fine.
   - For missing-grounding, always surface the result as a **Grounding to-do** list in the report: every `\cite{}` lacking a `% GROUNDING:` comment, by `file:line` and key. This list is always emitted, not a project-internal decision.
   - Spelled-out author names that should use `\citeauthor{}`. The script does not check this. Scan manually.
   - `.bib` entries with missing required fields. To find the bib files, grep the LaTeX root (and any `\input`-ed files) for `\bibliography{...}` and `\addbibresource{...}` directives and resolve each path. If at least one is found, run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/check_bib_fields.py <bibfile1> <bibfile2> ...` and report each printed entry as a finding. The script uses standard BibTeX required-field semantics (Patashnik's `btxdoc`) and does not honor `crossref` inheritance, so sanity-check flagged entries before reporting them, and skip the check entirely if no bib files are referenced. The script always prints a one-line summary to stderr (e.g. `checked 142 entries across 1 file(s), 0 missing-field issue(s)`). Use it to confirm the run completed.
   - Hallucinated or mismatched references. After the field check, run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/verify_references.py <bibfile1> [<bibfile2> ...] [--mailto you@example.org]` over the same `.bib` files. It looks each entry up in CrossRef (by DOI, then title) and DBLP (by title) and prints one tab-separated line per entry that is not cleanly verified: `<key>\t<verdict>\t<detail>`, where `<verdict>` is `doi-not-found`, `title-mismatch`, `year-mismatch`, `venue-mismatch`, `not-found`, `unchecked-offline`, or `unchecked`. Report these under **Reference verification**. This check is advisory and online-first: with no network every entry returns `unchecked-offline` and the run still exits 0. Never assert a reference is fabricated from eyeballing — treat `doi-not-found` and `not-found` as likely-fabricated only after a sanity check, and for entries the databases cannot confirm, do a web search to validate before flagging. DBLP's curated BibTeX is the canonical record for CS/SE venues; prefer the publisher/DOI metadata only when DBLP holds just a preprint of a now-published paper. For an exhaustive non-LLM audit of someone else's submission, point the user to the `hallucite` skill.

7. **Write the report.** Save the assessment as `ai-slop-report.md` in the user's current working directory. The report is a generated artifact and must never be committed: if the working directory is inside a git repository and its `.gitignore` does not already list `ai-slop-report.md`, append that line (creating `.gitignore` if absent).

   Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-report.md`. If the linter exits non-zero, read its stdout findings (one per line, tab-separated `<file>:<line>\t<rule>\t<message>`), revise the report in place to address each, and re-run the linter. Repeat at most three iterations; after the third pass proceed regardless of the linter's state. The lint loop is internal quality control — do not mention lint output, rule names, exit codes, or iteration counts in the user-facing summary.

   Then Read the file back and quote its contents verbatim in your reply — do **not** regenerate the report text from memory for the inline echo, which has triggered repetition glitches (duplicate disclaimer blockquotes and `## Summary` headings). Echoing the Read result keeps the printed version identical to the file. Use the report template below.

8. **Stop after the report.** Do not modify the paper. If the user wants the findings applied, route them to `/ai-slop:revise`.

## Report template

The report's schema is stable so revise mode can parse it. Each finding has `Rule`, `Location`, `Quote`, and `Suggested revision`; revise mode locates the `Quote` in the paper and replaces it with `Suggested revision`.

````markdown
# AI Slop Review

**Paper:** <path>
**Skill version:** 2026-05_rev21 <!-- maintainer: bump on every release; see README "Maintainer notes" -->
**Reviewed:** <ISO 8601 date>

> This report applies the writing rules at
> <https://github.com/se-uhd/ai-slop-skill> as a self-check.
> Findings are revision suggestions; nothing is grounds for rejection.

## Summary

<Two to four sentences. What reads well, what needs revision, headline metrics.>

## Findings by section

### <Section name, e.g., Abstract>

#### Finding <N>

- **Rule:** <rule name from a rule layer, or trope name from tropes.fyi>
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

### Combined pause-punctuation signal
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
- Spelled-out author names that should use `\citeauthor{}`: <list>

### Grounding to-do
- `\cite{}` calls with no `% GROUNDING:` comment (always listed): <file:line — keys>

### BibTeX (if applicable)
- Entries with missing or unverifiable required fields: <list>

### Reference verification (if applicable)
- Entries flagged by `verify_references.py`, with verdict and detail: <list>
- Entries returned `unchecked-offline` (no network at review time): <list>

## Items requiring author judgment

<Findings the skill cannot resolve automatically: terminology choices, threats-to-validity specificity,
gap statements in related work, hedging that depends on evidence the skill has not assessed.
Phrase each as a suggestion, not a command. Revise mode will not act on these.>
````

## Bundled files

- `../../shared/rules-general.md`, `../../shared/rules-scientific.md`, and `../../shared/rules-latex.md` are the three rule layers (general prose; research-article conventions; LaTeX mechanics). Load the subset the scope calls for (step 2).
- `../../shared/tropes-snapshot.md` is the offline fallback the trope-fetch script falls through to when the upstream Gist and tropes.fyi viewer are both unreachable.
- `../../scripts/find_latex_root.py`, `../../scripts/fetch_tropes.py`, `../../scripts/find_citation_issues.py`, `../../scripts/check_bib_fields.py` implement the deterministic checks above; their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Quote verbatim.** The `Quote` field must match the paper text exactly, with enough surrounding context to be unique. Revise mode relies on exact-match lookup.
- **Suggest concrete revisions.** Avoid vague guidance ("rewrite to be clearer"). Where a rule has a specific replacement (a banned phrase, a restricted word, a tense correction), provide it. For judgment-call findings, put them in "Items requiring author judgment" rather than "Findings by section".
- **Reformulate, do not delete.** A `Suggested revision` should rewrite the flagged text into a compliant form that preserves the author's content. Propose deletion only for genuine empty filler (padding and windup sentences per the concision rules, non-evidence-based hedges) or when the author has asked for cuts. Do not resolve a flagged substantive claim, example, or qualification by removing it.
- **Do not editorialize.** Do not flag stylistic choices the rules do not address (e.g., theoretical contribution, novelty argument, narrative structure, general readability), even if you notice them.
- **Do not modify the paper.** Review mode writes only `ai-slop-report.md` in the working directory.
