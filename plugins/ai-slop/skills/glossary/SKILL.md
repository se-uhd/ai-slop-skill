---
name: glossary
description: Extract or maintain a document's GLOSSARY.md and validate its terminology. Use when the user asks for a glossary, proposed definitions, a synonym audit, or a check that a paper or document uses one term for each concept. Flags competing names, conflicting meanings, undefined terms, and newly invented labels for existing concepts. Supports LaTeX, PDF, Markdown, and plain text. Writes a glossary and a terminology report, or validates an existing glossary with --check. Does not rewrite the document.
license: CC-BY-4.0
metadata:
  version: "2026-10_rev3"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Glossary Mode

Read the document to establish its concepts, propose definitions where needed, and
use the glossary to check how the document names those concepts. The glossary is
a maintained project document, and the terminology report records suggestions
for revising the source. Preserve distinctions that matter to the author's
argument and the connected prose that explains them.

## Client and paths

Resolve `<skill-dir>` to the absolute directory containing this `SKILL.md`, using
the path supplied by the client. Resolve bundled files relative to that directory,
while keeping the working directory at the user's project. Quote script paths
and do not require a client-specific environment variable.

In Claude Code, invoke `/ai-slop:glossary`. In other Agent Skills clients, select
the `ai-slop:glossary` skill. Sibling command names below refer to their skill
entries as well.

## Inputs and outputs

The optional positional argument names a `.tex`, `.pdf`, `.md`, or plain-text
document. Without a path, use `python3 "<skill-dir>/../../scripts/find_latex_root.py"`
to find the LaTeX root in the working directory. If none exists, use the sole PDF
in that directory. Ask the user to select a document only when the candidates
are ambiguous or no document was found.

The default glossary is `GLOSSARY.md` in the working directory. A
`--glossary=<path>` argument selects another path, resolved from that directory.
Read any existing glossary before extracting terms, and preserve its definitions,
structure, qualifications, links, and human edits. An invocation that creates a
glossary also validates the document against it in the same run.

With `--check`, read the existing glossary and write only `ai-slop-report.md`.
Do not create or update a glossary in this mode. If the selected glossary does not
exist, explain that a normal invocation creates it and stop. The source document
stays unchanged in both modes.

## Establish the concepts

Read `../../shared/rules-general.md`, especially `G.one-term`, `G.define-once`,
`G.distinct-synonyms`, `G.no-coinages`, and `G.context-first`. This mode checks
terminology and does not fetch the trope catalog or audit unrelated style,
citations, or statistics. Existing project terminology and an explicitly
designated codebook take precedence over a newly proposed preference.

Read the full document before choosing preferred terms. For LaTeX, follow
`\input{}` and `\include{}` inside the project tree, and examine the prose in
tables and captions as well as the body. For PDF, extract text with an available
tool and retain page or section locations. If extraction is unavailable or
incomplete, report that limit instead of claiming to have checked unseen text.

Identify the concepts that readers need to distinguish, including the object of
study, populations, units of analysis, methods, measures, and named artifacts
where relevant. For each concept, collect the terms and abbreviations used for
it, the passages that establish its meaning, and any relevant scope conditions.
Ordinary words need no glossary entry unless the document assigns them a
special meaning or their use creates ambiguity.

Compare meanings before grouping names. A sampling frame and a sample, a label
and a decision, or an agent loop and a session can name related but distinct
concepts. Keep both terms when the source supports the distinction, and explain
the boundary in their definitions. Where the source leaves the distinction
unclear, record the competing readings for author judgment rather than inventing
a definition or treating the terms as confirmed synonyms.

## Write or maintain the glossary

Prefer an established glossary term, then an explicit definition in the document,
then the author's predominant term for the same concept. Do not invent a new
label to replace several existing labels. A preference inferred from usage is a
proposal, and an existing definition is not silently replaced when a later
passage disagrees with it. Record the disagreement in the report.

For each entry, provide a concise definition and a source location with a short
verbatim supporting passage. Mark a definition as **Documented** only when the
source explicitly supplies it. Mark an inferred definition or a new preference
as **Proposed**, and state any uncertainty that affects its scope. A definition
must preserve what counts as an instance, what it excludes, and how it differs
from neighboring concepts, without adding facts that the source does not give.

Keep an existing glossary's format, including prose definitions and tables of
retired vocabulary. Add inferred entries under a clearly marked proposed section,
and leave established entries intact. Keep uncertain synonym groups and missing
information under author judgment instead of adding each competing name as a
new accepted concept. In `--check` mode, put all proposed additions in the report.

For a new glossary, group related concepts under headings that suit the document.
Use the following tables where their content is needed. Omit empty sections and
do not create entries merely to fill the format:

```markdown
# Glossary

<State the document and scope covered by the glossary.>

## <Concept group>

| Preferred term | Definition | Status | Source and supporting passage |
|---|---|---|---|
| <term> | <definition and boundary> | Documented or Proposed | <file:line or PDF page, short verbatim passage> |

## Accepted variants

| Preferred term | Accepted form | When it is appropriate |
|---|---|---|
| <term> | <abbreviation or short form> | <introduction, scope, or other condition> |

## Vocabulary to avoid

| Avoid | Use instead | Scope and reason | Evidence |
|---|---|---|---|
| <competing term> | <preferred term> | <the sense in which the two name one concept> | <locations supporting the equivalence> |

## Proposed additions and unresolved distinctions

<Proposed entries or definitions and the questions that the author must settle.>
```

Accepted abbreviations, ordinary inflections, and contextually clear short forms
are not unwanted synonyms. A vocabulary restriction applies to its stated sense,
not every occurrence of a word. For example, a preference for *commit history*
over *logs* in a discussion of version control does not rename runtime logs.

## Validate the document

Reread the source against the glossary, including passages that introduce terms
absent from it. Trace each important concept across sections and check its
definition, first use, and later names. Search known forms with `rg -n -F --`
when helpful, but read their contexts before reporting a finding.

Report competing names for the same referent, a term used for conflicting
concepts, uses that contradict a definition, and technical terms that need a
definition at first use. Also inspect new compounds, renamed abstractions, and
longer paraphrases that appear to name an existing concept, even when the glossary
does not list them as synonyms. Absence from the glossary alone is not a defect,
and adding another entry must not conceal a second name for the same thing.

For a suspected synonym or new label, show the source passage that establishes
the concept and the passage that uses the competing name. Explain why they refer
to the same thing and how the change improves the reader's understanding. Keep
genuine distinctions, a clear reference to an established concept, and approved
short forms. Do not replace ordinary descriptive wording with the full preferred
term in every sentence if the reference is already clear.

Check the scope and exceptions of retired-vocabulary entries before flagging a
match. Preserve quotations, attributed terminology, titles, literal identifiers,
commands, and external names, and check the surrounding author's prose instead.
When a glossary choice is only proposed, identify it as a proposed convention
in the report. An uncertain equivalence or conflicting authoritative definition
belongs under author judgment and receives no automatic replacement.

## Report and finish

Read the Report template in `../review/SKILL.md` for its schema, without running
the review workflow. Write `ai-slop-report.md` in that format. Include the
`**Paper:**` path, the version from this skill's metadata, the review date, and a
`**Glossary:**` path and status. Use `Findings by section` for a single document
or `Findings by file` for source spread across files. Each `#### Finding N`
contains `Rule`, `Location`, `Quote`, `Suggested revision`, and `Reason`, with a
rule key from the general layer and an exact source quote that revise mode can
locate. Put a supporting passage elsewhere in the document in `Reason` with its
location, and make replacements preserve the surrounding argument.

Use `Cross-cutting metrics` for the scope actually checked and counts of confirmed
terminology issues, not word quotas. Put proposed definitions, ambiguous synonym
groups, and conflicts in `Items requiring author judgment`. State when no
confirmed issue was found. For PDF input, explain that applying suggestions
requires editable source.

The report is a generated artifact. If the working directory is in a git
repository, add `ai-slop-report.md` to its root `.gitignore` when absent.
`GLOSSARY.md` is maintained content and must not be added to `.gitignore` by this
skill. Do not change project instruction files or the source document.

Run `python3 "<skill-dir>/../../scripts/lint_markdown.py" <output>` separately on
each written output and correct introduced Markdown errors. Read the outputs
back, then give the user their paths and the main terminology decisions or
unresolved questions. Stop after the glossary and report, without committing or
applying source changes. The user can apply concrete source suggestions with
`/ai-slop:revise`.
