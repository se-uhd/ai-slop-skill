---
description: Apply the findings of an `/ai-slop:review` report to the source, replacing each flagged quote with its suggested revision and inserting `% GROUNDING` to-do stubs for ungrounded citations.
---

Use the `ai-slop:revise` skill.

The skill's workflow and inputs are in `skills/revise/SKILL.md`. By default the skill reads `ai-slop-report.md` from the working directory and auto-detects the document (the path named in the report header, or the LaTeX root in the working directory). Explicit paths can be passed as arguments to override either default. Revise mode edits the source in place. It applies the report's suggested revisions and, for LaTeX, inserts `% GROUNDING` stubs for ungrounded citations. A Markdown or plain-text draft reviewed by `/ai-slop:review` is revised the same way, and a repo-mode report is applied one file at a time. The user is expected to use `git diff` to inspect changes and `git commit` to keep them.
