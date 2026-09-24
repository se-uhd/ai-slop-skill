---
name: review-repo
description: Review a whole code repository's natural-language text for AI slop and rule violations, covering every Markdown and plain-text file plus the comments and doc-comments of its source and config files, not just one document or a diff. Use when the user wants to audit the prose spread across a codebase (READMEs, changelogs, design docs, and the comments in code and config). Triggers on prompts such as "scan this repo for slop", "check the prose across the codebase", "audit the comments and docs", or `/ai-slop:review-repo`. Loads the general rules by default. `--scientific` adds the research article layer, and `--ste` adds the Simplified Technical English layer. Writes a structured Markdown report grouped by file.
license: CC-BY-4.0
metadata:
  version: "2026-09_rev29"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Repo Mode

This skill reviews the natural-language text spread across a whole repository, rather than a single document (`/ai-slop:review`) or the changed lines of one (`/ai-slop:review-diff`). It extracts every Markdown and plain-text file in full, the comments and doc-comments of the source and config files, and the repository's commit messages, then scans that prose against the general rules and the AI trope catalog and writes an `ai-slop-report.md` grouped by file (and by commit). It is the right mode for problems that build up over many commits and that a diff review never revisits, such as a British spelling, an em-dash, or a trope in a committed comment or a commit message.

**Audience and tone.** The default user maintains a codebase and wants a sweep of its prose: READMEs, changelogs, design notes, and the comments in code and config. Frame findings as suggestions, not violations.

## When to use

Invoke this skill when the user:

1. Asks to scan or audit the prose across a whole repository, for example, "check the repo for slop", "audit the comments and docs", or "find British spellings and tropes across the codebase".
2. Runs `/ai-slop:review-repo`, optionally with a path to the repo root, `--scientific`, `--ste`, and/or a commit-scanning flag (`--commits=<spec>` or `--no-commits`).

Do not invoke for a single document (use `/ai-slop:review`) or for only the changed lines (use `/ai-slop:review-diff`). Repo mode does scan a repository's `.tex` files (as prose, against the general rules), but for the LaTeX-specific checks (e.g., citations, BibTeX, and section-aware rules) a single paper is still better served by `/ai-slop:review` with the dedicated LaTeX layer.

## Inputs

The skill scans the repository rooted at the current working directory by default.

**Repo root.** A positional path argument overrides the default (`/ai-slop:review-repo path/to/repo`). The path must be a directory.

**Scope of the text scanned.** `scripts/scan_repo.py` decides which text to scan (see Workflow). In a git repository it scans the tracked files and so excludes `.gitignore`d build output and dependencies automatically. Outside a git repository it walks the whole tree, and in both cases it skips a denylist of vendored, build, dependency, and test-fixture directories. The script reads Markdown, plain-text, and LaTeX files in full, including a `.tex` file's `%` comments, and extracts only the comments and doc-comments from source and config files. It also scans the repository's commit messages (their subject and body), dropping merge commits and the standard trailer lines such as `Co-authored-by` and `Signed-off-by`. It skips generated files (a `DO NOT EDIT` or `@generated` marker on a comment line in the first ten lines, each named on stderr), lockfiles, dependency pins, and binaries. In Markdown, the script treats a fenced block as prose when its info string names a prose format (`markdown`, `text`), so a quoted template counts as content. It skips other fenced code, YAML front matter, and indented code blocks.

**Commit message scope.** By default the scan covers the most recent 200 commits. Pass `--commits=<N>` for a different count, `--commits=all` for the full history, `--commits=<range>` for a git revision range (for example `--commits=main..HEAD` to review just a branch's commits before they are pushed), or `--no-commits` to skip commit messages entirely. Pushed commit history is rewritten only by a deliberate repair, so commit message findings are mostly advisory: a guide for future messages, or for rewording a branch's not-yet-pushed commits with an interactive rebase. `/ai-slop:revise` does not touch commit messages.

**Rule layers.** The general layer always loads. Pass `--scientific` to also load the research article layer when the repository's prose is research writing (e.g., a thesis or a paper repo's Markdown or LaTeX). `.tex` files are scanned as prose (their body and `%` comments) against the general (and, with `--scientific`, the research article) layer. Repo mode does not load the dedicated LaTeX layer. Pass `--ste` to also load the Simplified Technical English layer (`rules-ste.md`) for a repository that writes its prose in STE.

**Trope catalog override.** `--tropes=<path>` (repeatable) replaces the live catalog with one or more user-supplied files, concatenated in the order given, exactly as in `/ai-slop:review`.

## Workflow

1. **Resolve the repo root.** Use the path argument if given, otherwise the current working directory. Confirm that it is a directory. If not, stop and tell the user.

2. **Extract the repository's prose.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/scan_repo.py <repo-root>`, appending the user's commit-scanning flag (`--commits=<spec>` or `--no-commits`) when one was given. Each stdout line is `<relpath>:<line>:<text>`: a Markdown or plain-text line, an extracted comment, or a commit message line. File lines come first, grouped by file and sorted. Commit messages follow under a `commit <short-sha>` pseudo-path, newest first. The script prints a one-line summary to stderr (files scanned, prose vs comment-bearing, commit messages, total lines). If stdout is empty, write an empty report (Summary: "No natural-language text found to review.") and stop. A `--commits` range that git cannot resolve stops the script with exit 2 and git's message, so report that to the user instead of writing a report with an empty commit section. The stderr summary also names each file skipped as generated. The script's module docstring documents what is scanned and its heuristic limits (how comment detection handles strings, which files count as generated, and how commit messages are selected and their trailer lines dropped).

3. **Determine which rule layers to load.** Read `../../shared/rules-general.md` always. Read `../../shared/rules-scientific.md` too when the user passed `--scientific`, and `../../shared/rules-ste.md` when the user passed `--ste`. Repo mode never loads the dedicated LaTeX layer (see Rule layers). Each layer contributes its own rules and self-check. A finding's `Rule` field carries the rule's name as written in the layer, followed by its key in parentheses, as in `Semicolons (G.semicolons)`. A catalog trope carries its name and its catalog status, as in `Negative parallelism (tropes.fyi, consistent)`.

4. **Load the AI trope catalog.** Same as `/ai-slop:review` step 3. If `--tropes=<path>` was passed, read each named file and concatenate them in order. Otherwise run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py` and read its stdout, stopping as review does when fetching the catalog fails.

5. **Review file by file.** Group the scan output by `<relpath>` and review each group's extracted text against the rules and the trope catalog. The `commit <short-sha>` groups are reviewed the same way as files. A repository can be large, so be systematic. Take one group's lines at a time and record only real findings. For each violation record:
   - The rule name with its key, as in `Semicolons (G.semicolons)`, or the trope name with its catalog status, as in `Negative parallelism (tropes.fyi, consistent)`.
   - The location (`<relpath>:<line>`, or `commit <short-sha>:<line>` for a commit message).
   - A short verbatim quote of the offending text. The scan strips comment markers, so read the file at that line when an exact quote matters. For a commit message use `git show <short-sha>`.
   - A concrete suggested replacement.

   When unsure whether a flagged line is prose or code that the extractor emitted by accident, open the file for context and drop the finding if it is not natural language.

   In STE mode, list a sentence that an STE rewrite would weaken under **Items requiring author judgment** instead of reporting it, as `/ai-slop:review` step 4 does.

6. **Cross-cutting metrics, repo-wide.** Compute the following metrics over the extracted text and report raw counts with locations, since per-page densities do not apply to a repository:
   - Dashes, from `python3 ${CLAUDE_SKILL_DIR}/../../scripts/scan_glyphs.py` run over the Markdown, plain-text, and LaTeX files that the scan listed. Take the counts from the scan, and treat the rows as `/ai-slop:review` step 5 does.
   - American-vs-British spelling, a frequent source of drift in code comments.
   - Restricted-word occurrences.
   - The "significant" audit and verb tense, when the scientific layer is in scope.
   - Repeated sentences, from `python3 ${CLAUDE_SKILL_DIR}/../../scripts/scan_repeats.py` run over the same Markdown, plain-text, and LaTeX files, with the rows tested per **Refer back instead of repeating** (`G.refer-back`) as `/ai-slop:review` step 5 does. The scan compares sentences within one file, not across files.
   - STE sentence candidates (STE mode only), from `python3 ${CLAUDE_SKILL_DIR}/../../scripts/scan_sentences.py` run over the same Markdown, plain-text, and LaTeX files, with the rows tested as `/ai-slop:review` step 5 does.

   A single punctuation mark that is the wrong choice (a semicolon joining two independent clauses, an em-dash standing in for a period, a colon used as a generic mid-sentence pause) is a per-file finding under step 5. Read comments and commit messages for the same rules without the scan.

7. **Write the report.** Save `ai-slop-report.md` in the working directory. It is a generated artifact and must never be committed, so resolve the repository root with `git rev-parse --show-toplevel` and add the report's name to the root's `.gitignore` if that file does not already list it. Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-report.md` and iterate up to three times exactly as in `/ai-slop:review` step 7, then read the file back and echo it verbatim. Use the report template from `../review/SKILL.md` "Report template" with `### <relpath>` headings under "Findings by file" in place of section names, and one extra header line under `**Reviewed:**`:

   ```text
   **Repo scope:** root=<repo root>, files=<N scanned>, commits=<N scanned>, prose lines=<N>
   ```

   The Summary should state that the review covered the repository's Markdown, plain-text, LaTeX, code/config comments, and commit messages, and name what the scan skipped (generated files, binaries, vendored directories, merge commits, and trailer lines). When commit message findings exist, note that they are advisory, since pushed history is rewritten only by a deliberate repair.

8. **Stop after the report.** Do not modify the repository. `/ai-slop:revise` operates on one document at a time, so a repo-wide report is not auto-applied. The user fixes each file directly, or runs `/ai-slop:revise ai-slop-report.md <file>` for one file, which applies the findings under that file's `### <relpath>` heading. Findings under a `### commit <sha>` heading name no file and are never applied.

## Report template

Identical to `/ai-slop:review` (same `Rule` / `Location` / `Quote` / `Suggested revision` schema), with `### <relpath>` headings under "Findings by file" instead of section names, and the extra `**Repo scope:**` header line from step 7. See `../review/SKILL.md` "Report template" for the full template.

## Bundled files

- `../../shared/rules-general.md`, `../../shared/rules-scientific.md`, and `../../shared/rules-ste.md` are the rule layers that repo mode can load (the LaTeX layer never applies here).
- `../../scripts/scan_repo.py` extracts the repository's natural-language text. `../../scripts/fetch_tropes.py`, `../../scripts/scan_glyphs.py`, `../../scripts/scan_repeats.py`, `../../scripts/scan_sentences.py`, and `../../scripts/lint_markdown.py` implement the catalog download, the glyph scan, the repeat scan, the sentence scan for STE mode, and report linting. Their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Do not modify the repository.** Repo mode writes only `ai-slop-report.md` in the working directory, plus the report's name in the repository's `.gitignore` when that line is missing (step 7).
- **Quote verbatim.** Quote the file's actual text, not the marker-stripped scan line, so a reader can find it.
- **Code is not prose.** The extractor is heuristic. If a flagged line is code that the extractor emitted by accident, drop the finding rather than rewriting code.
- **Do not stash, commit, or alter the working tree.** The skill reads files and writes the report. It never runs `git add`, `git stash`, `git commit`, or any other state-changing git command.
