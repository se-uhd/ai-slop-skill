---
description: Review only the modified parts of a git-versioned paper for AI slop and violations of the SE writing rules. Generates a structured Markdown report scoped to the diff.
---

Use the `ai-slop:review-diff` skill.

The skill's workflow lives in `skills/review-diff/SKILL.md`. It runs `git diff` against a base ref (default `HEAD`), restricts the rule and trope checks to lines added or modified in `.tex` files, and writes `ai-slop-report.md` in the working directory using the same schema as `/ai-slop:review` so `/ai-slop:revise` can apply the suggestions unchanged.

The base ref is positional. Default is `HEAD` (uncommitted working-tree changes). Examples:

- `/ai-slop:review-diff` — working tree vs `HEAD` (uncommitted changes only).
- `/ai-slop:review-diff main` — working tree vs `main` (the whole branch's worth of changes).
- `/ai-slop:review-diff abc1234` — working tree vs a specific commit.

The trope catalog override flags from `/ai-slop:review` (`--tropes=<path>`, `--refresh-tropes`, `--edit-tropes`) work the same way here. They remain a rare corner case.

If the working directory is not inside a git repository, fall back to telling the user to run `/ai-slop:review` instead — diff mode has nothing to compare against.

Do not modify the user's paper; the only output is `ai-slop-report.md` in the working directory.
