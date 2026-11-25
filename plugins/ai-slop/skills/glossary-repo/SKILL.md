---
name: glossary-repo
description: Build or maintain GLOSSARY.md for a whole repository and check its terminology. Use when the user asks for a glossary of a code base, a project, or a paper repository, or for a check that its documentation, code comments, user-facing messages, and LaTeX or Markdown files use one term for each concept. Reads every text file of the repository through the shared repository scan, including the comments and prose string literals of source code, and the identifiers that name each concept. Flags competing names, conflicting meanings, undefined terms, avoided vocabulary, and newly invented labels for existing concepts. Writes a glossary and a terminology report grouped by file, or validates an existing glossary with --check. --ste adds the Simplified Technical English layer. Does not change the repository files that it checks.
license: CC-BY-4.0
metadata:
  version: "2026-11_rev8"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Repository Glossary Mode

Read the text of a whole repository to establish its concepts, record one term
for each concept in `GLOSSARY.md`, and check how the repository names them.
This mode is the repository counterpart of `/ai-slop:glossary`, which works on
one document. The glossary is maintained project content, and the terminology
report records suggestions for revising the files. Preserve distinctions that
matter to the project and the connected prose that explains them.

## Client and paths

Resolve `<skill-dir>` to the absolute directory containing this `SKILL.md`,
using the path supplied by the client. Resolve bundled files relative to that
directory, while keeping the working directory at the user's project. Quote
script paths and do not require a client-specific environment variable.

In Claude Code, invoke `/ai-slop:glossary-repo`. In Codex, select the
`ai-slop:glossary-repo` skill through `/skills` or a `$` mention. In pi, invoke
`/skill:glossary-repo`. References to other `/ai-slop:` commands below mean
the corresponding sibling skill in any client.

## Inputs and outputs

The skill reads the repository rooted at the current working directory. A
positional path to a directory overrides it. For one document, use
`/ai-slop:glossary`.

- **Glossary.** The default is `GLOSSARY.md` at the repository root, or the
  glossary that the project instructions name. `--glossary=<path>` selects
  another path, resolved from the repository root.
- **Check mode.** `--check` reads the existing glossary and writes only
  `ai-slop-report.md`. If the glossary does not exist, explain that a normal
  invocation creates it and stop. Without `--check`, the skill creates or
  updates the glossary and checks the repository against it in the same run.
- **Scan options.** `--exclude=<glob>` (repeatable) skips the files that match
  a shell pattern relative to the root, such as `data/*`. `--no-strings` reads
  only the comments of source files and not their string literals.
  `--commits=<spec>` adds commit messages, which the scan leaves out by
  default, with the selectors of `/ai-slop:review-repo`.
- **STE.** `--ste` loads the Simplified Technical English layer (see Check the
  repository).

The skill writes the glossary (not in check mode) and `ai-slop-report.md` in
the working directory. It does not edit the other files of the repository.

## Scan the repository

Run `python3 "<skill-dir>/../../scripts/scan_repo.py" <root> --no-commits`,
or with the user's `--commits=<spec>` in place of `--no-commits`, and append
the user's `--exclude` and `--no-strings` arguments. Each stdout line is
`<relpath>:<line>:<text>`. The scan covers the tracked files, reads Markdown,
plain text, and LaTeX in full, and extracts the comments, doc-comments, and
prose string literals of source and config files and the text of user
interface templates, in HTML files, in the template literals of JavaScript
and TypeScript, and in JSX. Text between tags appears as `>text<`, and a
string literal or attribute value keeps its quote characters, which tells
both from a comment. Short strings under keys that name text, such as
`label: 'Manage users'`, are included too, so the labels of the interface
reach the check. The module docstring of the script documents what it skips, such as generated files, test strings,
vendored directories, and binaries. Save the output to a file in the
scratchpad or a temporary directory and read it from there.

Before reading the lines, list the directories with their line counts, for
example with `cut -d: -f1 <scan> | sed 's|/[^/]*$||' | sort | uniq -c`. Sort
the directories into the following kinds:

- **Defining sources** state what the terms mean: the README files, the
  project instructions (`AGENTS.md`, `CLAUDE.md`), design documents,
  specifications, current decision records, a codebook, the main manuscript of
  a paper, and the docstrings of the main modules. Read in full the parts that
  describe the product, its concepts, and its terms, and search the parts on
  building, deployment, and tooling for the terms.
- **Using sources** use the terms: the other documentation, code comments,
  user-facing strings, scripts, and tests. Read them from the scan output, one
  directory at a time, and keep a running list of concepts and names.
- **Records** keep the terms of their date: a changelog, dated notes, logs,
  release notes, decision records that describe a past state, and commit
  messages. Their former names help fill the table of vocabulary to avoid, but
  they are not changed. Name them in the scope paragraph of the glossary.
- **Data** is text that the project stores but did not write as its own prose,
  such as collected documents, transcripts, datasets, fixtures, and the full
  texts of reviewed papers. Run the scan again with an `--exclude` pattern for
  each data directory, and name the exclusion in the scope paragraph. If it is
  unclear whether a large directory is data or project prose, ask the user.

Sort a directory by what it holds, not by its name. A module named `data/`
that holds source code is a using source. When the using sources are too large
to read in one pass, as a guide more than about 5,000 scan lines, read them
through searches instead: the candidates that `scan_glossary.py` lists and a
search of the scan for the names, variants, and likely competing names of each
concept. The report names the directories read in full and those covered by
searches.

## Establish the concepts

Read `../../shared/rules-general.md`, especially `G.one-term`,
`G.define-once`, `G.distinct-synonyms`, `G.no-coinages`, and
`G.context-first`, and read `../../shared/glossary-format.md`. With `--ste`,
also read `../../shared/rules-ste.md`. This mode checks terminology and does
not fetch the trope catalog or audit unrelated style. Existing project
terminology, an explicitly designated codebook, and the wording of a user
interface that the project names as its reference take precedence over a newly
proposed preference.

Identify the concepts that readers need to distinguish, such as the parts of
the system, roles, data, units, states, processes, measures, and named
artifacts. For each concept, collect the following:

- the terms, abbreviations, and paraphrases that the documents, comments, and
  strings use for it, with their locations
- the passages that define it or state its scope
- the identifiers that name it, found by searching the code for the forms of
  each candidate term (snake_case, camelCase, PascalCase, kebab-case) with
  `git grep -n -i -E` and by reading the declarations of the main types,
  modules, configuration keys, and commands

Compare meanings before grouping names. Two subsystems can use one word for
different concepts, such as "host" for a developer machine and for a
production server, and related concepts, such as a session and the agent loop
inside it, keep separate entries when the sources support the distinction.
Where the sources leave a distinction unclear, record the competing readings as
an open question instead of inventing a definition or treating the terms as
synonyms.

## Write or maintain the glossary

Skip this section in check mode.

Prefer an established glossary term, then an explicit definition in a defining
source, then the wording that users see in the interface and messages, then
the predominant term across the repository. Do not invent a new label to
replace several existing labels. A preference inferred from usage is a
proposal, and an existing definition is not silently replaced when a later
passage disagrees with it. Record the disagreement in the report.

Write the glossary in the format of `../../shared/glossary-format.md`, with the
Code column. The scope paragraph names the directories and kinds of text that
the glossary covers, the records and data that the check skips, and the source
that decides between sources. Mark a definition as proposed unless a defining
source states it. A definition must preserve what counts as an instance, what
it excludes, and how it differs from neighboring concepts, without adding facts
that the sources do not give. With `--ste`, write the definitions, the scope
paragraph, and the reasons in the avoid table in STE.

An existing glossary keeps its structure, its definitions, and the edits of
its authors, unless the user asks to convert it to the format. Add new
concepts to the matching section, with "Proposed," in the Source cell.

A term of the glossary is never vocabulary to avoid. Before finishing, run
`python3 "<skill-dir>/../../scripts/scan_glossary.py" <glossary> --lint`. It
exits with status 1 and names each avoided word that is also a term or a
variant of one. Remove each such word from the avoided vocabulary and state
the distinction in the definition of the term, as
`../../shared/glossary-format.md` describes, in an existing glossary too.

## Check the repository

Check the repository against the glossary in both modes.

1. **Avoided vocabulary.** Pipe the scan into
   `python3 "<skill-dir>/../../scripts/scan_glossary.py" <glossary> --root=<root> --counts`,
   adding an `--exclude=<glob>` for each record or data path that the glossary
   exempts, in its scope paragraph or, in an older format, wherever it names
   the exempt files. The counts show how many uses each avoided word has and
   the scope that the glossary states for it, such as the Scope and reason
   cell or a sense in parentheses, and the words without a use come last
   with zero counts. An avoided word that is also a term is named on stderr,
   left out of the counts, and reported as a defect of the glossary (below).
   Without a scope paragraph, the check covers every scanned
   file except the records and data. Run the scan again without `--counts` to
   list the uses. Judge every use of a word that the glossary avoids in every
   sense. For a word avoided in one sense, read enough uses to find those in
   the avoided sense, searching the list for the contexts in which that sense
   occurs, and report the uses in that sense. The script lists candidates, and
   the scope decides each one.
2. **Competing names.** Trace each concept across the defining and using
   sources. Report a second name for the same referent, a term used for
   conflicting concepts, a use that contradicts a definition, a technical term
   that a document uses without a definition, and a new compound, renamed
   abstraction, or long paraphrase that names an existing concept, even when the
   glossary does not list it as a synonym. Absence from the glossary alone is
   not a defect. To find second names, search the scan for the phrases that
   share the head noun of a term, such as "wall link" or "login link" beside
   "coffee link", and read the labels and headings of the interface (the
   `>text<` lines and the quoted strings in the UI code).
3. **One meaning for each word.** With `--ste`, also apply `T.one-meaning` to
   the key words of the repository that are not glossary terms, such as "run",
   "check", or "issue", and report a word that takes a second meaning within
   one document or one module.

For each suspected synonym or new label, quote the passage that establishes
the concept and the passage that uses the competing name, explain why they
refer to the same thing, and state how the change helps the reader. Keep
genuine distinctions, a clear reference to an established concept, and
approved short forms. Do not replace ordinary descriptive wording with the full
term in every sentence when the reference is already clear.

When a word appears in the avoided sense in more places than the report can
list one by one, as a guide more than about 20, report a few representative
uses as findings, and put the count and the files under author judgment,
since the authors decide between a sweep and a change of the glossary.

Report a defect of the glossary itself as a finding on the glossary under
`G.distinct-synonyms`, with a suggested revision of its line:

- an avoided word that is also a term: the revision removes the word from the
  avoided vocabulary and states the distinction in the definition of the term
- an avoided word without a sense that the project uses correctly in other
  senses: the revision names the avoided sense
- a row that rules out a label of the interface that the glossary names as its
  reference: the revision limits the row to the other text

A definition that the code contradicts goes under author judgment, since the
authors decide which of the two is right.

Quotations, attributed terminology, titles, external names, commands, and
identifiers keep their wording. A finding on a string literal changes what the
program prints, and tests or documentation can quote the message, so its
Reason names the places that quote it, including generated files that the
scan skips, such as an API specification. In STE mode, a string literal is a
literal string under `T.literals`: report a competing term in it, and leave its
wording otherwise as written. An identifier that uses an avoided word or a
second name is not renamed by a suggested revision, since renaming code is a
refactoring. List it under author judgment with the files that declare it.

## Report and finish

Read the report template in `../review/SKILL.md` for its schema, without
running the review workflow. Write `ai-slop-report.md` in that format, with
the repository root as `**Paper:**`, `### <relpath>` headings under "Findings
by file", as `/ai-slop:review-repo` does, and the following header lines under
`**Reviewed:**`:

```text
**Repo scope:** root=<repo root>, files=<N scanned>, commits=<N scanned>, prose lines=<N>
**Glossary:** <path>, <created | updated | checked>
```

`prose lines` counts the lines of the scan that the check read, after the
exclusions. Include the version from the metadata of this skill and the review
date. Each
`#### Finding N` contains `Rule`, `Location`, `Quote`, `Suggested revision`,
and `Reason`, with a rule key from the general layer (or `T.one-meaning` in
STE mode) and an exact quote from one line of the file, not the scan line and
without the comment leader of a wrapped doc-comment, so that `/ai-slop:revise`
can locate it. The Reason of a finding on avoided vocabulary names the row of
the glossary (`GLOSSARY.md:<line>`), and the Reason of a finding on a second
name says that the glossary does not list it. Put a supporting passage from
another file in `Reason` with its location.

Use `Cross-cutting metrics`, in place of the subsections of the template, for
the scope actually checked: the directories read in full and those covered by
searches, the excluded records and data, the counts from
`scan_glossary.py --counts`, and the counts of confirmed terminology issues.
Put proposed definitions, open questions, identifiers that use another name,
and uses in records under `Items requiring author judgment`. Write each
proposed definition in full, in the format of the glossary and with its
source, so that the authors can confirm it as written. State when no
confirmed issue was found.

The report is a generated artifact. Add `ai-slop-report.md` to the root
`.gitignore` of the repository when it is absent. `GLOSSARY.md` is maintained
content and must not be added to `.gitignore`. Do not change project
instruction files or the files that the report covers.

Run `python3 "<skill-dir>/../../scripts/lint_markdown.py" <output>` separately
on each written output and correct introduced Markdown errors. Read the outputs
back, then give the user their paths, the main terminology decisions, and the
open questions. Stop after the glossary and the report, without committing or
applying changes. `/ai-slop:revise ai-slop-report.md <file>` applies the
findings for one file.

## Bundled files

- `../../shared/glossary-format.md` defines the format of the glossary.
- `../../shared/rules-general.md` and, with `--ste`, `../../shared/rules-ste.md`
  hold the terminology rules.
- `../../scripts/scan_repo.py` extracts the text of the repository, and
  `../../scripts/scan_glossary.py` lists the uses of avoided vocabulary. Their
  module docstrings document inputs, outputs, exit codes, and limitations.
- `../../scripts/lint_markdown.py` lints the outputs.
