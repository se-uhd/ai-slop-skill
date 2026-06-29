---
name: review-repo
description: Review a whole code repository's natural-language text for AI slop and rule violations — every Markdown and plain-text file plus the comments and doc-comments of its source and config files, not just one document or a diff. Use when the user wants to audit the prose spread across a codebase (READMEs, changelogs, design docs, and the comments in code and config). Triggers on prompts such as "scan this repo for slop", "check the prose across the codebase", "audit the comments and docs", or `/ai-slop:review-repo`. Loads the general rules by default; `--scientific` adds the research-article layer. Writes a structured Markdown report grouped by file.
license: CC-BY-4.0
metadata:
  version: "2026-06_rev15"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review — Repo Mode

This skill reviews the natural-language text spread across a whole repository, rather than a single document (`/ai-slop:review`) or the changed lines of one (`/ai-slop:review-diff`). It extracts every Markdown and plain-text file in full, the comments and doc-comments of the source and config files, and the repository's commit messages, then scans that prose against the general rules and the AI-trope catalog and writes an `ai-slop-report.md` grouped by file (and by commit). It is the right mode for a codebase whose prose has drifted over many commits: a British spelling, an em-dash, or a trope sitting in a committed comment or a commit message that a diff review never revisits.

**Audience and tone.** The default user maintains a codebase and wants a sweep of its prose: READMEs, changelogs, design notes, and the comments in code and config. Frame findings as suggestions, not violations.

## When to use

Invoke this skill when the user:

1. Asks to scan or audit the prose across a whole repository — for example, "check the repo for slop", "audit the comments and docs", or "find British spellings and tropes across the codebase".
2. Runs `/ai-slop:review-repo`, optionally with a path to the repo root, `--scientific`, and/or a commit-scanning flag (`--commits=<spec>` or `--no-commits`).

Do **not** invoke for a single document (use `/ai-slop:review`) or for only the changed lines (use `/ai-slop:review-diff`). Repo mode does scan a repository's `.tex` files (as prose, against the general rules), but for the LaTeX-specific checks (citations, BibTeX, section-aware rules) a single paper is still better served by `/ai-slop:review` with the dedicated LaTeX layer.

## Inputs

The skill scans the repository rooted at the current working directory by default.

**Repo root.** A positional path argument overrides the default (`/ai-slop:review-repo path/to/repo`). The path must be a directory.

**Scope of the text scanned** is decided by `scripts/scan_repo.py` (see Workflow). In a git repository it scans the tracked files, so `.gitignore`d build output and dependencies are excluded automatically; outside one it walks the tree minus a denylist of build and dependency directories. Markdown, plain-text, and LaTeX files are read in full (a `.tex` file's `%` comments are reviewed alongside its body); source and config files contribute only their comments and doc-comments. The repository's commit messages are scanned too (their subject and body, with merge commits and the standard trailer lines such as `Co-authored-by` and `Signed-off-by` dropped). Generated files, lockfiles, and binaries are skipped.

**Commit-message scope.** By default the scan covers the most recent 200 commits. Pass `--commits=<N>` for a different count, `--commits=all` for the full history, `--commits=<range>` for a git revision range (for example `--commits=main..HEAD` to review just a branch's commits before they are pushed), or `--no-commits` to skip commit messages entirely. Note that published commit history is immutable, so commit-message findings are mostly advisory: a guide for future messages, or for rewording a branch's not-yet-pushed commits with an interactive rebase. `/ai-slop:revise` does not touch commit messages.

**Rule layers.** The general layer always loads. Pass `--scientific` to also load the research-article layer when the repository's prose is research writing (a thesis, or a paper repo's Markdown or LaTeX). `.tex` files are scanned as prose (their body and `%` comments) against the general (and, with `--scientific`, the research-article) layer; repo mode does not load the dedicated LaTeX layer.

**Trope catalog override.** `--tropes=<path>` (repeatable) replaces the live fetch with one or more user-supplied files, concatenated in the order given, exactly as in `/ai-slop:review`.

## Workflow

1. **Resolve the repo root.** Use the path argument if given, otherwise the current working directory. Confirm it is a directory; if not, stop and tell the user.

2. **Extract the repository's prose.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/scan_repo.py <repo-root>`, appending the user's commit-scanning flag (`--commits=<spec>` or `--no-commits`) when one was given. Each stdout line is `<relpath>:<line>:<text>`: a Markdown or plain-text line, an extracted comment, or a commit-message line. File lines come first, grouped by file and sorted; commit messages follow under a `commit <short-sha>` pseudo-path, newest first. The script prints a one-line summary to stderr (files scanned, prose vs comment-bearing, commit messages, total lines). If stdout is empty, write an empty report (Summary: "No natural-language text found to review.") and stop. The script's module docstring documents what is scanned and its heuristic limits (string-aware comment detection, first-comment-per-line, the generated-file skip, the commit-message selection and trailer drop).

3. **Determine which rule layers to load.** Read `../../shared/rules-general.md` always. Read `../../shared/rules-scientific.md` too when the user passed `--scientific`. Repo mode never loads the dedicated LaTeX layer; it reviews any `.tex` files as prose against the general layer. Each layer contributes its own rules and self-check; a finding's `Rule` name comes from whichever layer defines it.

4. **Load the AI-trope catalog.** Same as `/ai-slop:review` step 3: if `--tropes=<path>` was passed, read each named file and concatenate them in order; otherwise run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/fetch_tropes.py ${CLAUDE_SKILL_DIR}/../../shared/tropes-snapshot.md` and read its stdout.

5. **Review file by file.** Group the scan output by `<relpath>` and review each group's extracted text against the rules and the trope catalog. The `commit <short-sha>` groups are reviewed the same way as files. A repository can be large, so be systematic: take one group's lines at a time and record only real findings. For each violation record:
   - The rule or trope name.
   - The location (`<relpath>:<line>`, or `commit <short-sha>:<line>` for a commit message).
   - A short verbatim quote of the offending text. The scan strips comment markers, so read the file at that line when an exact quote matters; for a commit message use `git show <short-sha>`.
   - A concrete suggested replacement.

   When unsure whether a flagged line is prose or code the extractor surfaced by accident, open the file for context and drop the finding if it is not natural language.

6. **Cross-cutting metrics, repo-wide.** Compute over the extracted text and report raw counts with locations (per-page densities do not apply to a repository): em-dashes; American-vs-British spelling (a frequent source of drift in code comments); restricted-word occurrences; and, when the scientific layer is in scope, the "significant" audit and verb tense. A single punctuation mark that is the wrong choice (a semicolon joining two independent clauses, an em-dash standing in for a period, a colon used as a generic mid-sentence pause) is a per-file finding under step 5.

7. **Write the report.** Save `ai-slop-report.md` in the working directory; it is a generated artifact and must never be committed, so add it to `.gitignore` if the repository does not already list it. Then run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/lint_markdown.py --fix ai-slop-report.md` and iterate up to three times exactly as in `/ai-slop:review` step 7, then read the file back and echo it verbatim. Use the report template from `../review/SKILL.md` "Report template" with `### <relpath>` headings under "Findings by file" in place of section names, and one extra header line under `**Reviewed:**`:

   ```text
   **Repo scope:** root=<repo root>, files=<N scanned>, commits=<N scanned>, prose lines=<N>
   ```

   The Summary should state that the review covered the repository's Markdown, plain-text, LaTeX, code/config comments, and commit messages, and name what the scan skipped (generated files, binaries, vendored directories, merge commits, and trailer lines). When commit-message findings exist, note that they are advisory, since published commit history is immutable.

8. **Stop after the report.** Do not modify the repository. `/ai-slop:revise` operates on a single document, so a repo-wide report is not auto-applied; the user fixes each file directly, or runs `/ai-slop:revise` against one file at a time.

## Report template

Identical to `/ai-slop:review` (same `Rule` / `Location` / `Quote` / `Suggested revision` schema), with `### <relpath>` headings under "Findings by file" instead of section names, and the extra `**Repo scope:**` header line from step 7. See `../review/SKILL.md` "Report template" for the full template.

## Bundled files

- `../../shared/rules-general.md` and `../../shared/rules-scientific.md` are the rule layers repo mode can load (the LaTeX layer never applies here).
- `../../shared/tropes-snapshot.md` is the offline fallback the trope-fetch script falls through to when the upstream Gist and tropes.fyi viewer are both unreachable.
- `../../scripts/scan_repo.py` extracts the repository's natural-language text; `../../scripts/fetch_tropes.py` and `../../scripts/lint_markdown.py` implement the catalog fetch and report linting. Their module docstrings document inputs, outputs, exit codes, and known limitations.

## Constraints

- **Do not modify the repository.** Repo mode writes only `ai-slop-report.md` in the working directory.
- **Quote verbatim.** Quote the file's actual text, not the marker-stripped scan line, so a reader can find it.
- **Code is not prose.** The extractor is heuristic; if a flagged line is code it surfaced by accident, drop the finding rather than rewriting code.
- **Do not stash, commit, or alter the working tree.** The skill reads files and writes the report; it never runs `git add`, `git stash`, `git commit`, or any other state-changing git command.
