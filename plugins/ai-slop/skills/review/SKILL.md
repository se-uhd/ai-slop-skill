---
name: review
description: Review a paper draft (LaTeX source or PDF) for AI slop and violations of the SE writing rules. Use when the user names a paper, hands you a path to a `.tex` or `.pdf`, asks to check, audit, or review a draft for AI tropes, statistical reporting, citation style, voice and tense, BibTeX correctness, or APA/IEEE/ACM conventions. Writes a structured Markdown report with concrete suggested revisions that revise mode can apply.
version: 2026-05-09
homepage: https://github.com/se-uhd/ai-slop-skill
license: CC-BY-4.0
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

**Auto-detection.** List the `.tex` files in the working directory (non-recursive) and identify the LaTeX root — the file containing `\documentclass{}` and `\begin{document}`. If exactly one root is found, use it. If multiple roots are found, prefer `main.tex` or `paper.tex`; otherwise list them and ask the user. If no `.tex` files are found, list `.pdf` files; if exactly one is present, use it, and if multiple are present, ask the user. If neither `.tex` nor `.pdf` is present, stop and tell the user (e.g., "No `.tex` or `.pdf` found in the current directory.").

**Reading the paper.**

- LaTeX source (`.tex`): read the root and follow `\input{}` / `\include{}` for files inside the project tree. A flattened `.tex` works the same way.
- PDF (`.pdf`): extract text using whatever tool is available in the environment (`pdftotext`, `mutool draw -F txt`, or a Python library). If no extractor is available, tell the user which one to install rather than failing silently.

When both LaTeX source and PDF are available for the same paper, prefer the LaTeX source. It exposes LaTeX-specific artifacts (e.g., commented-out disclosures, `\todo{}` notes, missing `% GROUNDING:` comments, spelled-out author names that should use `\citeauthor{}`) that get lost in the PDF.

**Optional path override.** If the user passes a path to a `.tex` or `.pdf` as an argument, use that instead of scanning.

**Trope catalog overrides (corner case).** The default catalog source is the live-fetch chain documented in step 4 (upstream Gist -> tropes.fyi viewer -> bundled `../../shared/tropes-snapshot.md`). Most users will never need to override it. The mechanisms below only apply when a user explicitly opts in for a particular run; nothing in the working directory is consulted otherwise.

- `--tropes=<path>` argument: load the catalog from that file for this run. The path can be absolute or relative to the working directory. The file is read as-is and not copied or modified.
- `--refresh-tropes` argument: fetch the upstream Gist and write it to `./tropes-snapshot.cache.md` (creating or overwriting it), then run this review against that fresh copy.
- `--edit-tropes` argument (or a conversational request such as "let me update the tropes first", "I want to add a custom trope"): seed `./tropes-snapshot.cache.md` from upstream (or the bundled fallback if upstream is unreachable) when it does not yet exist, then pause and let the user edit it. Once the user confirms they are done, run this review against the edited cache.

`./tropes-snapshot.cache.md` is a per-workspace artifact written only by the two flags above; it is never read implicitly. To reuse it on a later run the user passes `--tropes=./tropes-snapshot.cache.md` explicitly. None of the override flags ever modify files inside the plugin install tree.

## Workflow

1. **Resolve inputs.** Auto-detect the paper as described in Inputs (or use the path the user supplied). Parse any trope catalog overrides (`--tropes=<path>`, `--refresh-tropes`, `--edit-tropes`) from the user's arguments or message. Open the paper file (or extract text from PDF) and identify its sections (e.g., Abstract, Introduction, Related Work, Method, Results, Discussion, Threats to Validity, Conclusion, Future Work). For LaTeX, follow `\section{}` and `\subsection{}` markers.

2. **Apply trope catalog overrides (rare).** Skip this step entirely unless the user explicitly opted in via one of the flags listed under "Trope catalog overrides" — the default flow goes straight from step 1 to step 3 with no working-directory file lookup. When an override is requested, all writes target `./tropes-snapshot.cache.md` in the working directory; never modify files inside the plugin install tree.
   - `--refresh-tropes`: fetch `https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/` and write the body to `./tropes-snapshot.cache.md`, overwriting it if present. Record the cache path for step 4. If the fetch fails, tell the user and continue the review with the default live-fetch chain rather than aborting.
   - `--tropes=<path>`: verify the file exists and is readable; record its path for step 4. Do not seed or touch `./tropes-snapshot.cache.md`.
   - `--edit-tropes` or an equivalent conversational request: ensure `./tropes-snapshot.cache.md` exists by seeding it from the live-fetch chain (upstream Gist -> tropes.fyi viewer -> bundled `../../shared/tropes-snapshot.md`) if missing; if it already exists, leave it alone. Pause and tell the user the file is ready for them to edit; once they confirm, record the cache path for step 4.

3. **Load the rule set.** Read `../../shared/rules.md` for the SE-specific rules: language conventions, the restricted-vocabulary table with alternatives, the "significant" statistical caveat, terminology consistency, voice and verb tense by section, punctuation (em-dash and colon limits), structure, tone, citation style, statistical reporting, figures and tables, threats to validity, BibTeX verification, and the 19-item self-check.

4. **Load the AI-trope catalog.** If step 2 recorded an override path (from `--tropes=<path>`, `--refresh-tropes`, or `--edit-tropes`), read that file and skip the rest of this step. Otherwise — the common case — try `https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/` first (the upstream Gist served as `text/plain`); if that fails, try `https://tropes.fyi/tropes-md` (HTML viewer; extract the markdown); if both fail, read `../../shared/tropes-snapshot.md` for the bundled fallback. Do not consult `./tropes-snapshot.cache.md` unless the user explicitly opted in.

5. **Per-section pass.** For each paper section, scan the prose against the rules and the trope catalog. For each violation, record:
   - The rule or trope name.
   - The location (`file:line` for LaTeX; `Section: <name>` for PDF).
   - A short verbatim quote of the offending text, with enough surrounding context to make the quote unique within the paper.
   - A concrete suggested replacement that follows the rules.

6. **Cross-cutting metrics.** Compute and record:
   - Em-dash density (target: ≤ 2 per page-equivalent of ~350 words).
   - Colon density in running prose (target: ≤ 2 per page-equivalent).
   - Restricted-word density per paragraph (flag paragraphs with more than 2 to 3 occurrences).
   - Sentence-length variance (flag stretches of three or more consecutive sentences within 5 words of each other in length).
   - Verb-tense compliance by section (compare against the table in `rules.md`).
   - American-vs-British spelling (flag British variants).
   - "Significant" audit (flag non-statistical uses).

7. **Citations and BibTeX (LaTeX only).** Scan for:
   - Citation clusters with three or more `\cite{}` entries that do not explain what each cited work contributes.
   - `\cite{}` calls without a nearby `% GROUNDING: "..."` comment.
   - Spelled-out author names that should use `\citeauthor{}`.
   - `.bib` entries referenced by the paper that have missing or unverifiable required fields.

8. **Write the report.** Save the assessment as `ai-slop-report.md` in the user's current working directory **and** print the same content to the console. Use the report template below.

9. **Stop after the report.** Do not modify the paper. If the user wants the findings applied, route them to `/ai-slop:revise`.

## Report template

The report's schema is stable so revise mode can parse it. Each finding has `Rule`, `Location`, `Quote`, and `Suggested revision`; revise mode locates the `Quote` in the paper and replaces it with `Suggested revision`.

````markdown
# AI Slop Review

**Paper:** <path>
**Skill version:** 2026-05-09
**Reviewed:** <ISO 8601 date>

> This report applies the writing rules at
> https://github.com/se-uhd/ai-slop-skill as a self-check.
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
- `../../shared/tropes-snapshot.md` for the AI-trope catalog. Together with the live Gist and the tropes.fyi viewer, this is the default catalog source — the common case for every review run.
- `./tropes-snapshot.cache.md` (working directory, optional) is written only when the user opts in via `--refresh-tropes` or `--edit-tropes`, and read only when an override flag points at it. It is not a default lookup location.

## Constraints

- **Quote verbatim.** The `Quote` field must match the paper text exactly, with enough surrounding context to be unique. Revise mode relies on exact-match lookup.
- **Suggest concrete revisions.** Avoid vague guidance ("rewrite to be clearer"). Where a rule has a specific replacement (a banned phrase, a restricted word, a tense correction), provide it. For judgment-call findings, put them in "Items requiring author judgment" rather than "Findings by section".
- **Do not editorialize.** Do not flag stylistic choices the rules do not address (e.g., theoretical contribution, novelty argument, narrative structure, general readability), even if you notice them.
- **Do not modify the paper.** Review mode writes only `ai-slop-report.md` in the working directory.
