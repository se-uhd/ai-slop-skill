---
description: Find the main document when no filename is supplied, extract GLOSSARY.md, propose definitions, and check for synonyms, conflicting meanings, and new labels for existing concepts. Use --check to validate against an existing glossary without updating it.
---

Use the `ai-slop:glossary` skill.

The workflow and inputs are in `skills/glossary/SKILL.md`. It reads a
LaTeX, PDF, Markdown, or plain-text document and creates or maintains
`GLOSSARY.md`, preserving established definitions and distinguishing proposed
ones. It validates the document against the glossary in the same invocation and
writes source suggestions to `ai-slop-report.md`, with uncertain distinctions
listed for author judgment. The source document stays unchanged.

```text
/ai-slop:glossary
/ai-slop:glossary main.tex
/ai-slop:glossary draft.md
/ai-slop:glossary draft.md --check
/ai-slop:glossary paper.pdf --glossary=terminology/GLOSSARY.md
```

Without a document path, the skill searches the working directory and relevant
subdirectories for the main LaTeX, PDF, Markdown, or plain-text document. It uses
project context to select the main work and prefers editable source over a PDF
of the same document. The default glossary is `GLOSSARY.md` in the working
directory, and `--glossary=<path>` selects another. `--check` leaves the existing
glossary unchanged and writes only the report.
