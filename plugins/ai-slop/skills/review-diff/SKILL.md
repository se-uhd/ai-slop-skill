---
name: review-diff
description: Review only the modified parts of a git-versioned paper for AI slop and violations of the SE writing rules. Use when the user has uncommitted edits or a feature branch in a LaTeX paper repo and wants to audit only what they changed, not the whole draft. Triggers on prompts such as "check my edits", "review what I just changed", "audit this branch's prose", or `/ai-slop:review-diff`. Writes a structured Markdown report with concrete suggested revisions that revise mode can apply.
version: 2026-05_rev2
homepage: https://github.com/se-uhd/ai-slop-skill
license: CC-BY-4.0
---

# AI Slop Review — Diff Mode

This skill reviews only the lines that changed in a git-versioned paper. It runs `git diff <base>` (default base: `HEAD`), restricts rule and trope checks to lines added or modified in `.tex` files, and writes the same `ai-slop-report.md` schema as `/ai-slop:review` so `/ai-slop:revise` can apply the suggestions unchanged.

**Audience and tone.** The default user is an author iterating on a draft and wants a quick pass over their latest edits before committing or sharing. Frame findings as suggestions, not violations.

## When to use

Invoke this skill when the user:

1. Has a paper repo with uncommitted edits (or a feature branch) and asks to check just the changes — for example, "review my edits before I commit", "audit what I just changed", "check this branch's prose".
2. Runs `/ai-slop:review-diff` with or without a base ref.

Do **not** invoke for a full-paper pass (use `/ai-slop:review`) or when the working directory is not a git repository (tell the user and suggest `/ai-slop:review` instead).

## Inputs

The skill auto-detects the paper and the diff in the current working directory.

**Base ref.** Defaults to `HEAD` (so the review covers staged + unstaged changes in the working tree). The user may pass any git ref as a positional argument:

- No argument -> `git diff HEAD` (uncommitted changes vs the last commit).
- A branch or commit-ish (e.g., `main`, `abc1234`) -> `git diff <ref>` (working tree vs that ref).

If the working directory is not inside a git repository (`git rev-parse --is-inside-work-tree` returns non-zero), stop and tell the user, e.g., "Not a git repository; use `/ai-slop:review` for a full-paper review."

**Paper detection.** Same as `/ai-slop:review`: list the `.tex` files in the working directory (non-recursive) and identify the LaTeX root — the file containing `\documentclass{}` and `\begin{document}`. If multiple roots are found, prefer `main.tex` or `paper.tex`; otherwise list them and ask the user. PDF input is not supported in diff mode (no diff available).

**Trope catalog overrides (rare corner case).** Same flags as `/ai-slop:review` (`--tropes=<path>`, `--refresh-tropes`, `--edit-tropes`); the default flow uses the live-fetch chain (upstream Gist -> tropes.fyi viewer -> bundled `../../shared/tropes-snapshot.md`). See `../review/SKILL.md` "Trope catalog overrides (corner case)" for the full semantics; the same precedence rules apply here.

## Workflow

1. **Verify git context.** Run `git rev-parse --is-inside-work-tree`. If not in a git repo, stop with the message above. Otherwise capture the repo root for later path resolution.

2. **Resolve inputs.** Auto-detect the LaTeX root. Parse the base ref (default `HEAD`) and any trope catalog override flags from the user's arguments.

3. **Apply trope catalog overrides (rare).** Same as `/ai-slop:review` step 2; skip entirely unless the user opted in.

4. **Compute the diff.** Run `git diff --unified=0 <base> -- '*.tex'` to list changed lines in `.tex` files only. Parse the unified-diff hunk headers (`@@ -<old_start>,<old_count> +<new_start>,<new_count> @@`) to extract per-file line ranges of added or modified lines in the new tree (the working-tree side). Track these as the **changed-line set** per file. If no `.tex` files changed, write an empty report (Summary: "No `.tex` changes since `<base>`."), print it, and stop.

5. **Expand to paragraph context.** For each changed-line range, expand outward in the new file to the nearest preceding and following blank line so the changed prose is reviewed in its full paragraph. Record both:
   - the **changed lines** (used to scope what counts as a finding), and
   - the **surrounding paragraph** (used as context so multi-line tropes or sentence-length checks have enough text to operate on).

6. **Identify sections.** For each changed paragraph, walk backward in the new file to the nearest preceding `\section{}` or `\subsection{}` to map the paragraph to its section. This drives section-aware rules (e.g., verb tense, threats-to-validity specificity).

7. **Load the rule set.** Read `../../shared/rules.md` for the SE-specific rules: language conventions, restricted vocabulary with alternatives, the "significant" caveat, terminology consistency, voice and tense by section, punctuation limits, citation style, statistical reporting, BibTeX verification, and the 19-item self-check.

8. **Load the AI-trope catalog.** Same live-fetch chain and override semantics as `/ai-slop:review` step 4: upstream Gist -> tropes.fyi viewer -> bundled `../../shared/tropes-snapshot.md`, unless an override flag pointed elsewhere.

9. **Per-paragraph pass.** For each changed paragraph, scan the prose against the rules and the trope catalog. **A finding is in scope only if at least one line of the offending quote falls inside the changed-line set.** A pre-existing violation on an unchanged line is out of scope, even when adjacent to a change. For each in-scope violation, record:
   - The rule or trope name.
   - The location (`file:line` in the new file).
   - A short verbatim quote of the offending text, with enough surrounding context to be unique within the paper.
   - A concrete suggested replacement.

10. **Cross-cutting metrics, scoped to the diff.** Compute on changed lines only:
    - Em-dash count and locations in changed lines.
    - Restricted-word occurrences in changed lines.
    - Verb-tense compliance for changed paragraphs (against the section table in `rules.md`).
    - American-vs-British spelling in changed lines.
    - "Significant" audit on changed lines.

    Skip metrics that need full-paper context (e.g., em-dash *density* per page, sentence-length variance over runs of three sentences spanning untouched prose, paragraph-restricted-word density when the diff touched only a fraction of the paragraph). Note the scoping in the report's Summary.

11. **Citations and BibTeX, scoped to the diff.** On changed lines, scan for newly added or modified `\cite{}` calls. Apply the same checks as `/ai-slop:review` step 7 (e.g., citation clusters with three or more entries lacking per-work explanation, missing `% GROUNDING:` comments, spelled-out author names that should use `\citeauthor{}`, missing required `.bib` fields for newly cited keys). Do not flag pre-existing citations the diff did not touch.

12. **Write the report.** Save `ai-slop-report.md` in the working directory and print the same content to the console. Use the report template from `../review/SKILL.md` "Report template" with one extra header line:

    ```
    **Diff scope:** base=<base ref>, files=<list of changed .tex files>
    ```

    Place this line under `**Reviewed:**`. The Summary should explicitly note that the review only covered changed lines, so a reader of the report does not assume the rest of the paper was checked.

13. **Stop after the report.** Do not modify the paper. If the user wants the findings applied, route them to `/ai-slop:revise` — the schema is identical, so revise mode works without changes.

## Report template

Identical to `/ai-slop:review` (same `Rule` / `Location` / `Quote` / `Suggested revision` schema so `/ai-slop:revise` can act on it), with the extra `**Diff scope:**` header line described in step 12. See `../review/SKILL.md` "Report template" for the full template.

## Bundled files

- `../../shared/rules.md` for the SE-specific rule set.
- `../../shared/tropes-snapshot.md` for the bundled trope catalog fallback.
- `./tropes-snapshot.cache.md` (working directory, optional) is read only when an override flag points at it; same semantics as in `/ai-slop:review`.

## Constraints

- **Diff scope is strict.** Only flag a finding when at least one line of its quote lies in the changed-line set. Do not surface pre-existing issues on untouched lines, even when they sit inside a changed paragraph.
- **Same report schema.** The report must match the schema produced by `/ai-slop:review` so `/ai-slop:revise` works without changes. The only difference is the extra "Diff scope" header line and the scoping note in the Summary.
- **Do not modify the paper.** Diff mode writes only `ai-slop-report.md` in the working directory.
- **Do not stash, commit, or alter the working tree.** The skill reads the diff and the working-tree files; it never runs `git add`, `git stash`, `git commit`, or any other state-changing git command.
