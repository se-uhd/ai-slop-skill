---
description: Fill the `% GROUNDING:` comments that review only flags as missing, and the `TODO verify` stubs left by revise or an earlier run — fetch each cited source, extract a verbatim supporting quote, and write it into the LaTeX (or a `TODO verify -- <reason>` stub when the source cannot be retrieved). LaTeX source only.
---

Use the `ai-slop:ground` skill.

The skill's workflow and inputs live in `skills/ground/SKILL.md`. By default it auto-detects the LaTeX root in the working directory; a `.tex` path can be passed as an argument to override. Ground mode closes the loop review opens: review *finds* `\cite{}` calls without a quote-backed `% GROUNDING:` comment, ground *fills* them; revise applies prose fixes and may plant `% GROUNDING: TODO verify <key>` stubs, which ground replaces with retrieved quotes. It runs `extract_cites.py` to gather each citation with the claim it supports and the source's BibTeX metadata, fans out one source-fetching agent per cited key (chunked to stay under rate limits), and runs `insert_grounding.py` to write the quotes back. The anti-fabrication rule is mandatory: a quote is written only when the source was actually retrieved; otherwise the comment is `TODO verify -- <reason>`. Grounding is LaTeX-only. The user inspects the edits with `git diff` and commits when satisfied.
