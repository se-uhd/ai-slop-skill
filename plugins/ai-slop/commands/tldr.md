---
description: Run an AI slop review and condense it into a TL;DR with one short assessment per scanned file of whether the authors used AI tools in a reasonable way or in a way that makes the text harder to read, up to three bullets with the worst patterns, and a rating of their impact on readability.
---

Use the `ai-slop:tldr` skill.

The skill's workflow is in `skills/tldr/SKILL.md`. It runs the review of `/ai-slop:review` on a document or the review of `/ai-slop:review-repo` on a directory, writes the full `ai-slop-report.md` as that review does, and then writes `ai-slop-tldr.md`. For each scanned file with findings, the TL;DR gives the patterns' impact on readability (None, Minor, Moderate, Major, or Severe, with the share of the prose that needs a rewrite), the AI-use verdict (Reasonable, Harder to read, or Little sign of AI tools), an assessment of one to five sentences, and up to three bullets with the worst patterns, each with its count and a short quote. Each block stands on its own, without rule keys or references to the full report, so it can be passed on by itself. The files without findings are listed together. `scripts/count_findings.py` supplies the counts, the ranking of the patterns, the level, and the verdict.

The target is positional. Examples:

- `/ai-slop:tldr`: auto-detect the document in the working directory as `/ai-slop:review` does, or review the working directory as a repository when no LaTeX root or PDF is found.
- `/ai-slop:tldr thesis.pdf`: one document.
- `/ai-slop:tldr path/to/repo`: a whole repository.

`--scientific`, `--ste`, `--tropes=<path>`, `--commits=<spec>`, and `--no-commits` are passed to the review. Do not modify the reviewed text. The outputs are `ai-slop-report.md` and `ai-slop-tldr.md` in the working directory, plus their names in the repository's `.gitignore` when those lines are missing. `/ai-slop:revise` applies the full report.
