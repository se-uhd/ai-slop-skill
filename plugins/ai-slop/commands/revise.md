---
description: Apply the findings of an `/ai-slop:review` report to the paper, replacing each flagged quote with the report's suggested revision.
---

Use the `ai-slop:revise` skill.

The skill's workflow and inputs live in `skills/revise/SKILL.md`. By default the skill reads `ai-slop-report.md` from the working directory and auto-detects the paper (the LaTeX root in the working directory). Explicit paths can be passed as arguments to override either default. Revise mode edits the paper in place; the user is expected to use `git diff` to inspect changes and `git commit` to keep them.
