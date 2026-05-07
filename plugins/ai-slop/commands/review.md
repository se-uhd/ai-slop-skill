---
description: Review a paper draft for AI slop and violations of the SE writing rules. Generates a structured Markdown report with concrete suggested revisions.
---

Use the `ai-slop:review` skill.

The skill's workflow and report template live in `skills/review/SKILL.md`. By default the skill scans the current working directory for the paper to review (LaTeX root first, falling back to PDF). A path to a `.tex` or `.pdf` can be passed as an argument to override the scan. Do not modify the user's paper; the only output is `ai-slop-report.md` in the working directory.
