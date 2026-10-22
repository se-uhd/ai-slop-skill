---
description: Extract GLOSSARY.md from a paper or document, propose definitions, and check for synonyms, conflicting meanings, and new labels for existing concepts. Use --check to validate against an existing glossary without updating it.
---

Use the `ai-slop:glossary` skill.

The skill's workflow and inputs are in `skills/glossary/SKILL.md`. It reads a
LaTeX, PDF, Markdown, or plain-text document and creates or maintains
`GLOSSARY.md`, preserving established definitions and distinguishing proposed
ones. It validates the document against the glossary in the same invocation and
writes source suggestions to `ai-slop-report.md`, with uncertain distinctions
listed for author judgment. The source document stays unchanged.

```text
/ai-slop:glossary main.tex
/ai-slop:glossary draft.md
/ai-slop:glossary draft.md --check
/ai-slop:glossary paper.pdf --glossary=terminology/GLOSSARY.md
```

Without a document path, the skill finds the LaTeX root or the sole PDF in the
working directory. The default glossary is `GLOSSARY.md` in that directory, and
`--glossary=<path>` selects another. `--check` leaves the existing glossary
unchanged and writes only the report.
