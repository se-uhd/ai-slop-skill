---
description: Review a text against the AI trope catalog and condense the review into a TL;DR that gives, per scanned file, the number of patterns that affect readability and up to five bullets with the patterns, their counts, and a quote each.
---

Use the `ai-slop:tldr` skill.

The skill's workflow is in `skills/tldr/SKILL.md`. It runs the review of `/ai-slop:review` on a document or the review of `/ai-slop:review-repo` on a directory against the tropes.fyi catalog only, with the rule layers serving only for their exceptions, writes the full `ai-slop-report.md` as that review does, and then writes `ai-slop-tldr.md`. Before the review, the skill works out which catalog patterns the conventions of the kind of text make normal, such as numbered concerns in a peer review, and records no finding for them. Formatting, single words, and restatements of a point just made are minor and do not count. For each scanned file with at least two other patterns, the TL;DR gives the number of patterns that affect readability and the word count, and up to five bullets, each with a fixed plain label, a count, and a short quote. It has no written assessment and does not say or suggest who or what wrote the text. Each block stands on its own, without rule keys or references to the full report, so it can be passed on by itself. The files that need no feedback are listed together. `scripts/count_findings.py` supplies the counts and the ranking of the patterns.

The target is positional. Examples:

- `/ai-slop:tldr`: auto-detect the document in the working directory as `/ai-slop:review` does, or review the working directory as a repository when no LaTeX root or PDF is found.
- `/ai-slop:tldr thesis.pdf`: one document.
- `/ai-slop:tldr path/to/repo`: a whole repository.
- `/ai-slop:tldr reviews/ The reviewers are non-native speakers.`: a directory, with instructions for the run.

Text after the path that is not a flag is the user's instructions. They can set what the review covers, exempt or add a pattern, and give context for the genre step, but they do not change the counts. `--tropes=<path>`, `--commits=<spec>`, and `--no-commits` are passed to the review, and `--scientific` marks a Markdown or PDF manuscript as a research article. Do not modify the reviewed text. The outputs are `ai-slop-report.md` and `ai-slop-tldr.md` in the working directory, plus their names in the repository's `.gitignore` when those lines are missing. `/ai-slop:revise` applies the full report.
