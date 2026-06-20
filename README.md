# AI Slop Review Skill

An [Agent Skill](https://agentskills.io/home) bundle that catches AI slop in prose and enforces conventions for clear writing. It works on any text — a Markdown draft, documentation, a blog post — and adds a scientific layer for empirical software engineering papers (voice and tense, statistical reporting per APA/IEEE/ACM, citations) and a LaTeX layer for LaTeX source (BibTeX, `\citeauthor`, `% GROUNDING`) — both load automatically for `.tex` source, and `--scientific` opts a non-LaTeX manuscript into the scientific layer. Agent Skills is an open standard originally developed by Anthropic and now read by Cursor, GitHub Copilot, OpenAI Codex, Gemini CLI, Claude Code, and JetBrains Junie, among others; see the [client list](https://agentskills.io/clients).

The skill keeps a layered set of writing rules — `rules-general.md` (any prose), `rules-scientific.md` (research article conventions), and `rules-latex.md` (LaTeX mechanics) — and fetches a general AI-trope catalog (e.g., banned words, formulaic openings, formatting tics, anaphora and tricolon abuse) at runtime from [tropes.fyi](https://tropes.fyi). A snapshot of that catalog is bundled as a fallback. Each mode always loads the general layer, adds the LaTeX layer when the input is LaTeX source (detected by `scripts/detect_scope.py`), and adds the scientific (research article) layer for LaTeX or when you pass `--scientific`. So the same bundle reviews a Markdown blog draft, a non-LaTeX manuscript (with `--scientific`), or a full LaTeX paper.

## Rule layers

The writing rules ship as three layers. Which ones load depends on whether the input is LaTeX source (detected automatically by `scripts/detect_scope.py`) and whether you pass `--scientific`:

| Input | general | scientific | latex |
|---|:---:|:---:|:---:|
| LaTeX source (`.tex`) | ✓ | ✓ | ✓ |
| Anything else, no flag | ✓ | — | — |
| Anything else, `--scientific` | ✓ | ✓ | — |

`rules-general.md` applies to any prose (vocabulary, punctuation, structure, tone). `rules-scientific.md` adds research article conventions (verb tense by section, citations, statistics, figures and tables, threats to validity). `rules-latex.md` adds LaTeX source mechanics (LaTeX quotes, `\citeauthor`, `% GROUNDING`, BibTeX). A LaTeX paper is always treated as a research article, so the scientific layer loads automatically; for a non-LaTeX manuscript (Markdown or PDF), `--scientific` opts into it.

## Versioning

The bundle uses CalVer with a per-month revision counter: `YYYY-MM` for the first release of a calendar month (the implicit `rev0`), then `YYYY-MM_rev1`, `YYYY-MM_rev2`, ... for subsequent releases that month. The version string lives in nine callsites, kept in sync by the smoke suite: `plugins/ai-slop/.claude-plugin/plugin.json` (canonical), `.claude-plugin/marketplace.json`, the `version` field of each of the five `SKILL.md` files, the `**Skill version:**` line in `review/SKILL.md`'s report template, and the `skill version` reference in `init/SKILL.md`'s WRITING.md header. Git tags follow the same scheme.

## Dependencies

The skills call small Python 3 helpers under `plugins/ai-slop/scripts/` for deterministic checks (LaTeX root and scope detection, trope-catalog fetch chain, BibTeX required-field verification, reference verification against CrossRef and DBLP, Markdown linting of the generated report and bundled rules). Requirements:

- `python3` (latest stable; CI pins to 3.14). The first-party helpers are stdlib-only. The Markdown linter is [PyMarkdown](https://github.com/jackdewinter/pymarkdown), vendored pure-Python with its dependencies under `plugins/ai-slop/scripts/_vendor/`; `lint_markdown.py` and the maintainer-side `check_baseline.py` (both synced from the upstream [pymarkdown-skill](https://github.com/se-uhd/pymarkdown-skill) repo) run against that vendored tree. Users do not need to `pip install` anything.

No other runtime dependencies. Two helpers reach the network: the reference check (`verify_references.py`, CrossRef and DBLP) and the trope-catalog fetch (`fetch_tropes.py`, the upstream Gist and tropes.fyi). Both degrade cleanly offline — references are reported as `unchecked-offline` and the catalog falls back to the bundled snapshot — so the review still completes. Smoke tests for the helpers live at `plugins/ai-slop/scripts/tests/run_smoke.py` and can be run with `python3 plugins/ai-slop/scripts/tests/run_smoke.py`.

## Install as a Claude Code plugin

```text
/plugin marketplace add se-uhd/ai-slop-skill
/plugin install ai-slop
```

Five slash commands become available:

```text
/ai-slop:review
/ai-slop:review-diff
/ai-slop:revise
/ai-slop:ground
/ai-slop:init
```

`review`, `review-diff`, and `init` detect LaTeX source automatically and load all three rule layers for it; any other input loads the general layer. Add `--scientific` to also apply the research article rules to a non-LaTeX manuscript (a Markdown or PDF paper).

Run them from your project directory. `/ai-slop:review` finds the document to review in the current directory (a LaTeX root or a PDF; pass an explicit path for a Markdown or plain-text draft), walks the full draft against the rules, and writes a structured Markdown report to `ai-slop-report.md` in the working directory. `/ai-slop:review-diff` does the same but only on the lines you changed in the git working tree (default base `HEAD`; pass any git ref as an argument to compare against a different baseline, e.g., `/ai-slop:review-diff main`). `/ai-slop:revise` reads the report and applies its suggested revisions to the source; the same report schema is used for both review modes. `/ai-slop:ground` fills the grounding comments the review flags as missing, for LaTeX papers: review *finds* the `\cite{}` calls missing a grounding comment, ground *fills* them by fetching each cited source and inserting a retrieved verbatim quote (or a `TODO verify -- <reason>` stub when the source cannot be retrieved). `/ai-slop:init` is a one-shot setup command: it copies the bundled writing rules into a project-local `WRITING.md` and adds a reference to it in the repository's `CLAUDE.md` (creating `CLAUDE.md` if missing) so collaborators and any Agent Skills client see the conventions even without this plugin installed. Explicit paths can be passed as arguments to override the auto-detection. The skills also auto-trigger on matching prompts (e.g., "audit this draft for AI slop", "check my edits before I commit", "apply the review report", "ground the citations", "set up writing rules in this repo").

To pick up a new release, refresh the marketplace catalog and reload plugins:

```text
/plugin marketplace update ai-slop
/reload-plugins
```

The marketplace update reports `(1 plugin bumped)` when a new version is found and installs it; `/reload-plugins` activates the new commands and skills in the running session.

To skip the manual refresh, enable auto-update for the marketplace: run `/plugin`, open the **Marketplaces** tab, select `ai-slop`, and choose **Enable auto-update**. Claude Code then refreshes the marketplace and installs the latest plugin version at startup.

## Use in other Agent Skills clients

The skills are laid out per the [Agent Skills specification](https://agentskills.io/specification): each `SKILL.md` is self-contained and ships under `plugins/ai-slop/skills/review/`, `plugins/ai-slop/skills/review-diff/`, `plugins/ai-slop/skills/revise/`, `plugins/ai-slop/skills/ground/`, and `plugins/ai-slop/skills/init/`, with shared content in `plugins/ai-slop/shared/` and helper scripts in `plugins/ai-slop/scripts/`. Each `SKILL.md` references the shared bundle via `../../shared/...` and the scripts via `${CLAUDE_SKILL_DIR}/../../scripts/...`. To use the bundle outside Claude Code's plugin loader, reproduce the `plugins/ai-slop/` subtree under your client's skills directory so those paths resolve, and ensure the client exposes `${CLAUDE_SKILL_DIR}` (or a documented equivalent) when invoking shell commands from skills. Each client's docs are linked from the [Agent Skills client list](https://agentskills.io/clients).

## Use as a system prompt

For chat UIs or LLM APIs without Agent Skills support, paste the contents of the rule layers (`rules-general.md`, plus `rules-scientific.md` and `rules-latex.md` as your text calls for) and `tropes-snapshot.md` (or fetch the live Gist) into the system prompt. The bundled `tropes-snapshot.md` is plain markdown formatted for system-prompt use.

## What the skills do

Conventions specific to one project, such as a venue's structural requirements (e.g., EMSE structured abstracts), preferred terminology, or a project glossary, belong in the project's own `CLAUDE.md`, which loads alongside these skills.

### `/ai-slop:review`

Given a document (LaTeX, PDF, or plain text), the review skill:

1. **Loads the rule layers** the scope calls for — `shared/rules-general.md` (language, restricted vocabulary, terminology, active voice, punctuation, structure, tone), `shared/rules-scientific.md` (the "significant" caveat, verb tense by section, citation style, statistical reporting per APA/IEEE/ACM, figures and tables, threats to validity), and `shared/rules-latex.md` (LaTeX quotes, caption punctuation, cross-reference and `\citeauthor` macros, `% GROUNDING`, BibTeX) — each carrying its own self-check. `scripts/detect_scope.py` detects LaTeX source and loads all three layers for it; any other input loads the general layer, plus the scientific layer when `--scientific` is passed.
2. **Loads the AI-trope catalog** via `scripts/fetch_tropes.py`, which tries the upstream Gist (`https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/`), then the rendered viewer at `https://tropes.fyi/tropes-md`, then the bundled `shared/tropes-snapshot.md`. To override for a single run, pass `--tropes=<path>` (repeatable for multiple files); the named files replace the live fetch and are concatenated in the order given.
3. **Walks the document section by section**, recording each violation as a finding with `Rule`, `Location` (`file:line` for text source, `Section: <name>` for PDF), `Quote` (verbatim, unique within the document), and `Suggested revision` (concrete replacement text).
4. **Computes cross-cutting metrics** (em-dash density, colon density, restricted-word density per paragraph, sentence-length variance, verb-tense compliance, American-vs-British spelling, the "significant" audit, citation grounding) and, for LaTeX, a grounding to-do list of ungrounded `\cite{}` calls plus a CrossRef/DBLP reference check for hallucinated or mismatched citations.
5. **Writes `ai-slop-report.md`** in the working directory with a stable schema so revise mode can act on it.

Review mode does not modify the document. The report is the only output.

### `/ai-slop:review-diff`

Diff mode is a variant of `/ai-slop:review` for git-versioned documents. Instead of walking the full draft, it runs `git diff <base>` (default `HEAD`) and restricts the rule and trope checks to the lines you added or modified — in `.tex` files for a LaTeX project, or `.tex`/`.md`/`.txt` otherwise. The output is the same `ai-slop-report.md` schema with one extra header line (`**Diff scope:** base=<ref>, files=<list>`), so `/ai-slop:revise` can apply the suggestions unchanged.

A finding is in scope only when at least one line of its quote falls inside the changed-line set; pre-existing issues on untouched lines are not reported. Cross-cutting metrics that need full-document context (e.g., em-dash *density* per page, sentence-length variance over runs of three sentences) are skipped, and only newly added or modified `\cite{}` calls are checked. Diff mode requires a git working tree; outside one, fall back to `/ai-slop:review`.

### `/ai-slop:revise`

Given a previously generated report and the document's source, the revise skill:

1. **Parses the report**, extracting the per-section findings.
2. **Locates each `Quote` in the document** using the report's `Location` hint to disambiguate.
3. **Applies the `Suggested revision`** with one Edit call per finding (so each change is one diff hunk).
4. **Inserts `% GROUNDING: TODO verify <key>` stubs** after the ungrounded `\cite{}` calls listed in the report's grounding to-do, for the author to fill — or for `/ai-slop:ground` to replace with retrieved quotes.
5. **Skips findings** whose `Quote` cannot be located uniquely or whose suggestion would break the markup (e.g., LaTeX), with reasons logged in the summary.
6. **Skips items in "Items requiring author judgment"** (they need manual decisions).
7. **Prints a summary** of applied, skipped, and author-judgment-required findings.

Revise mode does not regenerate the report and does not commit. The user runs `git diff` to inspect and `git commit` to keep the changes.

### `/ai-slop:ground`

Ground mode fills the grounding comments the review flags as missing, for LaTeX papers. Review *finds* the `\cite{}` calls missing a grounding comment; ground *fills* them. Given a LaTeX root, the ground skill:

1. **Extracts the citations** with `scripts/extract_cites.py`, which resolves the root, follows `\input` / `\include`, and emits, per cited key, the claims the surrounding sentences attribute to it and the BibTeX metadata (title, author, year, DOI, URL) needed to find the source.
2. **Fetches each source** with one agent per cited key, chunked into small slices to stay under rate limits. Each agent retrieves the source (online, or a user-supplied local file for a paywalled article or book) and copies a short verbatim quote that supports the claim.
3. **Writes the comments back** with `scripts/insert_grounding.py`, inserting `% GROUNDING: <key> -- "<quote>"` after each ungrounded cite and replacing any `TODO verify` stub left by revise mode or an earlier run (idempotently, matching indentation).

The anti-fabrication rule is mandatory: a quote is written only when the source was actually retrieved. Otherwise the comment is `% GROUNDING: <key> -- TODO verify -- <reason>` (`paywalled`, `abstract-only`, `book`, `not-found`, or `source-does-not-support`), never a quote from memory. A `source-does-not-support` result is reported as a finding, not a gap: it flags a likely miscitation. Ground mode is LaTeX-only and does not commit; the user inspects the edits with `git diff`.

### `/ai-slop:init`

The init skill is a one-shot setup command for new (or existing) project repositories. It builds a project-local `WRITING.md` by concatenating the bundled writing rules (the layers selected automatically — all three for a LaTeX project, the general layer otherwise, or general + scientific with `--scientific`) with the AI-trope catalog (fetched live from the upstream Gist, with the tropes.fyi viewer and the bundled `shared/tropes-snapshot.md` as fallbacks), then either creates a `CLAUDE.md` that references the file or appends a reference to an existing one. Once both files are in place, every Agent Skills client that loads `CLAUDE.md` (Claude Code, Cursor, Copilot, Codex, Gemini CLI, JetBrains Junie) sees the writing conventions and the trope catalog through the standard mechanism, even when this plugin is not installed and even offline.

`WRITING.md` is meant to be edited freely after generation; it is a starting point, not a synced replica. The skill confirms before overwriting an existing `WRITING.md`, and the `CLAUDE.md` update is idempotent: if `CLAUDE.md` already references `WRITING.md`, nothing is appended on a re-run. The init skill does not modify your content and does not commit.

## Repository layout

The plugin lives under `plugins/ai-slop/`: `commands/` holds the five slash commands, `skills/` the five `SKILL.md` workflows (review, review-diff, revise, ground, init), `shared/` the three rule layers plus the rationale doc and the bundled trope snapshot, and `scripts/` the stdlib Python helpers — scope and LaTeX root detection, the trope fetch chain, citation, BibTeX, and reference checks, citation extraction and grounding-comment insertion, and the vendored Markdown linter under `_vendor/`. The marketplace manifest sits at `.claude-plugin/marketplace.json` and the plugin manifest at `plugins/ai-slop/.claude-plugin/plugin.json`.

## Maintainer notes

### Refreshing the tropes.fyi snapshot

The bundled snapshot is a copy of the upstream Gist. To refresh it:

```bash
curl -sSf https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/ \
  -o plugins/ai-slop/shared/tropes-snapshot.md
```

### Refreshing the vendored Markdown linter

The bundled `_vendor/` tree under `plugins/ai-slop/scripts/` holds PyMarkdown plus its pure-Python deps. To pull a newer release:

```bash
python3 plugins/ai-slop/scripts/refresh_vendor.py
```

The script creates a clean venv, installs `pymarkdownlnt` with `--no-binary :all:` so every dep is built from source (pure-Python where the package supports it), copies the resolved tree into `_vendor/`, replaces `pyjson5/` with a stdlib shim (PyMarkdown is always invoked with `--no-json5`, so the C-extension is never reached), asserts no compiled extensions land in the tree, and regenerates `_vendor/NOTICE` from each package's dist-info. Pin to a specific version with `--version pymarkdownlnt==0.9.37`.

Bump the version per the scheme above (`YYYY-MM` for the first release of a calendar month, `YYYY-MM_revN` thereafter; the next rev is the highest existing rev for the month plus one — the bare `YYYY-MM` tag is rev0, so the release after it is `_rev1`) in `plugins/ai-slop/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, the `version` field of each `SKILL.md` under `plugins/ai-slop/skills/`, and the `**Skill version:**` line in `review/SKILL.md`'s report template and `init/SKILL.md`'s WRITING.md header. After committing the bump, create the matching tag (`git tag YYYY-MM_revN`) and push it; every release commit gets one, and tags must stay ancestors of `main`. Never amend or rebase a commit that has already been tagged or pushed — additional work is a new rev, not a re-cut of the released one.

### Validating the manifests

Before committing changes to the manifests, validate them:

```bash
claude plugin validate plugins/ai-slop
claude plugin validate .claude-plugin/marketplace.json
```

If a user reports `Failed to install: This plugin uses a source type your Claude Code version does not support`, do **not** assume the problem is the `source` field. Claude Code emits that same message for any unrecognized key in either manifest. Run `claude plugin validate` first; the validator reports the real error.

## Acknowledgements

The general AI-trope catalog is the work of [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi). This skill bundles a snapshot of his Gist for offline use and otherwise fetches it at runtime; all credit for the trope catalog goes to him. The layered writing rules (`rules-general.md`, `rules-scientific.md`, `rules-latex.md`) are maintained by the [Software Engineering Group at Heidelberg University](https://github.com/se-uhd).

## License

First-party content is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [`LICENSE`](LICENSE).

Third-party software bundled under `plugins/ai-slop/scripts/_vendor/` is distributed verbatim under its own licenses (MIT, BSD-3-Clause, Apache-2.0, PSF-2.0). See [`plugins/ai-slop/scripts/_vendor/NOTICE`](plugins/ai-slop/scripts/_vendor/NOTICE) for per-package attribution and full license texts.

The AI-trope catalog bundled at `plugins/ai-slop/shared/tropes-snapshot.md` is third-party content by [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi). The upstream gist does not declare an explicit license; the snapshot is bundled here with attribution and used consistently with upstream's stated intent ("Add this file to your AI assistant's system prompt or context"). All rights to the catalog remain with the original author. See [`plugins/ai-slop/shared/tropes-snapshot.ATTRIBUTION.md`](plugins/ai-slop/shared/tropes-snapshot.ATTRIBUTION.md) for the full provenance note; the snapshot itself is kept bit-identical to upstream so refreshes are a straightforward copy. The runtime fetcher (`plugins/ai-slop/scripts/fetch_tropes.py`) prefers the live upstream when reachable and falls back to the snapshot offline.
