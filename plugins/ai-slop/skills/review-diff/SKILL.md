---
name: review-diff
description: Review only the modified parts of a git-versioned paper for AI slop and violations of the SE writing rules. Use when the user has uncommitted edits or a feature branch in a LaTeX paper repo and wants to audit only what they changed, not the whole draft. Triggers on prompts such as "check my edits", "review what I just changed", "audit this branch's prose", or `/ai-slop:review-diff`. Writes a structured Markdown report with concrete suggested revisions that revise mode can apply.
license: CC-BY-4.0
metadata:
  version: "2026-05_rev11"
  homepage: https://github.com/se-uhd/ai-slop-skill
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

**Paper detection.** Same as `/ai-slop:review`: run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_latex_root.py`. Exit 0 → use the printed path; exit 2 → multiple candidates printed, ask the user; exit 1 → no `.tex` root, stop and tell the user (PDF input is not supported in diff mode because no diff is available).

**Trope catalog override.** `--tropes=<path>` (repeatable) replaces the default fetch with one or more user-supplied files; contents are concatenated in the order given. When `--tropes` is not passed (the common case), the catalog is fetched live — see step 7.

## Workflow

1. **Verify git context.** Run `git rev-parse --is-inside-work-tree`. If not in a git repo, stop with the message above. Otherwise capture the repo root for later path resolution.

2. **Resolve inputs.** Auto-detect the LaTeX root. Parse the base ref (default `HEAD`) and any `--tropes=<path>` arguments (repeatable) from the user's message.

3. **Compute the diff.** Run `git diff --unified=0 <base> -- '*.tex'` to list changed lines in `.tex` files only. Parse the unified-diff hunk headers (`@@ -<old_start>,<old_count> +<new_start>,<new_count> @@`) to extract per-file line ranges of added or modified lines in the new tree (the working-tree side). Track these as the **changed-line set** per file. If no `.tex` files changed, write an empty report (Summary: "No `.tex` changes since `<base>`."), print it, and stop.

4. **Expand to paragraph context.** For each changed-line range, expand outward in the new file to the nearest preceding and following blank line so the changed prose is reviewed in its full paragraph. Record both:
   - the **changed lines** (used to scope what counts as a finding), and
   - the **surrounding paragraph** (used as context so multi-line tropes or sentence-length checks have enough text to operate on).

5. **Identify sections.** For each changed paragraph, walk backward in the new file to the nearest preceding `\section{}` or `\subsection{}` to map the paragraph to its section. This drives section-aware rules (e.g., verb tense, threats-to-validity specificity).

6. **Load the rule set.** Read `../../shared/rules.md` for the SE-specific rules: language conventions, restricted vocabulary with alternatives, the "significant" caveat, terminology consistency, voice and tense by section, punctuation (em-dash, colon, and semicolon caps; capitalization after a colon; the combined pause-punctuation budget), citation style, statistical reporting, BibTeX verification, and the 25-item self-check.

7. **Load the AI-trope catalog.** If `--tropes=<path>` was passed (one or more times), read each named file and concatenate them in the order given. Otherwise run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py ${CLAUDE_SKILL_DIR}/../../shared/tropes-snapshot.md` and read its stdout. The script tries the upstream Gist, then the tropes.fyi viewer, then the bundled fallback, and always emits a non-empty body.

8. **Per-paragraph pass.** For each changed paragraph, scan the prose against the rules and the trope catalog. **A finding is in scope only if at least one line of the offending quote falls inside the changed-line set.** A pre-existing violation on an unchanged line is out of scope, even when adjacent to a change. For each in-scope violation, record:
   - The rule or trope name.
   - The location (`file:line` in the new file).
   - A short verbatim quote of the offending text, with enough surrounding context to be unique within the paper.
   - A concrete suggested replacement.

9. **Cross-cutting metrics, scoped to the diff.** Compute on changed lines only:
   - Em-dash count and locations in changed lines.
   - Restricted-word occurrences in changed lines.
   - Verb-tense compliance for changed paragraphs (against the section table in `rules.md`).
   - American-vs-British spelling in changed lines.
   - "Significant" audit on changed lines.

   Skip metrics that need full-paper context (e.g., em-dash *density* per page, sentence-length variance over runs of three sentences spanning untouched prose, paragraph-restricted-word density when the diff touched only a fraction of the paragraph). Note the scoping in the report's Summary.

10. **Citations and BibTeX, scoped to the diff.** On changed lines, scan for newly added or modified `\cite{}` calls. Apply the same checks as `/ai-slop:review` step 6 (citation clusters with three or more entries lacking per-work explanation, missing `% GROUNDING:` comments, spelled-out author names that should use `\citeauthor{}`). For BibTeX field checks scoped to newly cited keys: identify the `.bib` files via `\bibliography{...}` / `\addbibresource{...}` directives, run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/check_bib_fields.py <bibfiles>`, and report only entries whose keys appear in newly added `\cite{}` calls. Do not flag pre-existing citations the diff did not touch. Standard BibTeX semantics apply (no `crossref` inheritance) — sanity-check flagged entries.

11. **Write the report.** Save `ai-slop-report.md` in the working directory.

    Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-report.md`. If the linter exits non-zero, read its stdout findings (one per line, tab-separated `<file>:<line>\t<rule>\t<message>`), revise the report in place to address each, and re-run the linter. Repeat at most three iterations; after the third pass proceed regardless of the linter's state. The lint loop is internal quality control — do not mention lint output, rule names, exit codes, or iteration counts in the user-facing summary.

    Then Read the file back and quote its contents verbatim in your reply — do **not** regenerate the report text from memory for the inline echo, which has triggered repetition glitches (duplicate disclaimer blockquotes and `## Summary` headings). Echoing the Read result keeps the printed version identical to the file. Use the report template from `../review/SKILL.md` "Report template" with one extra header line:

    ```text
    **Diff scope:** base=<base ref>, files=<list of changed .tex files>
    ```

    Place this line under `**Reviewed:**`. The Summary should explicitly note that the review only covered changed lines, so a reader of the report does not assume the rest of the paper was checked.

12. **Stop after the report.** Do not modify the paper. If the user wants the findings applied, route them to `/ai-slop:revise` — the schema is identical, so revise mode works without changes.

## Report template

Identical to `/ai-slop:review` (same `Rule` / `Location` / `Quote` / `Suggested revision` schema so `/ai-slop:revise` can act on it), with the extra `**Diff scope:**` header line described in step 11. See `../review/SKILL.md` "Report template" for the full template.

## Bundled files

- `../../shared/rules.md` for the SE-specific rule set.
- `../../shared/tropes-snapshot.md` is the offline fallback the trope-fetch script falls through to when the upstream Gist and tropes.fyi viewer are both unreachable.
- `../../scripts/find_latex_root.py`, `../../scripts/fetch_tropes.py`, `../../scripts/check_bib_fields.py` implement the deterministic checks above; their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Diff scope is strict.** Only flag a finding when at least one line of its quote lies in the changed-line set. Do not surface pre-existing issues on untouched lines, even when they sit inside a changed paragraph.
- **Same report schema.** The report must match the schema produced by `/ai-slop:review` so `/ai-slop:revise` works without changes. The only difference is the extra "Diff scope" header line and the scoping note in the Summary.
- **Do not modify the paper.** Diff mode writes only `ai-slop-report.md` in the working directory.
- **Do not stash, commit, or alter the working tree.** The skill reads the diff and the working-tree files; it never runs `git add`, `git stash`, `git commit`, or any other state-changing git command.
