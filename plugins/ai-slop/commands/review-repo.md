---
description: Review a whole repository's natural-language text for AI slop and rule violations — every Markdown and plain-text file plus the comments in source and config — using the general rules and the same report schema as `/ai-slop:review`. Generates a structured Markdown report grouped by file.
---

Use the `ai-slop:review-repo` skill.

The skill's workflow lives in `skills/review-repo/SKILL.md`. It runs `scripts/scan_repo.py` to extract the repository's natural-language text (Markdown and plain-text files in full, plus the comments and doc-comments of source and config files), scans that prose against the general rules and the AI-trope catalog, and writes `ai-slop-report.md` in the working directory using the same `Rule` / `Location` / `Quote` / `Suggested revision` schema as `/ai-slop:review`, with findings grouped by file. In a git repository the scan covers the tracked files (so `.gitignore`d build output and dependencies are excluded); generated files, lockfiles, and binaries are skipped, and `.tex` is left to `/ai-slop:review`.

The repo root is positional and defaults to the current working directory. Examples:

- `/ai-slop:review-repo` — scan the repository in the current directory.
- `/ai-slop:review-repo path/to/repo` — scan another repository.
- `/ai-slop:review-repo --scientific` — also apply the research-article rules (for a thesis or paper repo's prose).

The `--tropes=<path>` override flag (repeatable) from `/ai-slop:review` works the same way here.

Use `/ai-slop:review` for a single document and `/ai-slop:review-diff` for only the lines a branch changed. Repo mode is for prose that has accumulated across a codebase, the kind a diff review never revisits.

Do not modify the repository; the only output is `ai-slop-report.md` in the working directory. `/ai-slop:revise` applies a single-document report, so fix a repo-wide report's files directly (or run revise against one file at a time).
