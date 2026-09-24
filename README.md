# AI Slop Review Skill

An [Agent Skill](https://agentskills.io/home) bundle that catches AI slop in prose and enforces conventions for clear writing. It works on any text, such as a Markdown draft, documentation, or a blog post, and adds a scientific layer for empirical software engineering papers (voice and tense, statistical reporting per APA/IEEE/ACM, citations) and a LaTeX layer for LaTeX source (BibTeX, `\citeauthor`, `% GROUNDING`). Both load automatically for `.tex` source, and `--scientific` opts a non-LaTeX manuscript into the scientific layer. An optional STE layer (`--ste`) applies rules based on ASD-STE100 Simplified Technical English to any input. Agent Skills is an open standard originally developed by Anthropic and now read by Claude Code, Cursor, GitHub Copilot, and OpenAI Codex, among others. The [client list](https://agentskills.io/clients) names the rest.

The skill keeps its writing rules in layers (listed under Rule layers below) and fetches a general AI trope catalog (named patterns such as negative parallelism, em-dash addiction, and rule-of-three groupings, each tagged with a status) at runtime from [tropes.fyi](https://tropes.fyi) and from no other source. The table under Rule layers shows which layers each input loads, and `review-repo` never loads the LaTeX layer. The same bundle therefore reviews a Markdown blog draft, a non-LaTeX manuscript (with `--scientific`), or a full LaTeX paper.

## Rule layers

The writing rules ship as four layers. Which of the first three load depends on whether the input is LaTeX source (detected automatically by `scripts/detect_scope.py`) and whether you pass `--scientific`:

| Input | general | scientific | latex |
|---|:---:|:---:|:---:|
| LaTeX source (`.tex`) | yes | yes | yes |
| Anything else, no flag | yes | no | no |
| Anything else, `--scientific` | yes | yes | no |

`rules-general.md` applies to any prose (vocabulary, punctuation, structure, tone). Every rule carries a stable key (`G.semicolons`, `S.significant`, `L.grounding-comments`) that reports, cross-references, and the self-checks cite alongside its name. `rules-scientific.md` adds research article conventions (verb tense by section, citations, statistics, figures and tables, threats to validity). `rules-latex.md` adds LaTeX source mechanics (LaTeX quotes, `\citeauthor`, `% GROUNDING`, BibTeX). A LaTeX paper is always treated as a research article, so the scientific layer loads automatically. For a non-LaTeX manuscript (Markdown or PDF), `--scientific` opts into it.

`rules-ste.md` is the optional STE layer, and `--ste` adds it to any row of the table. It applies part of ASD-STE100 Simplified Technical English: short sentences with the subject and verb near the start, active voice, one topic per paragraph, one meaning per word, verbs instead of nominalizations, and no dropped articles. It changes the ASD-STE100 rules on sentence length and style. Sentence length varies around a target of 25 words, with a tolerance up to 35. Each unit (a reply, a headed section, or a text without headings) carries one stylistic device at most. Quotations and literal strings stay as written. Where the STE layer and the general layer set different limits for the same construction, the STE limit applies. The STE rules carry `T.` keys.

When an STE rewrite of an existing sentence would lose meaning, precision, or force, the sentence stays as written, and a review lists it for author judgment. `scripts/scan_sentences.py` lists the candidates that a count or a word pattern can find: sentences over 25 words, runs of sentences of similar length, passive verbs, and a light verb followed by an action noun ("make a decision").

## Versioning

The bundle uses CalVer with a per-month revision counter: `YYYY-MM` for the first release of a calendar month (the implicit `rev0`), then `YYYY-MM_rev1`, `YYYY-MM_rev2`, ... for subsequent releases that month. The version string appears in twelve callsites, kept in sync by the smoke suite: `plugins/ai-slop/.claude-plugin/plugin.json` (canonical), `.claude-plugin/marketplace.json`, the `version` field of each of the eight `SKILL.md` files, the `**Skill version:**` line in `review/SKILL.md`'s report template, and the `skill version` reference in `init/SKILL.md`'s WRITING.md header. Git tags follow the same scheme.

## Dependencies

The skills call small Python 3 helpers under `plugins/ai-slop/scripts/` for deterministic checks (LaTeX root and scope detection, the trope catalog download, BibTeX required-field verification, reference verification against CrossRef and DBLP, the check of grounding quotes against their sources, Markdown linting of the generated report and bundled rules). Requirements:

- `python3` (latest stable, and CI pins to 3.14). The first-party helpers are stdlib-only. The Markdown linter is [PyMarkdown](https://github.com/jackdewinter/pymarkdown), vendored pure-Python with its dependencies under `plugins/ai-slop/scripts/_vendor/`. Both `lint_markdown.py` and the maintainer-side `check_baseline.py` run against that vendored tree. Both, together with `refresh_vendor.py`, the vendored tree, and `bundled_licenses/`, are synced from the upstream [pymarkdown-skill](https://github.com/se-uhd/pymarkdown-skill) repo and are not edited here. Users do not need to `pip install` anything.

No other runtime dependencies. Three helpers reach the network: the reference check (`verify_references.py`, CrossRef and DBLP), the grounding quote check (`check_quotes.py`, for a quote with a URL as its source), and the trope catalog download (`fetch_tropes.py`, tropes.fyi, which `export_rules.py` calls as well). Offline the reference check degrades cleanly and reports `unchecked-offline`, and the review still completes. The catalog download is required. The catalog has one source and no bundled copy, so the run stops when fetching the catalog fails, unless you pass a catalog file with `--tropes=<path>`. `fetch_tropes.py` accepts only a body with the catalog's shape (a title and its trope headings) and prints the size, heading count, and content hash of what it accepted to stderr, which makes a changed catalog visible. The catalog is third-party text that the skills hand to the model as rules to apply. A paper repository that needs a reproducible review keeps its own copy and passes it with `--tropes`. Smoke tests for the helpers are at `plugins/ai-slop/scripts/tests/run_smoke.py` and can be run with `python3 plugins/ai-slop/scripts/tests/run_smoke.py`.

## Install as a Claude Code plugin

```text
/plugin marketplace add se-uhd/ai-slop-skill
/plugin install ai-slop
```

Eight slash commands become available:

```text
/ai-slop:review
/ai-slop:review-diff
/ai-slop:review-repo
/ai-slop:tldr
/ai-slop:revise
/ai-slop:ground
/ai-slop:init
/ai-slop:export
```

`review`, `review-diff`, and `init` detect LaTeX source automatically and load all three rule layers for it. Any other input loads the general layer. Add `--scientific` to also apply the research article rules to a non-LaTeX manuscript (a Markdown or PDF paper). `review-repo` is the whole-codebase mode and always loads the general layer (`--scientific` optional). It never loads the LaTeX layer, since it reviews a repository's prose and code comments rather than a single paper. `--ste` adds the STE layer in `review`, `review-diff`, `review-repo`, `init`, and `export`.

Run them from your project directory. `/ai-slop:review` finds the document to review in the current directory (a LaTeX root or a PDF, while a Markdown or plain-text draft needs an explicit path), walks the full draft against the rules, and writes a structured Markdown report to `ai-slop-report.md` in the working directory. `/ai-slop:review-diff` does the same but only on the lines that you changed in the git working tree (default base `HEAD`, or any git ref passed as an argument to compare against a different baseline, e.g., `/ai-slop:review-diff main`). `/ai-slop:review-repo` sweeps a whole repository instead of one document: its Markdown, plain-text, and LaTeX files, the comments in its source and config files, and its commit messages, with findings grouped by file and by commit (see `/ai-slop:review-repo` below). `/ai-slop:tldr` runs the review of `/ai-slop:review` on a document or of `/ai-slop:review-repo` on a directory and condenses the report into a short assessment per file (see `/ai-slop:tldr` below). `/ai-slop:revise` reads the report and applies its suggested revisions to the source. All three review modes write the same report schema. For LaTeX papers, `/ai-slop:ground` fills the grounding comments that the review flags as missing. Review *finds* the `\cite{}` calls missing a grounding comment, and ground *fills* them by fetching each cited source and inserting a retrieved verbatim quote (or a `TODO verify -- <reason>` stub when the source cannot be retrieved). `/ai-slop:init` is a one-shot setup command. It copies the bundled writing rules into a project-local `WRITING.md` and adds a reference to it in the repository's `CLAUDE.md` (creating `CLAUDE.md` if missing) so collaborators and any Agent Skills client see the conventions even without this plugin installed. `/ai-slop:export` writes the general rules and the trope catalog into one file under `~/.claude/rules/`, which Claude Code loads at the start of every session, so Claude's own replies and edits follow the rules in every project (see `/ai-slop:export` below). Explicit paths can be passed as arguments to override the auto-detection. The skills also auto-trigger on matching prompts (e.g., "audit this draft for AI slop", "check my edits before I commit", "apply the review report", "ground the citations", "set up writing rules in this repo").

To pick up a new release, refresh the marketplace catalog and reload plugins:

```text
/plugin marketplace update ai-slop
/reload-plugins
```

The marketplace update reports `(1 plugin bumped)` when a new version is found and installs it. `/reload-plugins` activates the new commands and skills in the running session.

To skip the manual refresh, enable auto-update for the marketplace: run `/plugin`, open the **Marketplaces** tab, select `ai-slop`, and choose **Enable auto-update**. Claude Code then refreshes the marketplace and installs the latest plugin version at startup.

## Use in other Agent Skills clients

The skills are laid out per the [Agent Skills specification](https://agentskills.io/specification). Each `SKILL.md` is self-contained and ships under `plugins/ai-slop/skills/review/`, `plugins/ai-slop/skills/review-diff/`, `plugins/ai-slop/skills/review-repo/`, `plugins/ai-slop/skills/tldr/`, `plugins/ai-slop/skills/revise/`, `plugins/ai-slop/skills/ground/`, `plugins/ai-slop/skills/init/`, and `plugins/ai-slop/skills/export/`, with shared content in `plugins/ai-slop/shared/` and helper scripts in `plugins/ai-slop/scripts/`. Each `SKILL.md` references the shared bundle via `../../shared/...` and the scripts via `${CLAUDE_SKILL_DIR}/../../scripts/...`. To use the bundle outside Claude Code's plugin loader, reproduce the `plugins/ai-slop/` subtree under your client's skills directory so those paths resolve, and ensure the client exposes `${CLAUDE_SKILL_DIR}` (or a documented equivalent) when invoking shell commands from skills. Each client's docs are linked from the [Agent Skills client list](https://agentskills.io/clients).

## Use as a system prompt

For chat UIs or LLM APIs without Agent Skills support, paste the contents of the rule layers (`rules-general.md`, plus `rules-scientific.md`, `rules-latex.md`, and `rules-ste.md` as your text calls for) and the catalog from [tropes.fyi](https://tropes.fyi/tropes-md) into the system prompt. The catalog page has a download button, and the file behind it is plain markdown formatted for system-prompt use. `/ai-slop:export <path>` writes the general layer and the catalog into one file at `<path>`, ready to paste or to add to a claude.ai Project's knowledge.

## Skill workflows

Conventions specific to one project, such as a venue's structural requirements (e.g., EMSE structured abstracts), preferred terminology, or a project glossary, belong in the project's own `CLAUDE.md`, which loads alongside these skills.

### `/ai-slop:review`

Given a document (LaTeX, PDF, or plain text), the review skill:

1. **Loads the rule layers** that the scope calls for, each carrying its own self-check: `shared/rules-general.md` (language, restricted vocabulary, terminology, active voice, punctuation, structure, tone), `shared/rules-scientific.md` (the "significant" caveat, verb tense by section, citation style, statistical reporting per APA/IEEE/ACM, figures and tables, threats to validity), and `shared/rules-latex.md` (LaTeX quotes, caption punctuation, cross-reference and `\citeauthor` macros, `% GROUNDING`, BibTeX). The table under Rule layers shows which layers each input loads, and `--ste` adds `shared/rules-ste.md` to any row.
2. **Loads the AI trope catalog** via `scripts/fetch_tropes.py`, which reads the rendered viewer at `https://tropes.fyi/tropes-md` and unwraps the catalog from the page. That is the only source. When fetching the catalog fails, the review stops rather than falling back to something older. To override for a single run, pass `--tropes=<path>` (repeatable for multiple files). The named files replace the live catalog and are concatenated in the order given.
3. **Walks the document section by section**, with deterministic scans for the patterns that a reader misses (Unicode glyphs, unanchored references, and sentences pasted from one place into another), recording each violation as a finding with `Rule`, `Location` (`file:line` for text source, `Section: <name>` for PDF), `Quote` (verbatim, unique within the document), and `Suggested revision` (concrete replacement text).
4. **Computes cross-cutting metrics** (dash density counting em-dashes and ASCII dashes, colon and semicolon density, the combined pause-mark count, restricted-word density per paragraph, sentence-length variance, verb-tense compliance, American-vs-British spelling, the "significant" audit, citation grounding, and, with `--ste`, the STE sentence metrics) and, for LaTeX, a grounding to-do list of ungrounded `\cite{}` calls plus a CrossRef/DBLP reference check for hallucinated or mismatched citations.
5. **Writes `ai-slop-report.md`** in the working directory with a stable schema so revise mode can act on it.

Review mode does not modify the document. The report is the only output, apart from adding its name to the repository's `.gitignore` when that line is missing.

### `/ai-slop:review-diff`

Diff mode is a variant of `/ai-slop:review` for git-versioned documents. Instead of walking the full draft, it runs `git diff <base>` (default `HEAD`) and restricts the rule and trope checks to the lines that you added or modified in `.tex`, `.md`, and `.txt` files. All three layers apply to the changed `.tex` files and the general layer (plus the scientific layer with `--scientific`) to the rest, so a code repository with one paper under a subdirectory still gets its Markdown changes reviewed. The output is the same `ai-slop-report.md` schema with one extra header line (`**Diff scope:** base=<ref>, files=<list>`), which lets `/ai-slop:revise` apply the suggestions unchanged.

A finding is in scope only when at least one line of its quote falls on a changed line. Pre-existing issues on untouched lines are not reported. Cross-cutting metrics that need full-document context (e.g., em-dash *density* per page, sentence-length variance over runs of three sentences) are skipped, and only newly added or modified `\cite{}` calls are checked. Diff mode requires a git working tree. Outside one, fall back to `/ai-slop:review`.

### `/ai-slop:review-repo`

Repo mode is the whole-codebase counterpart to review and diff modes. Instead of one document, it runs `scripts/scan_repo.py` to extract the repository's natural-language text: every Markdown, plain-text, and LaTeX file in full, the comments and doc-comments of the source and config files, and the commit messages. The comment languages are Shell, Java, Kotlin, Python, JavaScript, and TypeScript; the C family, Go, Rust, Swift, Scala, Dart, Groovy/Gradle, Ruby, PHP, Perl, R, Lua, and Lisp/Clojure; HTML/XML, Vue/Svelte, CSS/SCSS/Less, and SQL; and config formats such as YAML, TOML, INI, `.properties`, Dockerfile, and Makefile. The `COMMENT_SPECS`/`NAME_SPECS` tables in `scan_repo.py` are the authoritative list. Repo mode then scans that prose against the general rules and the trope catalog and writes `ai-slop-report.md` with findings grouped by file (`### <relpath>`) and by commit (`### commit <short-sha>`), plus a `**Repo scope:**` header line. Comment detection is string-aware. A `//` or `#` inside a string literal is not mistaken for a comment. In Markdown, a fenced block with a prose format (e.g., `markdown`, `text`) as its info string is read as prose, so a quoted template is content. Other fenced code is skipped.

In a git repository the scan covers the tracked files, so `.gitignore`d build output and dependencies are excluded automatically. Outside one it walks the whole tree. In both cases it skips a denylist of vendored, build, dependency, and test-fixture directories. Generated files (a `DO NOT EDIT` or `@generated` marker on a comment line in the first ten lines, each named on stderr), lockfiles, dependency pins, and binaries are skipped. LaTeX (`.tex`) files are reviewed as prose (body and `%` comments) against the general rules. `/ai-slop:review` remains the dedicated LaTeX tool for citations, BibTeX, and section-aware checks. Commit messages are scanned too: the subject and body of each commit, with merge commits and the standard trailer lines (`Co-authored-by`, `Signed-off-by`, ...) dropped. The default covers the most recent 200 commits. `--commits=<N>` sets another count, `--commits=all` the full history, `--commits=<range>` a git revision range (e.g. `main..HEAD` for one branch), and `--no-commits` turns it off. Pushed history is rewritten only by a deliberate repair, so commit message findings are advisory (a guide for future messages, or for rewording a branch's unpushed commits) and are not something revise applies. Because the report spans many files, `/ai-slop:revise` (a one-document-at-a-time tool) does not auto-apply it. Fix each file directly, or run `/ai-slop:revise ai-slop-report.md <file>` for one file, which applies the findings under that file's heading. This mode catches the slop that a diff review never revisits: a British spelling, an em-dash, or a trope that has been in a committed comment or a commit message for many commits.

### `/ai-slop:tldr`

TL;DR mode answers one question per file: did the authors use AI tools in a reasonable way, or in a way that makes the text harder to read? It runs the review of `/ai-slop:review` on a document, or the review of `/ai-slop:review-repo` on a directory, with the same flags, and writes the full `ai-slop-report.md`. Without a path it auto-detects the document as review does and falls back to the working directory as a repository. `scripts/count_findings.py` then sorts each finding by its cost to the reader (it obscures the meaning, delays the content, or only distracts), ranks the rules of each file by that cost, finds the paragraphs that need a rewrite, and rates the file, and the skill writes `ai-slop-tldr.md`. Each scanned file with findings gets a block with four parts:

- The patterns' **impact on readability**, rated by how much of the prose needs a rewrite. A paragraph needs one when at least two of its findings obscure or delay, and at least one per 100 words. The level is None when no finding obscures or delays, Minor when under a tenth of the prose needs a rewrite, Moderate up to a third, Major up to two thirds, and Severe above that. Major and Severe also need at least three paragraphs that need a rewrite, so one or two of them cannot decide the level of a short text. The share follows the level in parentheses, so a reader sees how close a file is to the next level.
- The **AI-use verdict**, one of three fixed values. It rests on the AI-typical findings, which are the catalog's tropes and the rules for the patterns that AI output overproduces (such as padding, restatement, restricted words, formulaic openings and closings, and em-dashes), and not on grammar slips, dropped words, spelling, or unclear pronouns, which hurried human writing produces too. Curly quotes never count, since the editor inserts them. The skill also records signs of unassisted writing (typos, grammar slips, missing articles), and in a paragraph with such a sign, the patterns that non-native writers produce as readily as models, such as figurative phrasing and padding, stop counting. The verdict is Little sign of AI tools with fewer than two AI-typical findings or fewer than one per page-equivalent, Harder to read when the level is Moderate or above and an AI-typical finding is in a paragraph that needs a rewrite, and Reasonable otherwise.
- An **assessment** of one to five sentences, of which the first states the verdict in fixed words, such as "The reviewer used AI tools in a reasonable way." It names the writers by their role, and for a file with texts by several writers it names the writer who drives the verdict.
- Up to **three bullets** with the worst patterns, under the same line in every block, `**Patterns that most affect readability:**`. They are the first three of the script's ranking (the count weighted 4 for obscures, 3 for delays, and 1 for distracts), each with its count and a verbatim quote of at most about twelve words.

Each block stands on its own, without rule keys, finding numbers, or references to the report, so it can be passed on by itself, for example as feedback on a thesis chapter. The files without findings are listed together, and a repository's commit messages get one block. The reply shows the TL;DR and names any file where the text contradicts its verdict, and `/ai-slop:revise` applies the full report as usual.

### `/ai-slop:revise`

Given a previously generated report and the document's source (LaTeX, Markdown, or plain text), the revise skill:

1. **Parses the report**, extracting the per-section findings.
2. **Locates each `Quote` in the document** using the report's `Location` hint to disambiguate.
3. **Applies the `Suggested revision`** with one Edit call per finding (so each change is one diff hunk).
4. **Inserts `% GROUNDING: TODO verify <key>` stubs (LaTeX only)** after the ungrounded `\cite{}` calls listed in the report's grounding to-do, for the author to fill, or for `/ai-slop:ground` to replace with retrieved quotes.
5. **Skips findings** with a `Quote` that cannot be located uniquely or a suggestion that would break the markup (e.g., LaTeX), with reasons logged in the summary.
6. **Skips items in "Items requiring author judgment"** (they need manual decisions).
7. **Prints a summary** of applied, skipped, and author-judgment-required findings.

Revise mode does not regenerate the report and does not commit. The user runs `git diff` to inspect and `git commit` to keep the changes.

### `/ai-slop:ground`

Given a LaTeX root, the ground skill fills the grounding comments that the review flags as missing:

1. **Extracts the citations** with `scripts/extract_cites.py`, which resolves the root, follows `\input` / `\include`, and emits, per cited key, the claims that the surrounding sentences attribute to it and the BibTeX metadata (title, author, year, DOI, URL) needed to find the source.
2. **Fetches each source** with one agent per cited key, chunked into small slices to stay under rate limits. Each agent retrieves the source (online, or a user-supplied local file for a paywalled article or book) and copies a short verbatim quote that supports the claim.
3. **Checks each quote against its source** with `scripts/check_quotes.py`, which re-reads the file or page that the agent named and confirms that the quote occurs in it. A quote that it cannot find is downgraded to a `TODO verify -- unverified` stub, and a source that it cannot read as text (a PDF) is handed back for the skill to check by hand.
4. **Writes the comments back** with `scripts/insert_grounding.py`, inserting `% GROUNDING: <key> -- "<quote>"` after each ungrounded `\cite{}` call and replacing any `TODO verify` stub left by revise mode or an earlier run (idempotently, matching indentation).

The anti-fabrication rule is mandatory. A quote is written only when the source was actually retrieved, and the check in step 3 enforces it wherever the source is text. Otherwise the comment is `% GROUNDING: <key> -- TODO verify -- <reason>` (`paywalled`, `abstract-only`, `book`, `not-found`, `source-does-not-support`, or `unverified`), never a quote from memory. A `source-does-not-support` result is reported as a finding rather than a gap, because it flags a likely miscitation. Ground mode is LaTeX-only and does not commit. The user inspects the edits with `git diff`. The grounding agents search the web with the claim sentences, so text of an unpublished manuscript leaves the machine. For a draft that must stay on the machine, use local sources.

### `/ai-slop:init`

The init skill is a one-shot setup command for new (or existing) project repositories. It builds a project-local `WRITING.md` by concatenating the bundled writing rules (the layers selected automatically: all three for a LaTeX project, the general layer otherwise, general + scientific with `--scientific`, or the general layer alone with `--general` for a code repository that happens to contain a paper, with the STE layer added by `--ste`) with the AI trope catalog (fetched live from tropes.fyi), then either creates a `CLAUDE.md` that references the file or appends a reference to an existing one. Once both files are in place, every Agent Skills client that loads `CLAUDE.md` sees the writing conventions and the trope catalog through the standard mechanism, even when this plugin is not installed and even offline.

`WRITING.md` is meant to be edited freely after generation. It is a starting point, not a synced replica. The skill confirms before overwriting an existing `WRITING.md`, and the `CLAUDE.md` update is idempotent. If `CLAUDE.md` already references `WRITING.md`, nothing is appended on a re-run. The init skill does not modify your content and does not commit.

### `/ai-slop:export`

Export mode writes the rules into one file that Claude Code loads at the start of every session, so that Claude's replies in chat, the files it edits, its code comments, and its commit messages follow the rules without a review afterward. `scripts/export_rules.py` combines the general layer with the AI trope catalog (fetched live from tropes.fyi), each under its own heading, below an instruction to apply the rules to the text that Claude writes or changes, and to let a project's own writing conventions take precedence. `--ste` adds the STE layer. The file carries no rules for a single genre or file format. The scientific and LaTeX layers belong to a paper project and stay with `/ai-slop:init`.

The default output is `~/.claude/rules/ai-slop.md`. Claude Code reads every Markdown file under `~/.claude/rules/` at launch, in every project, so the rules load without an import in any `CLAUDE.md`. A path under a repository's `.claude/rules/` loads the file in that project only, and any other path writes the file for another use, such as a claude.ai Project's knowledge or an `@<path>` import. Running the mode again replaces an earlier export with the current rules and catalog. The skill asks before replacing any other file, so keep your own additions in a separate file. The general layer and the catalog come to about 20,000 tokens, which every session carries in its context. The file takes effect in the next session.

Export and init serve different purposes. Init writes a `WRITING.md` into one project, with the layers that the project calls for, for co-authors to read, edit, and commit. Export writes one file for every session and replaces it on each run.

## Repository layout

The plugin is under `plugins/ai-slop/`: `commands/` holds the eight slash commands, `skills/` the eight `SKILL.md` workflows (review, review-diff, review-repo, tldr, revise, ground, init, export), and `shared/` the four rule layers plus the rationale doc. `scripts/` holds the vendored Markdown linter under `_vendor/` and the stdlib Python helpers for scope and LaTeX root detection, repository prose extraction (`scan_repo.py`), the glyph, reference, repeat, and sentence scans (`scan_glyphs.py`, `scan_reference.py`, `scan_repeats.py`, `scan_sentences.py`), the count of a report's findings per file for the TL;DR (`count_findings.py`), the trope catalog download, the export of the rules as one file (`export_rules.py`), the citation, BibTeX, and reference checks, citation extraction, the grounding quote check, and grounding-comment insertion. The marketplace manifest is at `.claude-plugin/marketplace.json` and the plugin manifest at `plugins/ai-slop/.claude-plugin/plugin.json`.

## Maintainer notes

### Refreshing the vendored Markdown linter

The bundled `_vendor/` tree under `plugins/ai-slop/scripts/` holds PyMarkdown plus its pure-Python deps. To pull a newer release:

```bash
python3 plugins/ai-slop/scripts/refresh_vendor.py
```

The script creates a clean venv, installs `pymarkdownlnt` with `--no-binary :all:` so every dep is built from source (pure-Python where the package supports it), copies the resolved tree into `_vendor/`, replaces `pyjson5/` with a stdlib shim (PyMarkdown is always invoked with `--no-json5`, so the C-extension is never reached), asserts that no compiled extensions end up in the tree, and regenerates `_vendor/NOTICE` from each package's dist-info. Pin to a specific version with `--version pymarkdownlnt==0.9.37`.

Bump the version at the twelve callsites listed in the Versioning section. The next rev is the highest existing rev for the month plus one, with the bare `YYYY-MM` tag as rev0. After committing the bump, create the matching tag (`git tag YYYY-MM_revN`) and push it. Every release commit gets one, and tags must stay ancestors of `main`. Never amend or rebase a commit that has already been tagged or pushed. Additional work is a new rev, not a re-cut of the released commit.

### Checking the TL;DR verdict

`scripts/tests/fixtures/tldr/` holds synthetic reviews of invented papers, with planted findings and the level and verdict that each case must get, and the smoke suite pins them. To check the review itself, run `/ai-slop:tldr` on each fixture text and pass the reports to `python3 plugins/ai-slop/scripts/tests/check_fixture_recall.py <report> ...`, which lists the planted findings that the review missed, the findings that it added, and the verdicts. The synthetic reviews test that the rules do what they are meant to do, not how often they are right about real writers, which needs texts of known origin.

### Validating the manifests

Before committing changes to the manifests, validate them:

```bash
claude plugin validate plugins/ai-slop
claude plugin validate .claude-plugin/marketplace.json
```

If a user reports `Failed to install: This plugin uses a source type your Claude Code version does not support`, do not assume that the problem is the `source` field. Claude Code emits that same message for any unrecognized key in either manifest. Run `claude plugin validate` first. The validator reports the real error.

## Acknowledgements

The general AI trope catalog is the work of [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi). This skill fetches the catalog at runtime and bundles no copy of it. All credit for the trope catalog goes to him. The layered writing rules (`rules-general.md`, `rules-scientific.md`, `rules-latex.md`, `rules-ste.md`) are maintained by the [Software Engineering Group at Heidelberg University](https://github.com/se-uhd). The STE layer adapts writing rules from the ASD-STE100 Simplified Technical English specification, which ASD maintains, and reproduces neither the specification nor its dictionary.

## License

First-party content is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [`LICENSE`](LICENSE).

Third-party software bundled under `plugins/ai-slop/scripts/_vendor/` is distributed verbatim under its own licenses (MIT, BSD-3-Clause, Apache-2.0, PSF-2.0). See [`plugins/ai-slop/scripts/_vendor/NOTICE`](plugins/ai-slop/scripts/_vendor/NOTICE) for per-package attribution and full license texts.

The AI trope catalog is third-party content by [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi), and it does not declare an explicit license. No copy of it is redistributed here. `plugins/ai-slop/scripts/fetch_tropes.py` fetches it at review time and passes it to the model, which is the use that upstream states on the page ("Add this file to your AI assistant's system prompt or context"). All rights to the catalog remain with the original author.
