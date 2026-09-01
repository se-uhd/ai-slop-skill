---
description: Review any prose for AI slop and rule violations. The general rules apply by default; `.tex` source auto-loads the scientific and LaTeX layers, which add citations, statistics, BibTeX, a reference check, and a grounding to-do, and `--scientific` adds the scientific layer to a non-LaTeX manuscript. Generates a structured Markdown report with concrete suggested revisions.
---

Use the `ai-slop:review` skill.

The skill's workflow and report template live in `skills/review/SKILL.md`. By default the skill scans the current working directory for the paper to review (LaTeX root first, falling back to PDF). A path to a `.tex`, `.pdf`, or plain-text file can be passed as an argument to override the scan. The rule layers are chosen automatically. A LaTeX source (`.tex`, detected by `scripts/detect_scope.py`) loads all three layers (general + scientific + LaTeX). Any other input loads the general layer only. Add `--scientific` to also apply the research-article rules to a non-LaTeX manuscript (a Markdown or PDF paper); LaTeX includes them automatically.

By default the review fetches the trope catalog from the live source (the upstream Gist, then the tropes.fyi viewer, then the bundled `shared/tropes-snapshot.md`). To override for a single run, pass `--tropes=<path>` (repeatable). Each named file is read as-is and the contents are concatenated in the order given to form the catalog.

Do not modify the user's document. The only output is `ai-slop-report.md` in the working directory.
