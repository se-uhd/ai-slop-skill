# Skill workflows

## `/ai-slop:review`

Without a path, the review skill looks for a LaTeX root or a PDF in the working directory, and a Markdown or plain-text draft needs an explicit path. Given a document (LaTeX, PDF, or plain text), the review skill:

1. **Loads the rule layers** that the scope calls for, each carrying its own self-check: `shared/rules-general.md` (language, restricted vocabulary, terminology, active voice, punctuation, structure, tone), `shared/rules-scientific.md` (the "significant" caveat, verb tense by section, citation style, statistical reporting per APA/IEEE/ACM, figures and tables, threats to validity), and `shared/rules-latex.md` (LaTeX quotes, caption punctuation, cross-reference and `\citeauthor` macros, `% GROUNDING`, BibTeX). The table under [Rule layers](rule-layers.md) shows which layers each input loads, and `--ste` adds `shared/rules-ste.md` to any row.
2. **Loads the AI trope catalog** via `scripts/fetch_tropes.py`, which reads the rendered viewer at `https://tropes.fyi/tropes-md` and unwraps the catalog from the page. When the fetch fails, the review stops. To override for a single run, pass `--tropes=<path>` (repeatable for multiple files). The named files replace the live catalog and are concatenated in the order given.
3. **Walks the document section by section**, with deterministic scans for the patterns that a reader misses (Unicode glyphs, unanchored references, sentences pasted from one place into another, and, in LaTeX source, unreferenced figures and tables and lowercase, doubled, or hard-coded cross-references), recording each violation as a finding with `Rule`, `Location` (`file:line` for text source, `Section: <name>` for PDF), `Quote` (verbatim, unique within the document), and `Suggested revision` (concrete replacement text).
4. **Computes cross-cutting metrics** (dash density counting em-dashes and ASCII dashes, colon and semicolon density, the combined pause-mark count, restricted-word density per paragraph, sentence-length variance, verb-tense compliance, American-vs-British spelling, the "significant" audit, citation grounding, and, with `--ste`, the STE sentence metrics) and, for LaTeX, a grounding to-do list of ungrounded `\cite{}` calls plus a CrossRef/DBLP reference check for hallucinated or mismatched citations.
5. **Writes `ai-slop-report.md`** in the working directory with a stable schema so that revise mode can act on it.

Review mode does not modify the document. The report is the only output, apart from adding its name to the top-level `.gitignore` when that line is missing.

## `/ai-slop:glossary`

Run `/ai-slop:glossary` without a filename to search the working directory and
relevant subdirectories for the main document. The skill uses project
instructions, the README, build configuration, and document content to identify
the main LaTeX, PDF, Markdown, or plain-text work. It prefers editable source
over a PDF of the same document and follows the files that a LaTeX root includes. A clear
candidate is used directly, with a question only when discovery finds no document
or leaves genuine ambiguity.

Glossary mode reads a paper or document, groups its terms by concept, and
creates or maintains `GLOSSARY.md` in the format of `shared/glossary-format.md`.
Each group of concepts has a table of terms with their accepted variants,
definitions, and sources. A table of vocabulary to avoid and a list of open
questions follow. Each fact is in one place, so the format has no separate
tables for variants, identifiers, or decisions. Each definition follows ISO 704
(*Terminology work: Principles and methods*): it names the broader concept and
what sets the concept apart, without an article, and it can replace the term in
a sentence without a change in meaning. Notes hold the other information.
Definitions carry source locations and short supporting passages, and an
inferred definition is marked as proposed until the authors confirm it. Existing
definitions, distinctions, accepted abbreviations, and scoped vocabulary
restrictions are preserved rather than replaced by newly extracted preferences,
and an existing glossary keeps its structure unless you ask for a conversion.

The same invocation validates the document against the glossary and writes
`ai-slop-report.md` with concrete source suggestions and questions for the author.
The check includes synonyms, conflicting meanings, undefined technical terms,
and newly invented names for concepts that already have a term. It compares
meanings in context, so a glossary does not have to enumerate every future coinage,
and the ordinary sense of a word is not automatically forbidden.
`scripts/scan_glossary.py` lists each use of a word that the glossary avoids,
and the scope of its row decides whether the use is a finding. A term of the
glossary is never a word to avoid, and the script reports a glossary that lists
one, so that a note of the term states the distinction. With `--definitions`,
it also lists the definitions that contain their own term, define each other,
say what a concept is not, or hold more than one statement. The document
stays unchanged, and `/ai-slop:revise` can apply concrete source suggestions.
With `--ste`, the check also gives each key word one meaning (`T.one-meaning`),
and the glossary definitions follow the STE rules.

```text
/ai-slop:glossary
/ai-slop:glossary main.tex
/ai-slop:glossary draft.md
/ai-slop:glossary draft.md --check
/ai-slop:glossary draft.md --convert
/ai-slop:glossary paper.pdf --glossary=terminology/GLOSSARY.md
/ai-slop:glossary main.tex --ste
```

`--check` validates against an existing glossary without editing it, and
`--convert` rewrites an existing glossary into the format and its definitions
into the form of ISO 704 before the check.
`--glossary=<path>` selects a glossary instead of `GLOSSARY.md` in the working
directory. Glossary mode works offline and loads the general terminology rules
without fetching the trope catalog. The glossary is maintained project content,
while the generated report is ignored by git. `/ai-slop:review`, `/ai-slop:review-diff`, and
`/ai-slop:review-repo` also check terminology against the project glossary.

## `/ai-slop:glossary-repo`

Repository glossary mode builds the glossary from the text of a whole
repository. It reads the same scan as `/ai-slop:review-repo` (Markdown,
plain-text, and LaTeX files, the comments and prose string literals of source
and config files, and the text of user interface templates) and searches the
code for the identifiers that name each
concept, which go in the Code column of the glossary. It sorts the directories
into defining sources, such as the README, design documents, and decision
records, and into using sources, records that keep the terms of their date,
and data. A changelog and other records supply former names for the table of
vocabulary to avoid, but they are not checked. A directory of collected data
is excluded with `--exclude=<glob>`.

The check covers the whole repository and writes `ai-slop-report.md` with
findings grouped by file. A finding on a string literal names the tests and
documents that quote the message. A defect of the glossary itself, such as a
term that it also lists as a word to avoid or an avoided word without the
sense that the repository uses, is a finding on `GLOSSARY.md` with a suggested
revision. A proposed definition is written in full, so that the authors can
confirm it as written. An identifier that uses another name is listed for
author judgment rather than renamed. `/ai-slop:revise ai-slop-report.md <file>`
applies the findings for one file.

```text
/ai-slop:glossary-repo
/ai-slop:glossary-repo --check
/ai-slop:glossary-repo --convert
/ai-slop:glossary-repo path/to/repo --exclude='data/*' --exclude='docs/archive/*'
/ai-slop:glossary-repo --ste
```

`--check` validates the repository against an existing glossary without
editing it, `--convert` rewrites the glossary into the format first,
`--glossary=<path>` selects another glossary, `--no-strings` reads
comments without string literals, and `--commits=<spec>` adds commit messages,
which the scan leaves out by default.

## `/ai-slop:review-diff`

Diff mode is a variant of `/ai-slop:review` for git-versioned documents. Instead of walking the full draft, it runs `git diff <base>` (default `HEAD`) and restricts the rule and trope checks to the lines that you added or modified in `.tex`, `.md`, and `.txt` files. All three layers apply to the changed `.tex` files and the general layer (plus the scientific layer with `--scientific`) to the rest, so a code repository with one paper under a subdirectory still gets its Markdown changes reviewed. The output is the same `ai-slop-report.md` schema with one extra header line (`**Diff scope:** base=<ref>, files=<list>`), which lets `/ai-slop:revise` apply the suggestions unchanged.

A finding is in scope only when at least one line of its quote falls on a changed line. Pre-existing issues on untouched lines are not reported. Cross-cutting metrics that need full-document context (e.g., em-dash *density* per page, sentence-length variance over runs of three sentences) are skipped, and only newly added or modified `\cite{}` calls are checked. Diff mode requires a git working tree. Outside one, fall back to `/ai-slop:review`.

## `/ai-slop:review-repo`

Repo mode is the whole-codebase counterpart to review and diff modes. Instead of one document, it runs `scripts/scan_repo.py` to extract the natural-language text of the repository: every Markdown, plain-text, and LaTeX file in full, the comments, doc-comments, and prose string literals of the source and config files, and the commit messages. The script reads comments in most common languages and config formats, such as Python, Java, Go, YAML, and Dockerfile, and the `COMMENT_SPECS`/`NAME_SPECS` tables in `scan_repo.py` list them all. Repo mode then scans that prose against the general rules and the trope catalog and writes `ai-slop-report.md` with findings grouped by file (`### <relpath>`) and by commit (`### commit <short-sha>`), plus a `**Repo scope:**` header line. Comment detection is string-aware. A `//` or `#` inside a string literal is not mistaken for a comment. A string literal on one line that reads as prose, such as an error message or a help text, is extracted with its quote characters, except in test files, whose strings are inputs and expected output. The text of user interface templates is extracted too, from HTML, Vue, and Svelte files, from the multi-line template literals of JavaScript and TypeScript, such as an inline Angular template, and from the JSX of React components: the text between the tags and the values of the attributes that users read, such as `aria-label` and `title`. Text between tags appears as `>text<` in the scan, and a short string under a key that names text, such as `label: 'Manage users'`, is extracted whatever its length. Translation catalogs in JSON, the web app manifest, and Gherkin `.feature` files are read as well. `--no-strings` turns the extraction of strings and template text off, and `--exclude=<glob>` skips the files that match a shell pattern, such as a directory of collected data. In Markdown, a fenced block with a prose format (e.g., `markdown`, `text`) as its info string is read as prose, so a quoted template is content. Other fenced code is skipped.

In a git repository the scan covers the tracked files, so `.gitignore`d build output and dependencies are excluded automatically. Outside one it walks the whole tree. In both cases it skips a denylist of vendored, build, dependency, and test-fixture directories. Generated files (a `DO NOT EDIT` or `@generated` marker on a comment line in the first ten lines, each named on stderr), lockfiles, dependency pins, and binaries are skipped. LaTeX (`.tex`) files are reviewed as prose (body and `%` comments) against the general rules. `/ai-slop:review` remains the dedicated LaTeX tool for citations, BibTeX, and section-aware checks.

Commit messages are scanned too: the subject and body of each commit, with merge commits and the standard trailer lines (`Co-authored-by`, `Signed-off-by`, ...) dropped. The default covers the most recent 200 commits. `--commits=<N>` sets another count, `--commits=all` the full history, `--commits=<range>` a git revision range (e.g., `main..HEAD` for one branch), and `--no-commits` turns it off. Pushed history is rewritten only by a deliberate repair, so findings on commit messages are advisory (a guide for future messages, or for rewording the unpushed commits on a branch) and are not something revise applies. Because the report spans many files, `/ai-slop:revise` (a one-document-at-a-time tool) does not auto-apply it. Fix each file directly, or run `/ai-slop:revise ai-slop-report.md <file>` for one file, which applies the findings under the heading for that file. This mode catches the slop that a diff review never revisits: a British spelling, an em-dash, or a trope that has been in a committed comment or a commit message for many commits.

## `/ai-slop:revise`

Given a previously generated report and the source of the document (LaTeX, Markdown, or plain text), the revise skill:

1. **Parses the report**, extracting the per-section findings.
2. **Locates each `Quote` in the document** using the `Location` hint in the report to disambiguate.
3. **Applies the `Suggested revision`** with one edit per finding, so each change is one diff hunk.
4. **Inserts `% GROUNDING: TODO verify <key>` stubs (LaTeX only)** after the ungrounded `\cite{}` calls listed in the grounding to-do of the report, for the author to fill, or for `/ai-slop:ground` to replace with retrieved quotes.
5. **Skips findings** with a `Quote` that cannot be located uniquely or a suggestion that would break the markup (e.g., LaTeX), with reasons logged in the summary.
6. **Skips items in "Items requiring author judgment"** (they need manual decisions).
7. **Prints a summary** of applied, skipped, and author-judgment-required findings.

Revise mode does not regenerate the report and does not commit. The user runs `git diff` to inspect and `git commit` to keep the changes.

## `/ai-slop:ground`

Given a LaTeX root, the ground skill fills the grounding comments that the review flags as missing:

1. **Extracts the citations** with `scripts/extract_cites.py`, which resolves the root, follows `\input` / `\include`, and emits, per cited key, the claims that the surrounding sentences attribute to it and the BibTeX metadata (title, author, year, DOI, URL) needed to find the source.
2. **Fetches each source** with one agent per cited key, chunked into small slices to stay under rate limits. Each agent retrieves the source (online, or a user-supplied local file for a paywalled article or book) and copies a short verbatim quote that supports the claim.
3. **Checks each quote against its source** with `scripts/check_quotes.py`, which re-reads the file or page that the agent named and confirms that the quote occurs in it. A quote that it cannot find is downgraded to a `TODO verify -- unverified` stub, and a source that it cannot read as text (a PDF) is handed back for the skill to check by hand.
4. **Writes the comments back** with `scripts/insert_grounding.py`, inserting `% GROUNDING: <key> -- "<quote>"` after each ungrounded `\cite{}` call and replacing any `TODO verify` stub left by revise mode or an earlier run (idempotently, matching indentation).

The anti-fabrication rule is mandatory. A quote is written only when the source was actually retrieved, and the check in step 3 enforces it wherever the source is text. Otherwise the comment is `% GROUNDING: <key> -- TODO verify -- <reason>` (`paywalled`, `abstract-only`, `book`, `not-found`, `source-does-not-support`, or `unverified`), never a quote from memory. A `source-does-not-support` result is reported as a finding rather than a gap, because it flags a likely miscitation. Ground mode is LaTeX-only and does not commit. The user inspects the edits with `git diff`. The grounding agents search the web with the claim sentences, so text of an unpublished manuscript leaves the machine. For a draft that must stay on the machine, use local sources.

## `/ai-slop:writing`

The writing skill is a one-shot setup command for new (or existing) project repositories. With `scripts/build_writing.py`, it builds a project-local `WRITING.md` from the bundled writing rules and the AI trope catalog (fetched live from tropes.fyi), then creates or updates `AGENTS.md` with an instruction to read `WRITING.md`. The layers follow the table under [Rule layers](rule-layers.md). `--general` keeps a code repository that contains a paper to the general layer, and `--economist` and `--ste` add their layers. The skill also creates a `CLAUDE.md` import of `AGENTS.md`, or preserves an existing Claude reference to the rules. An existing `AGENTS.override.md` receives the reference too, because Codex and pi read it instead of `AGENTS.md`, even when it is empty. All three clients can use the generated rules without this plugin installed and when offline.

`WRITING.md` is meant to be edited freely after generation. It is a starting point, not a synced replica. The skill confirms before overwriting an existing `WRITING.md`, and the instruction-file updates are idempotent. Existing instructions are preserved, and references already present are not appended again. The writing skill does not modify your content and does not commit.

Conventions specific to one project, such as a venue's structural requirements (e.g., EMSE structured abstracts), preferred terminology, or a project glossary, belong in the `AGENTS.md` of the project. A `CLAUDE.md` containing `@AGENTS.md` also loads them in Claude Code, including older versions. This repository uses that arrangement for its maintainer guidance.

## `/ai-slop:init`

Init mode sets up the rules for the current client across projects, so that the assistant's replies in chat, the files it edits, its code comments, and its commit messages follow the rules without a review afterward. `scripts/export_rules.py` combines the general layer with the AI trope catalog (fetched live from tropes.fyi), each under its own heading, below an instruction to apply the rules to the text that the assistant writes or changes, and to let the writing conventions of the project itself take precedence. `--economist` adds the core Economist advice, and `--ste` adds the STE layer. Both flags can be combined. The file leaves out the self-check of each layer, which restates the rules item by item, and asks for the check in its opening paragraph instead. It also drops the status line of each catalog entry, its `**Avoid patterns like:**` label, and the `---` line after it. The file carries no rules for a single genre or file format. The scientific and LaTeX layers belong to a paper project and stay with `/ai-slop:writing`.

In Claude Code, the default output remains `~/.claude/rules/ai-slop.md`. Claude Code reads every Markdown file under `~/.claude/rules/` at launch, in every project, so the rules load without an import in any `CLAUDE.md`. A path under `.claude/rules/` in a repository loads the file in that project only, and any other path writes the file for another use, such as knowledge for a claude.ai Project or an `@<path>` import. Running the mode again replaces the file with the current rules and catalog. The mode also replaces a file from `/ai-slop:export`, its former name. The skill asks before replacing any other file, so keep your own additions in a separate file. The general layer and the catalog come to about 20,000 tokens, which every session carries in its context. The file takes effect in the next session.

In Codex, the default output is `<codex-home>/ai-slop.md`, with `CODEX_HOME` or `~/.codex` determining the home directory. After exporting successfully, the skill appends an instruction to read that file to the effective global instruction file: a nonempty `AGENTS.override.md` if present, otherwise `AGENTS.md`. It preserves existing instructions and adds the reference only once. The full rules stay in the export file, so the global instruction file stays small and a later run replaces the rules without touching your own instructions. See [Codex instruction discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md). Start a new session to use the setup automatically.

In pi, the default output is `<pi-agent-dir>/ai-slop.md`, with `PI_CODING_AGENT_DIR` or `~/.pi/agent` determining the agent directory. After exporting successfully, the skill appends the same read instruction to the first global context file that pi loads from that directory: an existing `AGENTS.override.md`, which pi reads even when it is empty, then `AGENTS.md` (or `AGENTS.MD`), then `CLAUDE.md` (or `CLAUDE.MD`), and otherwise a new `AGENTS.md`. It preserves existing instructions and adds the reference only once. The rules stay in a separate file so the global context file stays small and a later run can replace them without touching your own instructions.

An explicit output path exports the file without changing the global instructions of Codex or pi. Run init in each client to set it up there, or name the target client in the request. The skill does not change the global configuration of any other client.

`/ai-slop:writing` writes a `WRITING.md` into one project, with the layers that the project calls for, for co-authors to read, edit, and commit. `/ai-slop:init` writes one file for every session and replaces it on each run.
