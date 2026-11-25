# Glossary format

`/ai-slop:glossary` and `/ai-slop:glossary-repo` write and maintain
`GLOSSARY.md` in this format. A glossary names one term for each concept that
readers of a project have to tell apart, defines the term, and lists the words
that the project does not use for it. It records decisions and their sources.
The uses of each term in the text are evidence for a check, so they belong in
the terminology report (`ai-slop-report.md`), which a later check writes again.

## Principles

1. State each fact once. A variant, an identifier, or a decision belongs to the
   entry of its concept. A distinction between two concepts goes in the entry
   of the term that readers confuse with the other, and other entries use the
   defined term without explaining it again.
2. Keep definitions short. A definition says what kind of thing the concept
   is, which property distinguishes it from its neighbors, and what does not
   count as an instance. Behavior, procedures, defaults, file layouts, counts,
   and history belong in the documentation that the Source cell names.
3. Put content with the same parts in every entry into a table, and use prose
   for the scope paragraph, the lead sentences, and the open questions.
4. Include the concepts that readers have to tell apart, such as the object of
   study or the parts of a system, roles, data, units, measures, and named
   artifacts. An ordinary word needs an entry only when the project gives it a
   special meaning or uses it for two concepts.

## Structure

A glossary has a scope paragraph, one section for each group of concepts, a
table of vocabulary to avoid, and a list of open questions:

```markdown
# Glossary

<Scope paragraph>

## <Group of concepts>

<Lead sentence, when the rows share a relation>

| Term | Definition | Code | Source |
|---|---|---|---|

<Value table, when a concept has a closed set of values>

## Vocabulary to avoid

| Avoid | Use instead | Scope and reason |
|---|---|---|

## Open questions

- <Question>
```

The format has no separate tables for accepted variants, abbreviations,
identifiers, decisions, or the status of a definition, and no column of
locations where a word is used. Each of these belongs in a cell of a concept
row or in the report.

### Scope paragraph

One paragraph under the title, without a heading, states the following:

- The documents, directories, and kinds of text that the glossary covers, such
  as the documentation, the code comments, and the messages that users see.
- The text that keeps its own wording: quotations, identifiers, and records
  that keep the terms of their date, such as a changelog, dated decision
  records, and logs. Name these records by path or pattern (`docs/adr/*`),
  because the check reads its exemptions from this paragraph.
- The source that decides when sources disagree, such as a codebook, a
  standard, or the wording of the user interface.
- That a Source cell that starts with "Proposed" marks a definition inferred
  from use, which the authors have not confirmed.

### Groups of concepts

Each group of concepts is a `##` section named with a noun phrase in sentence
case, such as "Builds and releases", "Populations", or "Coding and checks".
Order the sections, and the rows within a section, so that a term is defined
before an entry uses it. When the rows of a section stand in one relation,
such as populations that are each drawn from the one above or the stages of a
pipeline, order the rows by that relation and state it once in a lead sentence
above the table. Divide a section into `###` subsections only when it covers
two subsystems or holds more than about 15 rows.

### Concept table

The columns are Term, Definition, Code, and Source. Leave out the Code column
when no code names the concepts, as in the glossary of a paper.

- **Term.** The preferred term as it appears in running text, lowercase unless
  it is a proper noun. Accepted variants follow in parentheses, such as an
  abbreviation or a short form for later mentions: `Global South (GS)`,
  `release tag (the tag)`. The last sentence of the definition states a
  condition on a variant. Two terms that differ only in one qualifier, such as
  a read lock and a write lock, can share a row.
- **Definition.** One to three sentences that give the kind of thing, the
  distinguishing property, and, where a neighboring concept invites confusion,
  what is not an instance. The definition uses the other terms of the glossary
  as they are defined.
- **Code.** The main identifiers that name the concept, each in a code span,
  such as a type, a module, a file, a configuration key, a command, or a route.
  An identifier that keeps an avoided word carries the reason in parentheses,
  as in `` `items` (the name in the API response) ``.
- **Source.** The location that supports the definition (`path:line`, a section
  of the document, a PDF page, or a link to an external source with its
  section) and a verbatim passage of at most about twelve words in double
  quotes. A definition inferred from use starts with "Proposed," and gives the
  location of a typical use. Authors confirm a definition by deleting
  "Proposed,".

### Value tables

A concept with a closed set of values, such as states, codes, roles, or
levels, gets a table with the columns Value and Meaning directly below the
concept table. A sentence that names the concept introduces the table, and the
values that the code or the data uses literally are in code spans. The concept
row does not list the values again.

### Vocabulary to avoid

One table for the whole glossary, sorted alphabetically by its first column:

- **Avoid.** The avoided words and phrases, separated by commas, as plain text
  without quotes, emphasis, or qualifiers, so that `scan_glossary.py` and a
  test of the project can match them. A plural that does not end in "s" or
  "es" is listed separately.
- **Use instead.** The term from the concept tables, or a plain phrase when the
  avoided word does not name a concept of the glossary.
- **Scope and reason.** The sense in which the word is avoided, the part of the
  project where the restriction applies when it does not apply everywhere, and
  the reason in one sentence. A word avoided in one sense remains correct in
  its other senses, and the cell names the sense. A word avoided only in one
  spelling of capitals says so, as in "With a capital C", and the scan then
  matches that spelling only. Exemptions that the scope paragraph states are
  not repeated.

The table never lists a term of the concept tables or a variant of one, not
even in one sense. When readers use a term for a neighboring concept, as
"rating" for the score of a rating, the definition of the term that readers
confuse states the distinction (principle 1). `scan_glossary.py --lint` names
each avoided word that is also a term.

### Open questions

A bulleted list of the distinctions and choices that the sources leave open.
Each item names the terms, gives the competing readings with their locations,
and says what would settle the question. A settled question leaves the list,
and the decision goes into the rows that it changes. Leave out the section
when no question is open.

## Existing glossaries

Keep the structure of an existing glossary unless the user asks to convert it.
An avoided word that is also a term is a defect in any structure, and every
update removes the word from the avoided vocabulary and states the
distinction in the definition of the term. A conversion keeps every definition, variant, restriction, and decision. It
moves accepted variants into the Term cells, identifier lists into the Code
cells, decisions into the definitions or the rows of the avoid table that they
settle, and a status column into the "Proposed," marker. It drops columns that
list where a word is used.

## Example

```markdown
# Glossary

This glossary covers the README, the documents in `docs/`, and the comments
and user-facing messages of the code in `src/`. `CHANGELOG.md` and the
decision records in `docs/adr/*` keep the terms of their date, and quotations
and identifiers keep their wording. Where the documents disagree,
`docs/releasing.md` decides. A source that starts with "Proposed" marks a
definition inferred from use, which the maintainers have not confirmed.

## Builds and releases

| Term | Definition | Code | Source |
|---|---|---|---|
| bundle | The archive that the server installs: one directory with the executable and the manifest. | `Bundle`, `dist/<id>.tar.gz` | `README.md:41`, "The bundle is the archive that the server installs" |
| test build | A bundle built from uncommitted changes. It cannot replace a release bundle. | `build.py --dirty` | `README.md:52`, "a test build skips the check for uncommitted changes" |
| release | One published version: its release tag, its changelog section, and its bundle. | `publish_release()` | `docs/releasing.md:8`, "A release is the tag, the changelog section, and the bundle" |
| release tag (the tag) | The signed git tag `v<version>` of a release. Write *the tag* only after the first mention in a section. | `RELEASE_TAG_RE` | Proposed, `docs/releasing.md:12` |

`build.json` records the state of a build:

| Value | Meaning |
|---|---|
| `pending` | The build has started and has not finished. |
| `built` | The bundle exists, and its checksum is recorded. |
| `failed` | The build stopped with an error, and the log names the step. |

## Vocabulary to avoid

| Avoid | Use instead | Scope and reason |
|---|---|---|
| artifact, package | bundle | For the archive. "Package" remains correct for a Go package. |
| dev build | test build | One name for a bundle built from uncommitted changes. |
| ship, shipping | publish | For making a release available. `publish_release()` performs the step. |

## Open questions

- release and version: `docs/releasing.md:8` uses "release" for the tag, the
  changelog section, and the bundle, and `src/version.py:3` uses "version" for
  the same set. A decision of the maintainers settles whether "version" names
  only the number.
```
