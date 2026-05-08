---
description: Review a paper draft for AI slop and violations of the SE writing rules. Generates a structured Markdown report with concrete suggested revisions.
---

Use the `ai-slop:review` skill.

The skill's workflow and report template live in `skills/review/SKILL.md`. By default the skill scans the current working directory for the paper to review (LaTeX root first, falling back to PDF). A path to a `.tex` or `.pdf` can be passed as an argument to override the scan.

By default the review fetches the trope catalog from the live source (upstream Gist → tropes.fyi viewer → bundled `shared/tropes-snapshot.md`). Updating or editing the catalog is a rare corner case and is opt-in per run. Override flags never modify the plugin install tree:

- `--tropes=<path>` — load the catalog from the given file (absolute or working-directory-relative) for this run. Read as-is.
- `--refresh-tropes` — fetch the upstream Gist into `./tropes-snapshot.cache.md` in the working directory and use that copy for this run.
- `--edit-tropes` — seed `./tropes-snapshot.cache.md` from the live source (or the bundled fallback) when missing, then pause for the user to edit it before running this review against the edited copy.

`./tropes-snapshot.cache.md` is never read implicitly. To reuse it on a later run, pass `--tropes=./tropes-snapshot.cache.md`.

Do not modify the user's paper; the only output is `ai-slop-report.md` in the working directory.
