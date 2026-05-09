---
description: Review a paper draft for AI slop and violations of the SE writing rules. Generates a structured Markdown report with concrete suggested revisions.
---

Use the `ai-slop:review` skill.

The skill's workflow and report template live in `skills/review/SKILL.md`. By default the skill scans the current working directory for the paper to review (LaTeX root first, falling back to PDF). A path to a `.tex` or `.pdf` can be passed as an argument to override the scan.

By default the review fetches the trope catalog from the live source (upstream Gist → tropes.fyi viewer → bundled `shared/tropes-snapshot.md`). To override for a single run, pass `--tropes=<path>` (repeatable). Each named file is read as-is and the contents are concatenated in the order given to form the catalog.

Do not modify the user's paper; the only output is `ai-slop-report.md` in the working directory.
