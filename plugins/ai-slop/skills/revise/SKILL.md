---
name: revise
description: Apply the findings of an `/ai-slop:review` report to the source — replace each flagged quote with its suggested revision, and insert `% GROUNDING` TODO stubs for ungrounded citations. Use when the user has a generated `ai-slop-report.md` (or equivalent) and wants the suggestions applied to the paper.
license: CC-BY-4.0
metadata:
  version: "2026-06_rev16"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review — Revise Mode

This skill applies a previous `/ai-slop:review` report to the paper. For each finding, it locates the quoted text in the paper and replaces it with the suggested revision.

**Audience and tone.** The user has already reviewed the report and wants it applied. Trust the report's `Suggested revision` fields; do not second-guess them unless the surrounding context makes the suggestion unsafe (e.g., the suggestion would break LaTeX syntax or change the meaning of a result).

## When to use

Invoke this skill when the user:

1. Has a generated `ai-slop-report.md` (or similarly structured report) and wants the findings applied to the paper.
2. Asks to "apply the review", "revise according to the report", or "fix the slop".

Do **not** invoke when the user wants a fresh review (use `/ai-slop:review` instead), or when no report file exists.

## Inputs

Both inputs default to the current working directory. No arguments are required.

- **Report.** Defaults to `ai-slop-report.md` in the working directory. If that file does not exist, ask the user to point to the report (or to run `/ai-slop:review` first). The report must match the schema produced by `/ai-slop:review` (i.e., Findings by section, Cross-cutting metrics, Items requiring author judgment).
- **Paper.** Auto-detected by running `python3 ${CLAUDE_SKILL_DIR}/../../scripts/find_latex_root.py`. Exit 0 → use the printed path; exit 2 → multiple candidates printed, ask the user; exit 1 → no `.tex` root, stop. PDF input is not supported; revise mode edits LaTeX directly.

**Optional path overrides.** Paths can still be passed as arguments. The first argument is the report path; the second is the paper path.

## Workflow

1. **Read the report.** Parse the `Findings by section` blocks. Each block has `Rule`, `Location`, `Quote`, and `Suggested revision`. Skip blocks under "Items requiring author judgment"; those need human input.

2. **Read the paper.** Open the LaTeX source root and follow `\input{}` / `\include{}` to gather the full text. Note the file each section lives in if the paper is multi-file.

3. **Apply each finding.** For each finding, in document order:
   - Locate the `Quote` text in the paper. Use the `Location` hint (`file:line`) to disambiguate if the same text appears multiple times.
   - If the quote is found exactly: replace it with `Suggested revision` using the Edit tool. One Edit call per finding (do not bundle multiple findings into one edit; that makes diffs harder to review).
   - If the quote is not found (the paper may have been edited since review): log it as a skipped finding with the reason. Do not attempt fuzzy matching that could change the wrong text.
   - If the quote appears in multiple locations and the `Location` hint does not uniquely identify one: prefer the location closest to the hint and log the ambiguity in the summary.
   - If the suggestion would break LaTeX (e.g., mismatched braces, undefined macros, broken `\cite{}` keys): log as skipped with the reason rather than apply.

4. **Insert grounding stubs.** For every `\cite{}` listed in the report's **Grounding to-do** section, insert a `% GROUNDING: TODO verify <key>` comment immediately after that `\cite{}` call (one Edit per cite, matching the surrounding indentation and comment placement). These are TODO markers for a supporting quote — never invent the quote. The author can fill them by hand, or run `/ai-slop:ground`, which fetches each cited source and replaces the stub with a retrieved verbatim quote. Skip and log any cite whose location cannot be matched.

5. **Cross-cutting metrics.** These are aggregate counts, not individual edits. The specific instances behind them should already appear under "Findings by section". Do not invent new edits to balance a metric.

6. **Summarize.** Print a summary to the console with three lists:
   - **Applied:** findings whose `Quote` was located and replaced, plus grounding stubs inserted.
   - **Skipped:** findings whose `Quote` could not be uniquely located, or whose suggestion was unsafe to apply, with reasons.
   - **Author judgment required:** findings copied from the "Items requiring author judgment" section, so the user knows what still needs manual attention.

7. **Stop.** Do not regenerate the report. Do not commit the changes. The user runs `git diff` to inspect and `git commit` when satisfied.

## Bundled files

- `../../shared/rules-general.md`, `../../shared/rules-scientific.md`, `../../shared/rules-latex.md` — the rule layers, referenced only as a fallback when the user asks *why* a finding was flagged; revise mode trusts the report's suggested revisions and does not re-derive them from the rules.
- `../../scripts/find_latex_root.py` — used by the Inputs section to locate the LaTeX root.

Revise mode does not load the trope catalog at runtime: the report already contains every suggested revision, so no trope source is needed.

## Constraints

- **Trust the report's suggested revisions.** Do not re-derive them from the rule layers or tropes.fyi. If a suggestion looks wrong, flag it in the "Skipped" list with the reason rather than silently substituting your own.
- **Edit only what the report asks for.** Do not "improve" prose that was not flagged. Do not add or remove citations, change figures, or restructure sections.
- **Reformulate, do not delete.** Apply each suggested revision as written. If a finding's suggested revision would delete a substantive statement (a claim, example, or qualification, not mere filler) and nothing indicates the author asked for a cut, treat it as a suggestion that looks wrong: log it in the "Skipped" list with the reason rather than delete. Genuine filler flagged by the concision rules may be removed.
- **One Edit call per finding.** Bundling makes diffs harder to review.
- **Preserve formatting.** Match the surrounding LaTeX context (line breaks, indentation, comment placement) when replacing.
- **Do not commit.** Leave the changes in the working tree. The user owns the commit.
