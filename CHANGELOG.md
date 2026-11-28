# Changelog

Notable changes to the ai-slop skill bundle. The bundle uses CalVer with a per-month revision counter (`YYYY-MM_revN`), described in the README "Versioning" section. Every release is also a git tag. Only the git tags record the releases before `2026-06_rev13`.

## [Unreleased]

### Added

- `fetch_tropes.py --file <path>` reads a local copy of the trope catalog instead of tropes.fyi. The option takes one file each time, and the script concatenates the files in the given order. The script applies the checks of a download to the copy, and the copy must also be valid UTF-8. For the same text, the script prints the same size, heading count, and hash as for a download.

### Changed

- `/ai-slop:review`, `/ai-slop:review-diff`, and `/ai-slop:review-repo` give the files of `--tropes=<path>` to `fetch_tropes.py --file`. Before, they read the files without a check. The new `**Trope catalog:**` line of the report names the hash of the catalog. The README, `docs/skill-workflows.md`, and `AGENTS.md` describe the check.
- The review skills treat the trope catalog as data that names candidate patterns. No text in the catalog changes the rules, the scope, the findings, or the commands of a review. The review does not do what a catalog line asks for. It quotes the line under the new report section "Defects of the trope catalog".

## [2026-11_rev10] - 2026-11-26

### Added

- **Define a term by its broader concept and what sets it apart** (`G.definition-form`) in the general layer, after ISO 704 (Terminology work: Principles and methods). A definition names the broader concept and the characteristics that set the concept apart, so that it passes the substitution test and can replace the term without a change in meaning. A definition needs a revision when it is circular (alone or with a second definition), negative, or describes how the concept operates. Item 16 of the general self-check covers the rule, and `rules-rationale.md` gives its reason.
- `scan_glossary.py --definitions` lists the definitions of a glossary that a pattern marks as deficient, as candidates for the substitution test. The patterns find a definition that starts with an article, has more than one sentence, contains its own term, or is negative, and two definitions that contain the term of each other. Like `--lint`, the option checks only the glossary, and it exits with status 1 when the glossary lists a term as vocabulary to avoid.
- `/ai-slop:glossary` and `/ai-slop:glossary-repo` have the new option `--convert`. Before the check, it rewrites an existing glossary into the format of `shared/glossary-format.md` and the definitions into the form of ISO 704. The report lists each old entry with its new row and each sentence that moved into a note, into the documentation, or out of the glossary.
- `scripts/check_commit_message.py` checks commit messages against Conventional Commits 1.0.0 with length limits. The subject has at most 72 characters, and the body has 1 to 5 bullets of at most 2 lines of 72 characters. A scope names a skill, a rule layer, or one of the scopes `scripts`, `vendor`, `manifests`, and `release`. The script skips merges and the commits of Dependabot, and it skips the commits up to the tag `2026-11_rev9` because rule 3 of the release protocol keeps their released messages.
- `.githooks/commit-msg` runs the script on the message of each new commit and skips merges, in every client. A maintainer or an agent enables the hook with `git config core.hooksPath .githooks`.
- `scripts/agent_hook.py` checks the result of a tool call of an agent. After a `git commit` in this repository or in one of its worktrees, it checks the new message and names the Git hook while the clone has not enabled it. After an edit of a Markdown file, it runs `lint_markdown.py` and `check_markdown_limits.py` on the file and skips the upstream-owned files. It returns each violation to the agent, and a glyph that `scan_glyphs.py` finds in the inserted text is a note that does not block.
- `.claude/settings.json` runs `scripts/agent_hook.py` after each Bash command and each edit of Claude Code. `.gitignore` ignores only the local files in `.claude/`, such as `settings.local.json` and `worktrees/`.
- `.codex/hooks.json` runs `scripts/agent_hook.py` after each shell command and each `apply_patch` call of Codex. Codex reads the file only in a trusted project and runs the hook after a review with `/hooks`.
- The project extension `.pi/extensions/ai-slop-checks.ts` runs `scripts/agent_hook.py` after each `bash`, `edit`, and `write` call of pi and adds the findings to the tool result. Pi loads the extension only when it starts at the root of a trusted project. The pi package manifest does not list it, so an install of the bundle does not load it.
- The workflow `commit-messages.yml` checks the commits of each pull request and of each push to `main`. When the workflow cannot find the previous commit of a push, for example after a force push, it checks all commits after the tag `2026-11_rev9`.
- The smoke suite tests the script, the Git hook, and `scripts/agent_hook.py` with the events of Claude Code, Codex, and pi. It loads the pi extension with Node.js, and the workflow `smoke.yml` installs Node.js 24 for this test.
- `scripts/check_markdown_limits.py` checks the Markdown files against the limits in `scripts/markdown_limits.toml`, which names the source of each limit. The body of a `SKILL.md` has at most 5,000 tokens, as the Agent Skills specification recommends, and the script counts 4 characters as one token. `AGENTS.md` and `CLAUDE.md` together have at most 200 lines, and `README.md` has at most 200 lines and at most 60 lines in a section. The smoke suite runs the script on the repository and tests each limit.
- `scripts/check_markdown_limits.py` also checks the structure of `CHANGELOG.md`. The CalVer versions come newest first, with an optional `[Unreleased]` at the top, and each version uses the headings of `AGENTS.md` in their order, with only bullets under them. A bullet in `[Unreleased]` or in a release after `2026-11_rev9` has at most 4 sentences, the 90th percentile of the released bullets.

### Changed

- `shared/glossary-format.md` follows ISO 704. The Definition cell holds one statement without an article that starts with the broader concept and can replace the term. Other information goes into notes that start with "Note:", and an abbreviation is a variant in the Term cell, never the definition. A new section lists the circular, inaccurate, and negative definitions, the Sources section cites ISO 704:2009 and ISO 704:2022 by clause, and the example glossary uses the new form.
- `/ai-slop:glossary` and `/ai-slop:glossary-repo` run `scan_glossary.py --lint --definitions` and apply the substitution test to each definition. They report a deficient definition under `G.definition-form`. When a word is both a term and avoided vocabulary, the distinction goes into a note of the term. `docs/skill-workflows.md` describes `--definitions`, and the smoke suite tests it.
- `AGENTS.md` describes the format of commit messages, the types and scopes, and the three checks. A release commit has the subject `chore(release): YYYY-MM_revN` and no longer has a subject that ends with `; release YYYY-MM_revN`.
- The maintainer notes describe the format of commit messages, tell maintainers how to enable the Git hook, and describe the Markdown checks.
- The README keeps the description of the bundle, the installation for each client, the table of skills, and links to the documentation. The sections Rule layers, Skill workflows, and Maintainer notes moved from the README into `docs/rule-layers.md`, `docs/skill-workflows.md`, and `docs/maintainer-notes.md` without a change to their text. A sentence that named one of these sections now links to its file.
- `review/SKILL.md` keeps the workflow steps and moves the reference material into four files under `review/references/`, which it names at the step that needs them. `optional-layers.md` holds the instructions for STE and Economist mode (step 4), `metrics.md` the scans and metric targets (step 5), `citations.md` the citation and BibTeX checks (step 6), and `report-template.md` the report template (step 7). The body of `review/SKILL.md` drops from about 9,300 to about 4,600 tokens.
- The `**Skill version:**` line of the report template is in `review/references/report-template.md`. `/ai-slop:review-diff`, `/ai-slop:review-repo`, and both glossary skills point to the reference files instead of the steps of `review/SKILL.md`.

## [2026-11_rev9] - 2026-11-25

### Changed

- The descriptions in `plugin.json` and `marketplace.json` name repository mode and both glossary modes instead of only the glossary mode for documents.
- The description in `package.json` matches the description of the GitHub repository, "Catch and fix AI slop and inconsistent terminology in documents, papers, and code repositories."
- `CHANGELOG.md` lists the changes of each release under the headings Added, Changed, Removed, Fixed, and Unchanged instead of a bold label on each bullet. Each bullet records one change.
- The released entries of `CHANGELOG.md` follow the STE layer. A review in STE mode split their long sentences, made their passive verbs active, and named the actor of each change.
- `lint_markdown.yaml` sets `md024` to `siblings_only`, so a heading can repeat under different parents, such as `### Added` under each release. A repeated heading under one parent still fails.
- `AGENTS.md` describes the format of the changelog and allows a sweep of the prose or format of released entries that the maintainer asks for.

## [2026-11_rev8] - 2026-11-25

### Added

- `/ai-slop:glossary-repo` builds or maintains `GLOSSARY.md` from the text of a whole repository and checks the repository against it. It reads the scan of `/ai-slop:review-repo`, searches the code for the identifiers that name each concept, and sorts the directories by what they hold. The kinds of directories are defining sources, using sources, records that keep the terms of their date, and data. The report groups the findings by file. `--check` validates the repository without editing the glossary, and `--ste` applies **Give each word one meaning** (`T.one-meaning`) and writes the glossary in STE.
- `shared/glossary-format.md` defines the format of `GLOSSARY.md` for both glossary skills. A scope paragraph names what the glossary covers and exempts. Each group of concepts has a table with the columns Term, Definition, Code, and Source, and a concept with a closed set of values has a value table. One table of vocabulary to avoid and a list of open questions follow. Accepted variants, identifiers, decisions, and the proposed status are cells of a concept row, so the format does not have separate tables for them or a column that lists uses.
- `scan_glossary.py` lists each use of a word that a glossary avoids, with the replacement that its row names, from files or from the output of `scan_repo.py`. It reads the format and older tables headed Avoid, Do not use, Retired, or Draft wording, as well as `Avoid:` lines. A word that several rows list is one avoided word with their replacements joined. `--counts` summarizes the uses by word, with the scope that the glossary states for each word, such as a sense in parentheses. The script does not list a use of a glossary term that contains an avoided word, such as "login name" for the avoided "login". It also skips a `[name]` or `{@link name}` reference in a doc-comment. A word matches only as written when its scope mentions capitals or case, and `--counts` lists the words without a use with zero counts. A quotation inside the parenthetical sense of an older Avoid line is part of the sense, not an avoided word. The glossary format states that a glossary term is never avoided vocabulary. The script therefore names each avoided word that is also a term or a variant of one, leaves it out of the scan, and exits with status 1. `--lint` checks only the glossary. The script matches a word in any part of speech, as its docstring states.

### Changed

- The glossary skills repair a row that lists a term or a variant of one as an avoided word when they write a glossary. A check reports such a row as a finding on the glossary with a suggested revision. The same holds for an avoided word without a sense and for a row that rules out a label of the interface. In a check report, the glossary skills write a proposed definition in full and in the format of the glossary.
- The glossary skills and the three review skills run `scan_glossary.py` when a glossary lists vocabulary to avoid.
- `scan_repo.py` extracts the string literals that look like prose, such as error messages and help texts, with their quote characters. It also extracts the text of user interface templates. It finds the templates in HTML, Vue, and Svelte files, in the JSX of React components, and in the multi-line template literals of JavaScript and TypeScript, such as an inline Angular template. From each template, it extracts the text between the tags, marked as `>text<`, and the values of the attributes that users read, such as `aria-label` and `title`. The script extracts a short string under a key that names text, such as `label: 'Manage users'` or `summary = "..."`, whatever its length. It does the same for the values of JSON translation catalogs in a locale directory and for the name and description of a web app manifest. It reads Gherkin `.feature` files as prose. The script no longer skips a file as generated if its "generated by" comment says that the file was tuned by hand since. It no longer reads a template literal line by line, so it does not treat a `//` or a quoted attribute in the literal as a comment or a string. The script leaves out test files and the strings of CSS and Lisp files, and `--exclude=<glob>` skips the files that match a pattern. `--no-strings` stops the script from extracting strings and template text.
- `/ai-slop:review-repo` reviews the strings that `scan_repo.py` extracts, and in STE mode treats them as literal strings under `T.literals`.
- `/ai-slop:glossary` writes the shared format, takes `--ste`, and points to `/ai-slop:glossary-repo` for a whole repository. An existing glossary keeps its structure unless the user asks for a conversion.
- The README, `AGENTS.md`, and the smoke suite count nine skills and twelve version callsites.

### Fixed

- `scan_sentences.py` reads the cells of Markdown tables and of LaTeX tabular and tabularx environments, which the STE layer covers (`T.scope`, `T.keep-articles`). The scan skipped tables before, so an STE review missed the long sentences and passives in table cells, such as the definitions in a glossary. Each body cell is a paragraph of its own, so a sentence does not continue across cells, and the scan does not compare the rows of a table for uniform runs. The scan skips a Markdown header row and the rule commands of a LaTeX table.

## [2026-11_rev7] - 2026-11-23

### Fixed

- The catalog downloader reports DNS, HTTP, TLS, timeout, and response read errors instead of reporting only "no catalog". It also distinguishes an empty or oversized response from content without a valid catalog. After a failed download, the downloader still exits non-zero with empty stdout, and the explicit `--tropes=<path>` option remains available for offline runs.

## [2026-11_rev6] - 2026-11-04

### Added

- "need not" and "need only" under **Phrases to avoid** (`G.phrases-to-avoid`), with the replacements "does not have to" and "only has to". When a noun phrase after "need not be" stands for a property, the rewrite names the property ("The folder need not be a complete copy of the server." -> "The folder does not have to contain every file on the server."). Where "need not" means "is not necessarily", the replacement is "does not necessarily", or "is not necessarily" for "need not be".

### Changed

- The release sweeps the prose of the bundle for "need not" and "need only".
- Every rule key appears in a self-check item of its layer, except four rules that have nothing to scan for (`G.plain-language`, `G.reformulate`, `T.scope`, `T.precedence`). The general self-check adds items for series and enumerations, bold, and metacommentary. The scientific self-check adds items for numbers in text and research-coded phrases. Existing items take the other rules that lacked one, such as the phrases to avoid under the word-level scan and `G.data-singular` under language conventions.
- `test_every_rule_key_in_a_self_check_item` fails when a rule key is in no self-check item of its layer, as `AGENTS.md` requires.
- The exported rules file leaves out the scientific layer and the catalog ratings, and the release rewrites three passages that pointed to them. **Treat "data" as singular** (`G.data-singular`) gives its reason without "this project". The Economist and STE layers name the layer of each key that they cite from the scientific layer. `G.catalog-precedence` mentions a rating only where the catalog gives one.
- **Verify every entry** (`L.verify-bibtex`) no longer lists the lookups of the reference check. The LaTeX self-check names the reference check of `/ai-slop:review` instead of a script that a project with only a WRITING.md does not contain.
- A WRITING.md has its catalog under "AI writing tropes to avoid", as in the exported rules, and the WRITING.md check matches the heading regardless of case. The paragraph under the heading says that the review skills fetch the live catalog.
- `/ai-slop:review` triggers on a request to check or review a draft, not on a file path alone. Its constraints no longer name narrative structure and readability as points that the rules leave out, since `G.connected-prose` and the Economist layer cover them. The Summary of a report has no sentence limit.
- `/ai-slop:review-diff` and `/ai-slop:review-repo` forbid state-changing git commands instead of any change to the working tree, since writing the report changes the working tree.
- The summary of `/ai-slop:init` has no line limit.
- The release protocol in `AGENTS.md` requires asking the maintainer before the release commit, the tag, and the push. It states its reason instead of using MUST and names the frontmatter key `metadata.version`.
- The README lists the eight commands in a table and states the layer selection and the single source of the catalog once each. It points to `AGENTS.md` for the release protocol.

### Fixed

- Four self-check items of the general layer disagreed with their rules. The closings check allows "In summary" in a summary or conclusion section, and the padding check treats a count of generic or evaluative sentences as a signal. The personification check tests the predicate instead of a list of subjects, and the reference check uses the test of `G.anchor-pronouns`. The coinage check lists "a create".
- **Spell out numbers below ten in running text** (`S.spell-out-below-ten`) exempts ages, scores, and exact sums of money, as **Use numerals for numbers ten and above** (`S.numerals-from-ten`) requires.
- **The body must stand independent of the abstract** (`S.body-independent`) states its exemption once.
- The STE layer cites the current title of `G.no-coinages`.
- **Use one stylistic device per unit, at most** (`T.one-device`) states its own limit on metaphors, since the general layer keeps familiar metaphors.

## [2026-11_rev5] - 2026-11-03

### Added

- **Attach the noun to a sentence-initial quantifier** (`G.bare-quantifiers`) in the general layer. A quantifier used as a pronoun at the start of a sentence ("Neither is a symbolic link") takes its noun ("Neither file is a symbolic link") or joins the sentence that names the noun. The bare form stays after its noun in the same sentence, before an of-phrase that names the set, and where the text names the referents with different nouns.
- **Restate *no* + noun phrase as a negated clause** (`G.no-plus-noun`) in the general layer. The rule covers *no* + adjective + noun ("systems that have no public code"), *no such* + noun, a light verb with *no* + nominalization ("has no effect on"), *there is no* + generic noun, and a trailing *with no*. The fix negates the verb or makes the property the subject ("systems for which the code is not publicly available"). The rule keeps *no* before the absent thing itself, in a quantification over a set, and in an established term.

### Changed

- `scan_reference.py` lists a sentence-initial *Both*, *Neither*, *Either*, *Each*, *None*, *All*, *Some*, *Most*, *Several*, *Many*, or *Few* before a verb as a `bare-quantifier` candidate.
- `/ai-slop:review` applies `G.bare-quantifiers` to the `bare-quantifier` candidates.
- The release sweeps the prose of the bundle for bare sentence-initial quantifiers and for *no* + noun phrase.

## [2026-11_rev4] - 2026-11-03

### Added

- **Unstack noun chains** (`G.noun-stacks`) in the general layer. The rule covers a chain of three or more nouns that the text assembled for the occasion ("absolute dotfile backup path handling"). The fix restates such a chain with a preposition, a verb, or a clause, and a term of the field or of the document stays. A count alone is no finding, since technical prose stacks nouns as terms.

### Changed

- **Keep *that* in formal prose** (`G.keep-that`) also names the clause after an adjective ("confident that the fix holds") and the purpose clause, where a bare "so" is ambiguous between purpose and result.
- **No invented compounds or verbs-as-nouns** is now **No invented compounds or conversions between noun and verb** (`G.no-coinages`). The rule also covers a noun used as a verb where the register has a verb phrase ("calendar the review", "action the feedback"). An established conversion stays (e.g., to email, to log, to mock a dependency).
- The personification part of **Use figurative language with a clear purpose** (`G.no-figurative-language`) names a bodily action, a memory, and a commitment as predicate classes ("the asymmetry bites", "the check forgot", "the docstring promises"). It also limits the metonymy that names a document for its authors to verbs of stating, showing, and requesting.
- The rationale entries for these rules, for `G.possessive-on-things`, and for `E.sentence-flow` cite corpus and training evidence that a length pressure in post-training selects the shorter member of each alternation. The Sources section lists the study.
- The release sweeps the prose of the bundle for noun chains and for purpose clauses with a bare "so".

## [2026-11_rev3] - 2026-11-01

### Changed

- **Caption punctuation** (`L.caption-punctuation`) accepts a `\paragraph{}` caption without a period under a class that appends the period itself. `acmart` renders `\paragraph{Title}` as "Title.", so a review no longer asks for a period that changes nothing on the page. A colon still renders as written. A `\textbf{}` caption still needs its punctuation in the source.

## [2026-11_rev2] - 2026-11-01

### Changed

- When no CrossRef hit matches a title, the reference check removes the hyphens from the title and asks again. Two titles match under either reading of a hyphen. The check no longer reports a false `not-found` or `title-mismatch` when a line break splits a word in a title copied from a PDF ("popu-larity").

## [2026-11_rev1] - 2026-11-01

### Added

- The new `scripts/setup_dblp.py` downloads the monthly DBLP snapshot, verifies its checksum, and builds the database at `$AI_SLOP_DBLP`, else at `~/dblp/dblp.db`.

### Changed

- The reference check reads DBLP from a local database and no longer queries the DBLP web API, which rate-limited a long bibliography. `--dblp` names a database for one run. Without a database, the check prints the setup command and still verifies the DOIs. In that case, it reports an entry as `unchecked` instead of `not-found` when the entry has no DOI and CrossRef does not hold it.
- The CrossRef title search sends the first three author names with the title and asks only for the fields that the comparison reads. A search that returns no result list counts as a failed lookup, not as a missing work. `--mailto` defaults to `$CROSSREF_MAILTO`. The address also goes into the User-Agent, and the reference check warns about a value that is not an email address and drops it.
- The venue comparison expands NeurIPS, ICML, ICLR, ACL, EMNLP, NAACL, KDD, CHI, and CSCW, and reads CoRR as arXiv.

### Fixed

- The reference check resolves a DOI that CrossRef does not hold, such as the DataCite DOIs of arXiv and Zenodo, at doi.org instead of reporting it as `doi-not-found`.
- The reference check spaces its requests to one host and retries an HTTP 429 or 503 after the delay that the server asks for. As a result, a CrossRef rate limit no longer produces `unchecked-offline`. The check allows doi.org 45 seconds, since a DataCite record can take that long, and decompresses a gzipped response.
- `scan_reference.py` lists a sentence-initial This, That, or It before any verb that ends in -s, such as "This produces", not only before the verbs on its lists. It does not treat a word with a noun or adjective ending (i.e., -ss, -us, -is, -os, -as, -ics) as a verb.

## [2026-11] - 2026-11-01

### Added

- `scripts/scan_crossrefs.py`, a cross-reference scan for LaTeX papers. It follows `\input` and `\include` from the root and lists figures and tables that no reference names (`S.refer-to-every-figure`). It also lists a lowercase name before a reference such as "section~\ref" (`S.capitalize-cross-references`), a name before `\autoref` or `\cref`, which print the name themselves, and a typed number such as "Table 2" (both `L.cross-reference-macros`). It skips comments, `\iffalse` blocks, and verbatim and listing environments.

### Changed

- `/ai-slop:review` runs `scan_crossrefs.py` on the root. When a sentence already discusses an unreferenced figure or table, the review suggests adding the reference to that sentence. It lists the other unreferenced figures and tables under author judgment.
- `/ai-slop:review-diff` keeps the `scan_crossrefs.py` rows on changed lines.

## [2026-10_rev12] - 2026-10-29

### Removed

- The command wrappers in `plugins/ai-slop/commands/`. Claude Code now serves each `/ai-slop:` command from its skill and loads the `SKILL.md` directly, with the same commands and arguments.

### Fixed

- `/ai-slop:writing` also adds its reference to an empty `AGENTS.override.md`, which Codex and pi read instead of `AGENTS.md`.
- `/ai-slop:init` also adds its reference to an empty `AGENTS.override.md` in the pi agent directory.
- Init and the README no longer cite the 32 KiB Codex limit for the global instruction file, since it applies only to project files.

## [2026-10_rev11] - 2026-10-29

### Changed

- `lint_markdown.py`, `refresh_vendor.py`, and `_vendor/` come from pymarkdown-skill 0.3.0. It vendors PyMarkdown 0.9.40.

### Fixed

- The README told maintainers to run `refresh_vendor.py` here, which `AGENTS.md` rules out. The README now describes the refresh in pymarkdown-skill and the sync.

## [2026-10_rev10] - 2026-10-29

### Added

- `scripts/build_writing.py` keeps the layers verbatim, self-checks included, and adds the layer name to a repeated heading, as in `## Voice (scientific)`, so the file lints clean. It does not replace an existing `WRITING.md` without `--force`, so the skill still asks first.

### Changed

- `/ai-slop:writing` builds `WRITING.md` with the new `scripts/build_writing.py` instead of having the model copy the rule layers and the trope catalog by hand.
- The version string has eleven callsites. The `WRITING.md` header takes the version from `plugin.json`, as the init export already did.
- `/ai-slop:review` lists a doubt about whether a citation supports a claim under **Items requiring author judgment** instead of recording a finding that revise mode would apply. `/ai-slop:ground` checks such a claim against the retrieved source.
- `/ai-slop:review-repo` runs `scan_reference.py`, as the other two review modes do.

### Fixed

- `/ai-slop:review-diff` reviews untracked files, which `git diff` does not list, such as a new chapter not yet added to git.
- Self-check item 6 of the general layer states the semicolon default of its rule, that is, a period between two independent clauses.
- Three self-check items no longer join clauses with a semicolon.
- `/ai-slop:glossary` no longer calls ripgrep, which is not a listed dependency.
- The rationale names the Economist layer and init mode.

## [2026-10_rev9] - 2026-10-29

### Added

- `--economist` selects an optional layer based on the core advice in Lane Greene's *Writing with Style: The Economist Guide* (2023). It covers reader knowledge, precise words, actors and actions, sentence flow, argument, concision, tone, imagery, and numerical context and precision. The bundle does not include the book or need it at runtime.
- The rules of the Economist layer carry `E.` keys. The layer preserves project and research conventions and combines with `--ste` under the stricter STE limits.

### Changed

- Review, diff, repository, writing, and init modes support the layer, including offline exports with `--tropes=<path>`.

## [2026-10_rev8] - 2026-10-27

### Added

- The repository root is a pi package, so `pi install git:github.com/se-uhd/ai-slop-skill@<tag>` installs the eight skills, which pi invokes as `/skill:<name>`. Its `package.json` lists `plugins/ai-slop/skills` under `pi.skills` and declares no extensions or prompts, which keeps the Claude Code command wrappers out of pi. Claude Code and Codex are unaffected.
- `/ai-slop:init` sets up pi. It writes `ai-slop.md` into the pi agent directory (`PI_CODING_AGENT_DIR` or `~/.pi/agent`). It also appends a read instruction once to the first global context file there (a nonempty `AGENTS.override.md`, then `AGENTS.md`, then `CLAUDE.md`, and otherwise a new `AGENTS.md`). An explicit output path still writes only the file.

### Changed

- Every `SKILL.md` names the pi invocation next to the Claude Code and Codex ones.
- The `WRITING.md` that `/ai-slop:writing` generates names `/skill:review`.
- The README has an "Install in pi" section on pinned and unpinned installs, updates, and name collisions.

### Unchanged

- The versioning stays CalVer. The pi manifest has no version field, since pi pins a git install to a tag, and the version callsites stay at twelve.

## [2026-10_rev7] - 2026-10-26

### Fixed

- Cross-references in the rationale and the STE layer name each rule as the general layer does. Some cross-references had used "No figurative language" for `G.no-figurative-language` or a label of their own, such as "Short paragraphs" for `G.paragraph-length`.
- Self-check item 23 cites `G.one-example-signal` instead of `G.parenthetical-lists`.

## [2026-10_rev6] - 2026-10-26

### Changed

- The general layer is about 6k characters shorter and keeps every rule, key, test, threshold, and exception. Each rule states its test once, keeps fewer examples, and no longer restates a neighboring rule. As a result, the file that `/ai-slop:init` writes takes up less of the 150k characters of instruction files above which Claude Code warns. The self-check and the rationale are unchanged.

## [2026-10_rev5] - 2026-10-23

### Added

- `G.possessive-on-things` flags the possessive 's on a thing or an abstraction ("the sentence's purpose") and prefers an of-phrase, a preposition, or a noun adjunct. The form stays for a person, group, organization, or named tool, for a document standing for its authors, in fixed phrases, and where the possessor is the topic under discussion.
- The smoke suite checks the first-party prose for 's on the text and repository units that the bundle writes about most.

### Changed

- The README, maintainer guide, command and skill files, rule layers, and Python docstrings and comments follow the new rule.

## [2026-10_rev4] - 2026-10-22

### Added

- `/ai-slop:glossary` creates or updates `GLOSSARY.md`, proposes definitions, and flags competing names or inconsistent meanings. It finds the main document when the user does not supply a filename, and `--glossary=<path>` selects another glossary. `--check` validates without updating the glossary.
- `G.connected-prose` requires a clear progression across sentences and paragraphs. Concision and punctuation edits preserve useful transitions.

### Changed

- `review`, `review-diff`, and `review-repo` use project glossaries for terminology checks.
- `G.paragraph-length` treats one- and two-sentence paragraphs as exceptions in sustained prose.

## [2026-10_rev3] - 2026-10-21

### Changed

- The README, maintainer guidance loaded through `CLAUDE.md`, rule rationale, and ignore rules describe the seven remaining modes and eleven version callsites.

### Removed

- `/ai-slop:tldr` and its command, skill, counting helper, schema check, recall helper, and synthetic fixtures. Use `/ai-slop:review` for a document, `/ai-slop:review-diff` for changed lines, or `/ai-slop:review-repo` for a repository.

## [2026-10_rev2] - 2026-10-08

### Added

- `G.context-first` requires a reason for stylistic edits based on the surrounding passage, so word matches, trope statuses, and counts prompt inspection rather than automatic replacements. Edits preserve purpose, logical relations, distinctions, scope, emphasis, evidence, and author voice.

### Changed

- The general rules and self-checks keep useful abstractions, familiar metaphors, clear references, and natural sentence rhythm. Explicit conventions such as spelling, terminology, citations, and statistical reporting still apply.
- Review, diff, repository, and TL;DR workflows require a problem in context before reporting a stylistic finding.
- Review findings include a reason for the proposed replacement.
- Revise mode checks that a suggestion preserves the argument as well as the facts. It skips a suggestion that loses meaning unless the user explicitly approved that change.

## [2026-10_rev1] - 2026-10-02

### Changed

- `G.plain-words` treats a vague "checkpoint" as it treats a vague "gate": Name the build, test, or command that must pass and, when it matters, before which action. The word stays for a saved state that a process resumes from, such as a model or database checkpoint.

## [2026-10] - 2026-10-01

### Changed

- `G.plain-words` adds examples that replace a vague "gate" with wording that fits the context and names what must pass and, when it matters, before which action. Established technical senses stay.

## [2026-09_rev37] - 2026-09-30

### Changed

- `G.be-concrete` flags vague uses of "moved" and "shifted" in descriptions of a revision. State the actual change or current behavior. Give version history only when it helps the reader compare versions, upgrade, reproduce a result, or understand a change. Actual relocation, physical movement, and established technical senses stay.

## [2026-09_rev36] - 2026-09-30

### Added

- `/ai-slop:init` sets up Codex. It exports its rules to the Codex home directory and adds a reference in the effective global instruction file. For Claude Code, the default output stays in the rules directory, and explicit export paths still write only the requested file.

### Changed

- All eight skills resolve bundled helpers from their installed `SKILL.md` location in both Codex and Claude Code, without a Claude-specific environment variable. Claude slash commands and plugin manifests remain compatible.
- The README documents Codex installation and invocation.
- `/ai-slop:writing` references `WRITING.md` from `AGENTS.md`, keeps Claude Code loading through a `CLAUDE.md` import, and preserves existing instructions and references.

## [2026-09_rev35] - 2026-09-27

### Changed

- The file that `/ai-slop:init` writes is about 15k characters smaller (69k instead of 84k with the current catalog). It leaves out the self-check of each layer. Its opening paragraph asks for the check instead. The file also drops the status and category line of each catalog entry, its `**Avoid patterns like:**` label, and the `---` line after it. The layer files keep their self-checks for the review modes.
- The details that only a self-check item stated are now in their rules, so the exported file loses no test. `G.american-english` names favor, center, defense, and license, and `G.restricted-words` gains the limit of 2 to 3 per paragraph. `G.em-dashes` excludes en dashes in ranges, minus signs, and `--` in code listings from the count. `G.em-dash-glyphs` names `---` for LaTeX and keeps an em-dash glyph in a quotation or code listing. `G.parenthetical-lists` defaults to "e.g.," for a list that is not obviously exhaustive, and `G.plain-language` asks for a scan for the sample words. In the STE layer, `T.one-topic` gains the test of naming the topic of a paragraph, and `T.verbs-not-nouns` names the light verb form.
- Self-check item 14 drops the "(verb)" note on "licence".

## [2026-09_rev34] - 2026-09-27

### Changed

- `/ai-slop:export` is now `/ai-slop:init`. The new init replaces a rules file from `/ai-slop:export` without `--force`.
- The former `/ai-slop:init`, which writes the `WRITING.md` of a project, is now `/ai-slop:writing`.
- `G.plain-words` lists "cut" for creating or publishing, as in "cut a release" -> "publish a release", and keeps it for removing or shortening.
- `CLAUDE.md` and the README no longer use "cut" in that sense.
- The seed test fails on "re-cut" and on "cut" before a release, tag, branch, or reference.

## [2026-09_rev33] - 2026-09-27

### Added

- A genre step, in which the skill determines before the review which catalog patterns are normal in the kind of text, such as numbered concerns in a peer review. It records no finding for them and lists them in the report and the TL;DR.
- Instructions for `/ai-slop:tldr`, given as text after the path. They can narrow the review, exempt or add a pattern, and give context for the genre step, but they cannot change a count. The report states how the review applied each instruction.
- Tests for borderline matches of tropes such as Negative parallelism and Preamble.
- A unit for each finding. A passage with two tropes is one finding, and one term under several names is one finding that quotes the names. Em-dashes count only above three per 350 words.
- `count_findings.py` takes `--scope=<path>:<ranges>`, which limits the word count to the lines that the review covered.

### Changed

- `/ai-slop:tldr` checks a text against the tropes.fyi catalog only. The layer rules no longer produce findings but still supply their exceptions, so `/ai-slop:tldr` does not flag a single "robust" or "we" in a paper. `--ste` no longer applies to this mode.
- The TL;DR no longer rates a text. The `**AI use:**` verdict, the five-level impact rating, the share of the prose that needs a rewrite, and the written assessment are gone. Each block gives the number of patterns that affect readability and the word count, as in "3 in 850 words". It also gives up to five bullets under "Patterns that affect readability". Minor patterns, such as formatting or a reused word, stay in the report but do not count. The TL;DR only lists a file with fewer than two other patterns.
- `count_findings.py` writes each bullet with a fixed label, a count, and a quote.
- The review skips quotations, text that the writer restates from the work under discussion, form text, and curly quotes.
- The review tests every paragraph against every catalog entry, one file at a time. For a directory, a last pass aligns the decisions on each trope across files.
- `count_findings.py` gives the number of patterns per file and whether the file needs feedback.
- `count_findings.py` ranks the rules by cost, with the minor rules last and `new` and `rising` tropes first on ties.
- `count_findings.py` counts character and formatting tropes once per line.

### Fixed

- `count_findings.py` counted LaTeX `%` comments as prose.
- `count_findings.py` missed catalog names in quotation marks such as `"Delve" and friends`.
- `count_findings.py` split "Preamble (announce-then-answer)" into two rules.

## [2026-09_rev32] - 2026-09-27

### Changed

- `G.plain-words` lists "shape" as a word to replace, with structure, format, or pattern for the noun and structure or influence for the verb. It keeps "shape" for geometry, statistical distributions, and array dimensions.
- The bundle no longer uses "shape" outside quoted examples and old commit messages.
- The lint check `tldr-block-shape` is now `tldr-block-format`.
- `check_baseline.py` comes from pymarkdown-skill 0.2.7.
- The seed test now fails on "shape".
- 21 rules in the general, scientific, and STE layers give their examples as "phrase" -> "rewrite" pairs. Some of these rules had given only the replacement word or no rewrite.

## [2026-09_rev31] - 2026-09-24

### Changed

- Thresholds that only the self-check of the general layer stated are now also in their rules. The thresholds per paragraph are more than one-third passive sentences (`G.active-voice`) and more than two hedges (`G.hedge-from-evidence`). The other thresholds are three consecutive sentences within 5 words of each other in length (`G.sentence-length`) and around 5 pause marks per page-equivalent (`G.pause-mark-count`). The thresholds and self-check items are unchanged.

## [2026-09_rev30] - 2026-09-24

### Added

- An export mode, `/ai-slop:export`, which writes the general layer and the AI trope catalog into one Markdown file. The file contains an instruction to apply the rules to all prose that Claude writes or changes, with the writing conventions of a project taking precedence. The default output, `~/.claude/rules/ai-slop.md`, loads in every Claude Code session and project without an import. A path under `.claude/rules/` in a repository loads in that project only, and any other path writes the file for another use. `--ste` adds the STE layer. The scientific and LaTeX layers stay out, and `/ai-slop:init` still writes them into `WRITING.md`.
- `export_rules.py`, which assembles and writes the file, with each layer under its own heading and without the title and preamble of the catalog. The script reports the approximate size in tokens on stderr. Running the mode again replaces an earlier export, which a sentence in its header identifies as generated by the mode. The skill asks before replacing any other file.

### Changed

- The version string has twelve callsites, with one in the new `SKILL.md`.

## [2026-09_rev29] - 2026-09-24

### Added

- `scan_repeats.py`, a candidate scan for **Refer back instead of repeating** (`G.refer-back`). It lists every sentence that repeats an earlier sentence of the same file. The repeat is a verbatim copy, a copy with a changed ending (a shared sequence of six words), or a short sentence pasted twice. The scan does not list a sentence that recurs three or more times, such as a form label.

### Changed

- `/ai-slop:review`, `/ai-slop:review-diff`, and `/ai-slop:review-repo` test each row of `scan_repeats.py` against `G.refer-back`, so a second copy is a finding and a brief reminder stays.
- Catalog tropes with the status `fading` are weak evidence for the AI-use verdict of the TL;DR. A sign of unassisted writing in the same paragraph discounts them, as it discounts figurative phrasing and padding.

### Fixed

- `count_findings.py` no longer reads the word that joins two rules in a Rule field, such as "matching", as part of the trope name.
- The TL;DR fixtures plant the rules that the layers assign.
- `check_fixture_recall.py` counts a rule and a catalog trope that name the same pattern, such as `G.refer-back` and "Self-echo", as one.

## [2026-09_rev28] - 2026-09-24

### Added

- A TL;DR mode, `/ai-slop:tldr`, which runs `/ai-slop:review` on a document or `/ai-slop:review-repo` on a directory, with the same flags, and condenses the report into `ai-slop-tldr.md`. Each file with findings gets a self-contained block with the impact level, a fixed AI-use verdict, an assessment of one to five sentences, and up to three bullets under a fixed line. Each bullet names one of the worst patterns, with its count and a short quote. The TL;DR lists files without findings together, commit messages get one block, and `/ai-slop:revise` still applies the full report.
- The impact scale. A finding obscures the meaning (e.g., an unclear referent), delays the content (e.g., padding), or only distracts (e.g., punctuation). A paragraph needs a rewrite when at least two of its findings obscure or delay, and at least one per 100 words. The level is the share of the prose in such paragraphs: None when no finding obscures or delays, Minor under a tenth, Moderate under a third, Major under two thirds, and Severe above. Major and Severe also need at least three such paragraphs.
- The AI-use verdict, which `count_findings.py` computes from the AI-typical findings, i.e., the catalog tropes and the rules for patterns that AI output overproduces, without grammar slips, dropped words, spelling, unclear pronouns, or curly quotes. The verdict is Little sign of AI tools with fewer than two such findings or fewer than one per page-equivalent. It is Harder to read when the level is Moderate or above and one of these findings is in a paragraph that needs a rewrite. Otherwise, it is Reasonable.
- Counter-evidence for the verdict. The report gains a `## Signs of unassisted writing` section with the typos, grammar slips, missing articles, and missing words of each file. Non-native and hurried writers produce some patterns as readily as models do. These patterns, such as figurative phrasing and hedges, stop counting as AI evidence in a paragraph with a sign of unassisted writing. The reply lists files where the text contradicts the verdict under `Verdicts to check:`.
- Nine synthetic reviews under `scripts/tests/fixtures/tldr/`, each with planted findings and the level and verdict that it must get.
- A new script, `scripts/tests/check_fixture_recall.py`, compares a real review of a fixture with its planted findings.
- `count_findings.py`, which computes everything in a TL;DR that a count can settle, so that two runs over the same report agree. It counts findings per file and rule and ranks the rules of each file by a count weighted 4 for obscures, 3 for delays, and 1 for distracts. It also gives the paragraphs that need a rewrite and the level and verdict of each file. A finding counts once for each rule that it cites, and the script warns when a finding has no rule.
- A `tldr-block-shape` check in `schema_checks.py`, which the linter runs on `ai-slop-tldr.md`. It flags a block without an impact level from the scale, an AI-use verdict, or an assessment. It also flags a block with an assessment of more than five sentences, with more than three bullets, or with bullets that lack the fixed line before them.

### Changed

- `scan_repo.py` now skips `fixtures` and `testdata` directories.
- The version string has eleven callsites, with one in the new `SKILL.md`.
- `ai-slop-tldr.md` joins the generated artifacts that are never committed.

## [2026-09_rev27] - 2026-09-22

### Changed

- The personification clause of **No figurative language** (`G.no-figurative-language`) covers any subject that is not a person or a group, where it had named code, models, tests, and data. A desire, feeling, belief, duty, or merit given to a document, a tool, or an abstract noun is a finding ("a period does the job"). The fix names the mechanism or observable behavior. Verbs that name a defined behavior ("a parser expects a token") and author metonymy ("the paper argues") stay literal.

### Fixed

- One personification in the revise skill, which now applies the suggested revisions of a report as written where it had said that it "trusts" them.

## [2026-09_rev26] - 2026-09-22

### Changed

- **Be concrete** (`G.be-concrete`) becomes a rule on empty head nouns, such as thing, aspect, or item, and the quantifiers before them, such as "various". The test is to write the specific noun in the slot. Where the text cannot supply it, the finding goes to author judgment with the candidate readings instead of a guessed noun. A generic noun stays where the generality is the claim, and no density threshold applies.

### Fixed

- Empty nouns in the prose of the bundle, such as "the same thing", which became "the same construction".

## [2026-09_rev25] - 2026-09-22

### Changed

- The release protocol in `CLAUDE.md` opens with a rule on when to publish a rev. The maintainer publishes a rev after checking the settled work against the main use of the bundle and the existing rule layers, not at the first version that passes the smoke suite. The maintainer squashes a correction from the same session into that rev. Rule 3 governs once the session has ended or anyone may have pulled the tag. The release renumbers the other rules.

## [2026-09_rev24] - 2026-09-22

### Added

- **Consequence connectives** (`G.consequence-connectives`) in the general layer. AI text marks nearly every consequence with one word, "so" in general prose and "therefore" or "thus" in academic prose. The rule tests whichever word a document uses most.
- An order of fixes for the rule: delete a connective that the order of the content already implies, then recast with because or since, and substitute another connective last. The substitute counts toward the two-per-paragraph limit on transition words. The rule calls for deleting a sentence-initial "So" in formal prose and recommends "therefore" and "thus" mid-sentence ("The counts are therefore unreliable").
- A count over the family of connectives. More than two or three per page-equivalent (~350 words) flags a text, and the concentration on one word counts only at or above that density. Parallelism across items of the same kind, the intensifier, "so that", the correlative, and quoted material are out of scope.

### Changed

- The transition-word note in the restricted-words section points to the new rule.

### Fixed

- The README, `fetch_tropes.py`, `find_citation_issues.py`, and `rules-rationale.md` follow the new rule. The exit-code listings in the ground and revise skills keep their connectives under the parallelism exception.

## [2026-09_rev23] - 2026-09-15

### Changed

- The bundle applies the findings of an `/ai-slop:review-repo` run over its own repository. Most of the findings concern dropped *that*, semicolons or colons used as pauses, parenthetical lists without "e.g.,", invented compounds, and colorful words. The fixes cover the README, `CLAUDE.md`, released entries of this changelog, the commands, rule layers, rationale, skills, and script docstrings and comments. No script code changed.
- The rule layers settle the questions for author judgment from that review. Noun stacks such as "AI trope catalog" lose their hyphens (`G.compound-hyphens`), and the nouns "cite" and "fetch" become "citation" and plain phrases (`G.no-coinages`). "Em-dash" has one spelling, the headings of the rule layers use sentence case, and the skills no longer bold words for emphasis.
- **Em dashes are unspaced** is now **Em-dashes are unspaced**, with its key unchanged.
- **Keep metacommentary in comment-commands** is now **Keep metacommentary in comment macros**, with its key unchanged.
- The upstream-owned `lint_markdown.py`, `check_baseline.py`, and `refresh_vendor.py` come from pymarkdown-skill 0.2.6, which applies the review findings for those files.
- The commit history. The review checked 85 commit messages, and the release rewrote 44 of them to follow the general layer, under the history repair that `CLAUDE.md` describes. Every tag moved with its commit, and every tree is unchanged.

### Removed

- The rationale entries for `G.such-as` and for the concision rules, which gave no reason.

### Fixed

- The README no longer says that the directory denylist applies only outside a git repository.
- The em-dash rule no longer offers parentheses as a replacement, which the same rule forbids.

## [2026-09_rev22] - 2026-09-15

### Fixed

- Prose that the rev21 sweep missed, such as "doing a dash's work", semicolons joining independent clauses, lowercase sentences after a colon, "sits" or "lies" for where something is (`G.plain-words`), and an "orchestration" banner in `verify_references.py`. The fixes cover the script docstrings and comments, `CLAUDE.md`, the README, the review-diff skill, and the restricted-words table.

## [2026-09_rev21] - 2026-09-15

### Changed

- The prose of the bundle follows its rules again. The release fixes semicolons joining independent clauses, lowercase sentences after a colon, dropped *that*, stand-in words, figurative wording such as "escape hatch", and a negative-parallelism sentence in the ground skill.

### Fixed

- README, `CLAUDE.md`, and manifest statements that no longer matched the bundle. Some statements concerned the three helpers that reach the network (`check_quotes.py` included), the report schema that all three review modes share, and the ten version callsites. Other statements concerned the glyph and reference scans, `--ste`, the author of the trope catalog, and the three places of a rule change.
- Skill steps that contradicted the scripts. A trope finding carries the catalog status. The revise skill puts a `% GROUNDING: TODO verify` stub on its own line below the citation, since a stub inside the line comments out the rest of it. The review skill says that only the ASCII dash pass skips fences and `%` comments. Review-diff reads a `passive` or `nominalization` row at the matched words, and review-repo applies the directory denylist inside a git repository too. Init prints two summary lines and lists every script that it runs, and ground shows the `source` field of a downgraded quote.
- Script docstrings and comments that misdescribed their code. One of them described a `scan_repo.py` limitation about a second comment on one line, which the extractor does read. Another misdescribed the `unchecked-offline` verdict of `verify_references.py`, which an HTTP error also produces.
- Drift inside the rule layers. The self-check and rationale for `G.paragraph-padding` count aphorisms, as the rule does. Cross-references use the rule names that their keys define. The rationale no longer says that the layers carry only additions to the catalog or that the skills load the catalog by path.
- The blank line between steps 1 and 2 of `revise/SKILL.md`, which rev20 removed.

## [2026-09_rev20] - 2026-09-15

### Changed

- Sentence length in STE mode has a tolerance band instead of a hard 25-word cutoff. Up to 25 words is the target. A sentence of 26 to 35 words stays when it has one main idea and the reader does not have to hold several clauses before its point. The rule says to split a longer sentence. `scan_sentences.py` still lists every sentence over 25 words.
- `T.precedence` no longer overrides `G.sentence-length` on length.
- The rule stays as `T.keep-original` (formerly `T.keep-and-mark`). A sentence that an STE rewrite would weaken keeps its original form, and a review lists it under **Items requiring author judgment** with the reason.

### Removed

- The `[KEPT: reason]` marker, the **Kept sentences** report section, the revise step that inserted the marker, and the scanner code that skipped marked sentences.

## [2026-09_rev19] - 2026-09-15

### Added

- An STE mode. `--ste` loads `shared/rules-ste.md` on top of the layers that the scope selects, in `/ai-slop:review`, `/ai-slop:review-diff`, `/ai-slop:review-repo`, and `/ai-slop:init`. The layer adapts part of ASD-STE100 Simplified Technical English, such as short sentences, active voice, one topic per paragraph, and verbs instead of nominalizations. It departs from STE with sentence length that varies within a 25-word limit and with at most one stylistic device per reply, headed section, or text without headings. Quotations and literal strings stay as written, and the rules carry `T.` keys.
- The `[KEPT: reason]` marker (`T.keep-and-mark`) for a sentence that an STE rewrite would weaken. A review lists such a sentence under a new **Kept sentences** report section. `/ai-slop:revise` inserts the marker inside a comment in LaTeX and Markdown, and a later STE review skips a marked sentence.
- `scan_sentences.py`, which lists the STE candidates in a Markdown, plain-text, or LaTeX file. The candidates are sentences over 25 words, sequences of three or more sentences within 5 words of each other in length, passive verbs, and a light verb followed by an action noun.

### Changed

- The review skills run `scan_sentences.py` in STE mode.

### Fixed

- The Bundled files list of `/ai-slop:review-repo` names `scan_glyphs.py`, which its metrics step already ran.

### Unchanged

- The prose of the bundle, since the STE layer is opt-in and needs no sweep.

## [2026-09_rev18] - 2026-09-09

### Removed

- The semicolon ratchet test added in rev17, which could not tell a list separator from a clause joiner. The release leaves clause-joining semicolons to the `/ai-slop:review-repo` sweep, and the "lives in" test stays.

## [2026-09_rev17] - 2026-09-09

### Added

- `check_quotes.py`, which re-reads the `source` (URL or local path) that each grounding agent now returns. It confirms that the quote occurs in the source after normalization and downgrades a quote that it cannot find to `TODO verify -- unverified`. A PDF or an unreachable source goes back to the skill to check by hand.
- Two smoke tests check the prose between sweeps, one counting prose semicolons in the first-party Markdown and one failing on "lives in".

### Changed

- The ground skill states that the agents send claim sentences to search engines.
- `/ai-slop:review-diff` decides the rule layers per changed file and diffs `.tex`, `.md`, and `.txt` together. As a result, it still reviews the Markdown changes of a code repository with a paper in a subdirectory. Its metrics also run `scan_glyphs.py` and `scan_reference.py`.
- `/ai-slop:init` takes `--general` to force the general layer for a code repository with a paper in a subdirectory.
- `/ai-slop:revise` accepts the Markdown or plain-text document that a review names in its `**Paper:**` header, where it had stopped without a LaTeX root. It applies a repo-mode report one file at a time, from the blocks under the `### <relpath>` heading of each file.
- The review, review-diff, review-repo, and ground skills resolve the repository root with `git rev-parse --show-toplevel` before appending to `.gitignore`.
- The dash heading of the report template names both dash kinds.
- The general layer describes the v2 catalog. `G.catalog-precedence` names the entries that it overrides (i.e., "Delve" and friends, Signposted conclusion, Rule of Three pattern, and Bold-first bullets) instead of a banned-word list. Self-check item 1 scans for the word-level entries of the catalog.
- `S.we` gains the single-author case.
- `L.editorial-comments` no longer names the author macros of one project.
- The init skill and its `WRITING.md` template, `verify_references.py`, the README, the review and review-diff skills, and the rationale no longer describe the snapshot fallback, fetch chain, or plural sources that rev16 removed.
- The prose of the bundle follows its rules again. The release fixes semicolons joining independent clauses, "lives in", lowercase sentences after a colon, announced counts, and the claim that pushed history is immutable, which rev15 disproved.

### Fixed

- `scan_repo.py` no longer drops a prose file that merely mentions "generated by" or "do not edit". A file counts as generated only when the marker is on a comment line within its first ten lines, or is the `@generated` tag or the uppercase `DO NOT EDIT` banner. The script names every skipped file on stderr.
- The `WRITING.md` structure check in `schema_checks.py` accepts the H1 "Writing rules for this project" that init writes, besides "Writing rules for this paper", so its findings fire on a real file.
- `fetch_tropes.py` accepts only a body with a Markdown H1 and at least five `##` trope headings, so an error body or error page no longer passes as the catalog. It decodes a base64 data URI and rejects a body over two megabytes. It also prints to stderr the size, heading count, and content hash of the accepted body.
- `scan_glyphs.py` no longer counts dashes in `%` comments of a `.tex` file, such as the ` -- ` separator of `% GROUNDING:` comments, toward the dash density. Sequences of four or more dashes no longer count toward the density either. Its fence tracking, which it shares with `scan_reference.py`, honors nesting.
- `verify_references.py` flagged correct entries. A year now matches any year that CrossRef (online-first or print) or DBLP records for the work. DOI entries merge in the DBLP record as `L.source-priority` says. To compare venues, the script expands common SE abbreviations (e.g., TOSEM, EMSE, ICSE) and matches database abbreviations such as "Empir. Softw. Eng." by word prefix.
- `find_citation_issues.py` follows `\input` / `\include` and finds a `\cite` with a key list that spans lines, so the grounding to-do of the review and the site list of ground contain the same calls.
- `insert_grounding.py` places the comment after the line where a multi-line call ends.
- `find_latex_root.py` no longer treats the chapters of a `subfiles` project as roots.
- `scan_repo.py` rejects a `--commits` value that starts with a dash. Git had read such a value as an option. When git cannot resolve a range, the script exits 2 with git's message instead of reporting zero commits. It also skips YAML front matter, indented code blocks, dependency pins such as `requirements.txt`, and license texts.
- `bib_parse.py` reads a backslash-escaped quote inside a quoted value, joins `#` concatenations, and resolves TeX accents (e.g., `{\"u}`, `\c{c}`, `\ss`) to Unicode.

## [2026-09_rev16] - 2026-09-09

### Changed

- `fetch_tropes.py` reads only tropes.fyi and exits 1 when the site is unreachable, and the four skills that load the catalog stop and say so. `--tropes=<path>` remains the way to review offline or against a pinned catalog.
- `scan_glyphs.py` counts the dash rather than the character. A new `ascii-dash` category matches `--` and `---` used as a dash, but not a command-line flag, numeric range, table separator, fenced block, or inline code span.
- The density metric of the review adds `ascii-dash` to `em-dash`, so a LaTeX em-dash written as `---` now counts.
- The review uses the status tags of the catalog. A trope finding names the status, as in `Negative parallelism (tropes.fyi, consistent)`. The review reports every `new` and `rising` match and confirms a `fading` match against the passage first. A rule layer still outranks the catalog wherever they disagree.

### Removed

- The gist mirror and the bundled snapshot, with `refresh_tropes.py`, `shared/tropes-snapshot.md`, the attribution sidecar, and the snapshot-refresh step of the release protocol.

## [2026-09_rev15] - 2026-09-09

### Changed

- The release rewrote every commit message in the history to follow the general layer, and all 59 release tags moved with their commits, with byte-identical trees. Semicolons became periods between independent clauses and commas between two actions in a subject line, and em-dash glyphs became periods or commas. Semicolons in lists, quoted output, or code spans stay, as do the two glyphs quoted as examples. The pass also fixed a British spelling, a comma splice, and an inhabitance framing.
- The release protocol allows a maintainer-requested history repair as the exception to its rule against rewriting a released commit. The repair moves every tag with `--tag-name-filter`, verifies the trees against `refs/original`, and force-pushes `main` and the tags together. The commit-message convention no longer claims that a pushed message cannot be corrected.

## [2026-09_rev14] - 2026-09-09

### Added

- A commit-message convention in `CLAUDE.md`, which puts the check of a message before `git commit`. The convention names the recurring failures: a semicolon joining two independent clauses, a literal em-dash glyph, and counts announced in front of continuous prose. The release suffix of the subject line stays as the one semicolon that the convention keeps.

### Unchanged

- The messages already pushed, since rule 2 of the release protocol forbids rewriting a released commit.

## [2026-09_rev13] - 2026-09-09

### Added

- `CLAUDE.md` records that changing a rule means editing the layer, its self-check item, and `rules-rationale.md`.
- `CLAUDE.md` also records that adding or tightening a rule means sweeping the prose of the bundle for the pattern in the same rev.

### Changed

- README semicolons that joined two independent clauses became sentences, per `G.semicolons`. Semicolons inside a parenthetical and those separating items in the review-repo language list stay.
- The step of the release protocol that refreshes the snapshot names its source order.

### Fixed

- The `2026-09_rev11` and `2026-09_rev12` entries below record what those releases changed and no longer break rules that the bundle enforces, such as `G.no-list-cramming`, `G.parenthetical-lists`, and `G.short-enumerations`.
- The README no longer calls the bundled snapshot a copy of the gist. Its Acknowledgements and License sections name the tropes.fyi page as the source since rev11.

## [2026-09_rev12] - 2026-09-09

### Added

- **Announce a count only when the reader tracks it** (`G.no-announced-counts`), from the Compulsive counting and Preamble entries of the v2 catalog. A count stays where the reader checks items against it, such as a checklist or the research questions of a study. The writer deletes a count before continuous prose. The test is whether a later sentence refers back to the number.
- **No enumerated list disguised as paragraphs** (`G.no-prose-listicle`), from the Excessive enumeration entry. Ordinals inside one paragraph are structure, and the same markers opening consecutive paragraphs are an unmarked list.
- A **Phrases to Avoid** entry for **"famously" / "notoriously" / "as is well known" / "a classic"**, from the Appeal to familiarity entry.
- Self-check items 26 and 27 for the two new rules and the new patterns in items 9, 13, and 21.
- `rules-rationale.md` entries for the two new rules and the clarification of `G.em-dash-glyphs`.

### Changed

- Rules in the general layer that partly covered a v2 entry now cover it. `G.no-formulaic-openings` covers the announce-then-answer opener, and `G.no-metacommentary` a sentence that narrates the reasoning behind the writing. `G.no-coinages` covers an abstract label of a domain word plus a problem-noun ("supervision paradox"), and `G.plain-words` covers "lives" for where something is defined. `G.paragraph-length` covers a bare fragment set as its own paragraph, `G.paragraph-padding` an aphorism written to be quoted, and `G.no-excess-bold` the bold-first bullet. `G.em-dash-glyphs` states that rewriting the glyph as `--` leaves the dash in place.
- `S.cite-specific-works` requires a quantity word to match the citations behind it, so "several studies" in front of two references is inflation.
- The prose of the bundle no longer frames a file or module as a place where something lives ("the skill's workflow lives in ..." became "is in ...").

## [2026-09_rev11] - 2026-09-09

### Changed

- The trope catalog comes from tropes.fyi first and the upstream gist second, since only the site carries the v2 catalog.
- The release refreshes the bundled snapshot to v2. The v2 catalog has 49 tropes instead of 37, each tagged with a category and one of the statuses new, rising, consistent, and fading. About twenty entries are new, such as Reasoning leak, Premise stacking, Compulsive counting, and Synonym cycling.
- `/ai-slop:init` inserts a blank line between each `**Avoid patterns like:**` line and the bullet list under it when it inlines the catalog. As a result, the lint loop no longer has to repair those lists in `WRITING.md`.
- The examples in the normalization step of `/ai-slop:init` follow the v2 headings.
- The release documents the source order in the README, the four skill files that load the catalog, the two command files, and `tropes-snapshot.ATTRIBUTION.md`. The attribution file names the site as the source of the snapshot and the gist as an earlier mirror.

### Fixed

- The site step of the fetch chain could hand a rendered HTML page to the review skills in place of the catalog. `fetch_tropes.py` now sends a user agent and unwraps the Markdown from the `data:text/markdown` URI of the download link or the `<pre>` block. A page that yields neither falls through to the next source.

## [2026-09_rev10] - 2026-09-05

### Added

- A **Phrases to Avoid** entry in the general layer against **"arm"**. The entry recommends "condition" or "treatment" for an experimental manipulation, "group" for a set of subjects, "variant" or "configuration" for a version of a prompt, model, or pipeline, and "split" for a data partition. "Arm" stays for a randomized trial group or a bandit option.

## [2026-09_rev9] - 2026-09-03

### Added

- **Rewrite *whose* clauses on things** (`G.whose-on-things`) in the general layer. A restrictive *whose* clause on a thing ("entries whose keys appear in the new citations") becomes *with*, a participle or verb on the head, or the property as the subject of its own clause. *Whose* stays for a person or group and where every restatement is longer or repeats the head noun. More than one *whose* clause on things per page-equivalent is a secondary signal.

### Changed

- The rule layers, skill files, README, this changelog, and Python docstrings and comments follow the new rule, except the upstream-owned `lint_markdown.py`.
- `review/SKILL.md` replaces the coinages "post-colon clause" and "post-colon text" with "the clause after it" and "the text after it".

## [2026-09_rev8] - 2026-09-01

### Changed

- `scan_repo.py` reviews the contents of a fence with a prose info string (i.e., `markdown`, `md`, `mdx`, `text`, `txt`, `plain`), such as the templates quoted in the skill files. Fences nest: A bare code fence inside a prose fence stays skipped. A fence closes only on a bare marker of its character with at least its length.

### Fixed

- The review-repo section of the README has its full language list again instead of the pointer to the `COMMENT_SPECS`/`NAME_SPECS` tables that the 2026-09_rev4 sweep left.
- The intro of the general layer no longer stacks "the contested rules, the rules that a reader might push back on" or joins its clauses with semicolons.

## [2026-09_rev7] - 2026-09-01

### Fixed

- Prose inside the fenced templates, which the repository scan skips as code. The disclaimer of every generated report no longer joins two clauses with a semicolon, and its Summary placeholder no longer asks for "headline metrics". The `WRITING.md` header and the two maintainer comments read the same way.
- The 2026-06_rev13 entry below has the language list again that the 2026-09_rev4 sweep had shortened.

## [2026-09_rev6] - 2026-09-01

### Fixed

- `CLAUDE.md` and the README name all five upstream-owned paths (i.e., `lint_markdown.py`, `check_baseline.py`, `refresh_vendor.py`, `_vendor/`, `bundled_licenses/`), where they had named only the first two. The `sync/sync_to_skill.sh` script of pymarkdown-skill copies them in and stamps the version in `scripts/.pymarkdown-skill-version`.

## [2026-09_rev5] - 2026-09-01

### Changed

- Synced the pymarkdown-skill helpers at upstream release 0.2.4, which carries the em-dash and wording fixes that the 2026-09_rev4 sweep had applied to `lint_markdown.py` and `refresh_vendor.py` here. No behavior change.

## [2026-09_rev4] - 2026-09-01

### Added

- **Participial openings** (`G.participial-openings`) as a rule in the general layer, where it had been only a self-check item.

### Changed

- Every rule in the three layers carries a stable key after its name (e.g., `G.semicolons`, `S.significant`, `L.grounding-comments`). Cross-references in the layers, rationale, and self-check items cite these keys, so a rename or an insertion no longer breaks a reference.
- The `Rule:` field of a report carries the name followed by the key, as in `Semicolons (G.semicolons)`.
- Rule names are plain directives without punctuation or metaphor. Renamed: "Name the relation with a connective; don't just drop the pause" to **Name the relation with a connective**; "Cite, do not gesture" to **Cite specific works**; "Name the thing instead of pointing at it" to **No stand-in words**; "Anchor every sentence-initial *This*, *These*, *That*, or *It* to a noun" to **Anchor sentence-initial pronouns**; "Use *the* only for a referent the reader can already identify" to **Definite article only for known referents**; "Watch the combined load" to **Combined pause-mark count**; "Hedge from evidence, not from timidity" to **Hedge only from evidence**; "Introducer punctuation: `:` not `.` before a list or continuation" to **Colon before a list or continuation**; "Pick one example-list signal and stay with it" to **One example signal per document**; "Signal whether a parenthetical list is examples or exhaustive" to **Mark parenthetical lists as examples or exhaustive**; "Avoid redundant content; refer back instead" to **Refer back instead of repeating**; the LaTeX caption rule to **Caption punctuation**; the "significant" rule to **Reserve "significant" for statistics**; and the paper-versus-study tense rule to **Present tense for the paper, past tense for the study**.
- The prose of the bundle follows its rules. A `/ai-slop:review-repo` sweep fixed findings such as em-dash glyphs, semicolons joining independent clauses, and dropped *that*. The fixes are in the rule layers, skill and command files, README, `CLAUDE.md`, this changelog, docstrings and comments, manifest descriptions, and H1 titles. The `"before" -> "after"` notation uses an ASCII arrow. The release fixed `lint_markdown.py` here and synced the fix back to pymarkdown-skill.

### Fixed

- `init/SKILL.md` step 3 points to step 9 for the summary, not step 7.

## [2026-09_rev3] - 2026-09-01

### Added

- A density signal in the same rule for generic-truth sentences, true of any document on the subject, and evaluative sentences, which grade the preceding claim without adding to it. One such sentence can open a section or mark that a result matters. More than one such sentence per paragraph, or more than two or three per page-equivalent, is filler.

### Changed

- **Cut padding at the paragraph level** (`G.paragraph-padding`) defines windup as a sentence that announces what its own paragraph then does. A paragraph that opens a section is legitimate when it states the claim or purpose of the section or orients the reader across the subsections beyond the headings. Such a paragraph is windup when it merely lists the subsection headings or repeats content stated elsewhere.
- The **Reference** and **Clause Boundaries** rules, self-check item #24, and the rationale use periods where a colon or semicolon joined clauses ("Test: do X; if Y, do Z" is now "To test it, do X. If Y, do Z."). No rule content changes.

## [2026-09_rev2] - 2026-09-01

### Added

- A fourth **Reference** rule, **No stand-in words** (`G.stand-ins`). The rule replaces a stand-in word that the sentence could state directly (e.g., *ones*, *the former / the latter*, *respectively*) with the noun. If the clause then repeats the noun, the rule restructures the clause ("detect flaky tests among the generated ones" -> "detect which of the generated tests are flaky").

### Changed

- `scan_reference.py` lists a third kind of candidate, `stand-in` (i.e., *ones*, *the former*, *the latter*, *respectively*, *do / did so*, *those of / that / which / with*).
- The metrics step of the review skill names the `stand-in` kind.

## [2026-09_rev1] - 2026-09-01

### Changed

- Two sentences in `rules-rationale.md` (**Reference and clause boundaries**) use plain language instead of terms such as "frame" and "definite-heavy register". No rule or skill behavior changes.

## [2026-09] - 2026-09-01

### Added

- A **Reference** section in the general layer with three rules that share one test ("which one?"). Anchor every sentence-initial *This / These / That / It* to a noun. A summarizing noun must name something that the text has listed. Use *the* only for a referent that the reader can already identify.
- A **Clause Boundaries** rule in the general layer, **Keep *that* in formal prose** (`G.keep-that`). It restores the relativizer of a restrictive object relative ("the metrics that the benchmark reports") and the complementizer after a reporting verb ("the results show that the effect persists"). The rule does not apply after fixed heads, in quoted text, or in deliberately informal text (e.g., commit messages, code comments).
- `scan_reference.py`, which lists a `<file>:<line>:<col>` row for each sentence-initial *This / These / That / It* followed directly by a verb and each *such* + noun, outside LaTeX comments, code blocks, and common dummy-*it* frames.
- `/ai-slop:review` tests each row of `scan_reference.py` against its rule. It lists a reference under **Items requiring author judgment** when it cannot determine the antecedent, instead of guessing a noun.

## [2026-08_rev1] - 2026-08-27

### Changed

- **No invented compounds or verbs-as-nouns** (`G.no-coinages`) also covers a noun phrase coined ad hoc to name a specific artifact, document, or table, hyphenated or not. The rule replaces such a phrase with a description ("data-sources table" -> "a table listing all data sources").

## [2026-08] - 2026-08-26

### Added

- A punctuation rule in the LaTeX layer, **Em dashes are unspaced.** Write `word---word` without surrounding spaces, the American convention. The rule governs spacing only, and **Em-dashes** (`G.em-dashes`) and **Literal em-dash glyphs in source** (`G.em-dash-glyphs`) govern the choice of mark and the glyph. Verbatim quotes keep the spacing of their source.

## [2026-07_rev2] - 2026-07-24

### Added

- A **Phrases to Avoid** entry in the general layer against **"headline numbers" / "headline figures"**, in favor of naming the figures plainly (e.g., "the largest claims", "the most-cited figures", "the figures").

## [2026-07_rev1] - 2026-07-09

### Added

- A punctuation rule in the general layer, **Name the relation with a connective.** The rule applies when a flagged em-dash or colon introduces an example or a restatement. The fix is then a connective that names the relation, such as "e.g.," or "that is", rather than a bare period or comma. A mark that sets up a single payoff clause or introduces a true list stays.

## [2026-07] - 2026-07-01

### Added

- `refresh_tropes.py`, a maintainer script that refreshes the bundled trope snapshot (`shared/tropes-snapshot.md`) from the gist, then tropes.fyi, and keeps it bit-identical to upstream. It reports "already up to date" without rewriting when the fetched catalog matches the snapshot, and exits non-zero without touching it when both sources are unreachable.

### Changed

- The release protocol refreshes the bundled snapshot with every rev (`CLAUDE.md` rule 6 and the README "Maintainer notes").
- The README recipe for the refresh uses `refresh_tropes.py` instead of a raw `curl`.

## [2026-06_rev16] - 2026-06-29

### Added

- `scan_glyphs.py`, a deterministic recheck for glyphs that the per-section LLM pass undercounts. It prints a `<file>:<line>:<col>` row for each literal em-dash, en-dash, arrow, curly quote, ellipsis, or non-breaking space.
- `/ai-slop:review` takes the em-dash density from `scan_glyphs.py`. Every em-dash, arrow, curly-quote, ellipsis, and non-breaking-space row becomes a per-section finding, while `/ai-slop:review` leaves en-dashes in ranges and glyphs inside quotes or code to judgment.

### Changed

- **Plain, literal language** (`G.plain-language`) names the systems-jargon count nouns "a write", "a read", "a create", and "a delete" as verbs used as nouns, with the rewrite "a write request" or "a write operation".

## [2026-06_rev15] - 2026-06-29

### Added

- `/ai-slop:review-repo` also scans commit messages, which `scan_repo.py` reads from `git log` under a `commit <short-sha>` pseudo-path, so the report groups their findings by commit. `scan_repo.py` skips merge commits and standard trailer lines (e.g., `Co-authored-by`, `Signed-off-by`).
- Options that set which commits the scan reads. The default covers the most recent 200 commits. `--commits=<N>` sets another count, `--commits=all` the full history, `--commits=<range>` a git revision range (e.g., `main..HEAD`), and `--no-commits` turns commit scanning off.
- Commit-message findings are advisory, and `/ai-slop:revise` does not apply them.

## [2026-06_rev14] - 2026-06-26

### Added

- `/ai-slop:review-repo` also scans LaTeX (`.tex`) files and reviews the document body and the `%` comments as prose against the general rules. The LaTeX layer of `/ai-slop:review` remains the tool for citations, BibTeX, and section-aware checks.

## [2026-06_rev13] - 2026-06-26

### Added

- A repo mode, `/ai-slop:review-repo`, which checks every Markdown and plain-text file and the comments and doc-comments of source and config files against the general rules and the trope catalog. The mode writes `ai-slop-report.md` with findings grouped by file.
- `scan_repo.py`, the extractor for the new mode. It reads comments in Shell, Java, Kotlin, Python (including docstrings), JavaScript, and TypeScript; the rest of the C family (C, C++, C#), Go, Rust, Swift, Scala, Dart, Groovy/Gradle, Ruby, PHP, Perl, R, Lua, and Lisp/Clojure; the web and styling formats HTML, XML, Vue, Svelte, CSS, SCSS, and Less; SQL; and config formats such as YAML, TOML, INI, `.properties`, `.env`, Dockerfile, Makefile, CMake, and Terraform. The `COMMENT_SPECS` and `NAME_SPECS` tables in `scan_repo.py` are the authoritative list. The extractor ignores a `//` or `#` inside a string literal when it detects comments, and it skips a shell shebang.
- The extractor honors `.gitignore` in a git repository (it scans the tracked files). It skips generated files (a "DO NOT EDIT" or `@generated` header), lockfiles, binaries, vendored directories, and (in this revision) `.tex` source.

### Changed

- The version string is in ten callsites, with one in the new `review-repo` `SKILL.md`.
