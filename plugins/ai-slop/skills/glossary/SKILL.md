---
name: glossary
description: Extract or maintain GLOSSARY.md for a document and validate its terminology. Use when the user asks for a glossary, proposed definitions, a synonym audit, or a check that a paper or document uses one term for each concept. Flags competing names, conflicting meanings, undefined terms, and newly invented labels for existing concepts. Supports LaTeX, PDF, Markdown, and plain text, and finds the main document when no filename is supplied. Writes a glossary and a terminology report, validates an existing glossary with --check, or converts it to the format and to ISO 704 definitions with --convert. --ste adds the Simplified Technical English layer. Does not rewrite the document. For the text of a whole repository, use glossary-repo.
license: CC-BY-4.0
metadata:
  version: "2026-11_rev11"
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

In Claude Code, invoke `/ai-slop:glossary`. In pi, invoke `/skill:glossary`. In
other Agent Skills clients, select the `ai-slop:glossary` skill. Sibling command names below refer to their skill
entries as well.

## Inputs and outputs

The optional positional argument names a `.tex`, `.pdf`, `.md`, or plain-text
document. When it is omitted, search the working directory and relevant
subdirectories for the main document as described below. Once a clear candidate
is found, read it and build the glossary without asking the user to supply a
filename. The same discovery applies in `--check` mode. For a glossary of the
documentation, code comments, and messages of a whole repository, use
`/ai-slop:glossary-repo` instead. `--ste` loads the Simplified Technical
English layer (see Validate the document).

The default glossary is `GLOSSARY.md` in the working directory. A
`--glossary=<path>` argument selects another path, resolved from that directory.
Read any existing glossary before extracting terms, and preserve its definitions,
structure, qualifications, links, and human edits. An invocation that creates a
glossary also validates the document against it in the same run.

With `--convert`, rewrite the existing glossary into the format and its
definitions into the form of ISO 704 before the check (see Convert an existing
glossary).

With `--check`, read the existing glossary and write only `ai-slop-report.md`.
Do not create or update a glossary in this mode. If the selected glossary does not
exist, explain that a normal invocation creates it and stop. The source document
stays unchanged in both modes.

## Find the main document

List the candidate documents, including LaTeX sources, PDFs, Markdown, and
plain text. Examine project instructions, the README, and build
configuration for pointers to the main manuscript or document. Search relevant
subdirectories, such as `paper/`, `manuscript/`, or `docs/`, when the root directory
does not contain it. Use filenames, titles, and document structure to distinguish
the main work from supporting material, and read enough context to make the
selection.

For LaTeX, run `python3 "<skill-dir>/../../scripts/find_latex_root.py"` to identify
root candidates. Treat the returned path or candidate list as evidence alongside
the project context, and inspect alternatives when several manuscripts are
present. Select the root that builds the main manuscript, then follow its
`\input{}` and `\include{}` files as part of reading it. Prefer editable source,
including Markdown or plain text, over a generated PDF of the same work.

Do not mistake `GLOSSARY.md`, `WRITING.md`, instruction files, review reports,
bibliographies, vendored examples, archived drafts, or downloaded literature for
the main document. A README can be the main document when it contains the
primary exposition of the project rather than just instructions for building a paper.
A sole PDF is a candidate, not proof that it is the main work. Ask the user only
if no document can be found after this search or several candidates remain
plausible without a clear basis for selecting one. Record the selected document
and the files actually read in the scope of the glossary and the report.

## Establish the concepts

Read `../../shared/rules-general.md`, especially `G.one-term`, `G.define-once`,
`G.distinct-synonyms`, `G.definition-form`, `G.no-coinages`, and
`G.context-first`, and read
`../../shared/glossary-format.md`. With `--ste`, also read
`../../shared/rules-ste.md`. This mode checks terminology and does not fetch
the trope catalog or audit unrelated style, citations, or statistics. Existing project terminology and an explicitly
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

Write the glossary in the format of `../../shared/glossary-format.md`. Leave
out the Code column unless the document names concepts with identifiers, as
the documentation of a library does. Each concept row gives a concise
definition and a source location with a short verbatim supporting passage.
Mark a definition as proposed ("Proposed," at the start of the Source cell)
unless the source explicitly supplies it, and state any uncertainty that
affects its scope. Write each definition in the form that the format
describes, following `G.definition-form`: the superordinate concept without an
article, the delimiting characteristics, and notes for the rest. A definition
and its notes must preserve what counts as an instance, what it excludes, and
how it differs from neighboring concepts, without adding facts that the source
does not give. Apply the substitution test to each definition: put it in place
of the term in a sentence of the document, and revise it when the meaning
changes. With `--ste`, write the definitions, the notes, the scope paragraph,
and the reasons in the avoid table in STE.

An existing glossary keeps its structure, its definitions, and the edits of its
authors, unless the user asks to convert it to the format or passes `--convert`
(see Convert an existing glossary). Add inferred entries
to the matching section with "Proposed," in the Source cell, and leave
established entries intact. Keep uncertain synonym groups and missing
information under open questions instead of adding each competing name as a new
accepted concept. In `--check` mode, put all proposed additions in the report,
each written in full in the format of the glossary.

## Convert an existing glossary

With `--convert`, rewrite the existing glossary into the format of
`../../shared/glossary-format.md` before the check. Without the flag, a
conversion happens only when the user asks for it.

1. Read every entry of the old glossary and give it a concept row in the group
   of concepts that it belongs to. Accepted variants and abbreviations go into
   the Term cell, identifiers into the Code cell, and the file or section that
   defines the concept into the Source cell.
2. Rewrite each definition in the form of `G.definition-form`: one statement
   without an article that starts with the superordinate concept and names
   the delimiting characteristics. Apply the substitution test to it. Move
   every other sentence of the old definition into a note that starts with
   "Note:", or into the documentation that the Source cell names when the note
   would only repeat it. Keep every restriction and decision.
3. Move the avoided words into the avoid table with the replacement and the
   sense that the old entry gave. Resolve each avoided word that is also a
   term as "Existing glossaries" in the format describes.
4. Run `scan_glossary.py <glossary> --lint --definitions` and revise each
   listed definition until only the exceptions of its kind remain.
5. List the conversion in the report: for each old entry its new row, and each
   sentence that moved into a note, into the documentation, or out of the
   glossary, so that the author can check that no content was lost.

A term of the glossary is never vocabulary to avoid. After writing the
glossary, run `python3 "<skill-dir>/../../scripts/scan_glossary.py" <glossary> --lint --definitions`.
It exits with status 1 and names each avoided word that is also a term or a
variant of one. Remove each such word from the avoided vocabulary and state
the distinction in a note of the term, as
`../../shared/glossary-format.md` describes, in an existing glossary too. The
script also lists the definitions that a pattern marks as deficient, such as a
definition that contains its term or two definitions that use each other's
term. Revise each listed definition that you added or changed, unless the
exception in its kind applies, and report the others.

Accepted abbreviations, ordinary inflections, and contextually clear short forms
are not unwanted synonyms. A vocabulary restriction applies to its stated sense,
not every occurrence of a word. For example, a preference for *commit history*
over *logs* in a discussion of version control does not rename runtime logs.

## Validate the document

Reread the source against the glossary, including passages that introduce terms
absent from it. Trace each important concept across sections and check its
definition, first use, and later names. Search for known forms as fixed strings
when helpful, but read their contexts before reporting a finding.

When the glossary lists vocabulary to avoid, run
`python3 "<skill-dir>/../../scripts/scan_glossary.py" <glossary> <file> ...`
over the document and the files that it includes, or over a text extraction of
a PDF. It lists each use of an avoided word with the replacement that the
glossary names. The list holds candidates, and the Scope and reason cell of the
row decides whether a use is in the avoided sense. The script also names on
stderr each avoided word that is a term of the glossary, which is a defect of
the glossary (below). With `--ste`, also apply
`T.one-meaning` to the key words of the document that are not glossary terms,
and report a word that takes a second meaning.

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

Check the scope and exceptions of the rows of the avoid table before flagging a
match. Preserve quotations, attributed terminology, titles, literal identifiers,
commands, and external names, and check the surrounding author's prose instead.
When a glossary choice is only proposed, identify it as a proposed convention
in the report. An uncertain equivalence or conflicting authoritative definition
belongs under author judgment and receives no automatic replacement.

Report a defect of the glossary itself as a finding on the glossary under
`G.distinct-synonyms`, with a suggested revision of its line: an avoided word
that is also a term leaves the avoided vocabulary while a note of the term
states the distinction, and an avoided word without a sense that the document
uses correctly in other senses gets the avoided sense.

Report a deficient definition as a finding on the glossary under
`G.definition-form`, with the definition rewritten in the form of the format
as the suggested revision. Run
`python3 "<skill-dir>/../../scripts/scan_glossary.py" <glossary> --definitions`
for the candidates that a pattern finds, and apply the substitution test to
the other definitions. The Reason names the defect and its clause of ISO 704
from the list of deficient definitions in `../../shared/glossary-format.md`.

## Report and finish

Read the report template in `../review/references/report-template.md` for its schema, without running
the review workflow. Write `ai-slop-report.md` in that format. Include the
`**Paper:**` path, the version from the metadata of this skill, the review date, and a
`**Glossary:**` path and status (created, updated, or checked). Use `Findings by section` for a single document
or `Findings by file` for source spread across files. Each `#### Finding N`
contains `Rule`, `Location`, `Quote`, `Suggested revision`, and `Reason`, with a
rule key from the general layer (or `T.one-meaning` in STE mode) and an exact
source quote that revise mode can locate. Put a supporting passage elsewhere in the document in `Reason` with its
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
