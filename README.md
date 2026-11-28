# AI Slop Review Skill

An [Agent Skill](https://agentskills.io/home) bundle that catches AI slop in prose and enforces conventions for clear writing. It works on any text, such as a Markdown draft, documentation, or a blog post, and on the text of a whole repository, including code comments and the messages that a program shows. A glossary of one term for each concept keeps the terminology of a document or a repository consistent. The bundle adds a scientific layer for empirical software engineering papers (e.g., voice and tense, statistical reporting per APA/IEEE/ACM, citations) and a LaTeX layer for LaTeX source (e.g., BibTeX, `\citeauthor`, `% GROUNDING`). Both layers load automatically for `.tex` source, and `--scientific` opts a non-LaTeX manuscript into the scientific layer. Optional layers apply rules based on ASD-STE100 Simplified Technical English (`--ste`) and core advice from *Writing with Style: The Economist Guide* (`--economist`) to any input. Agent Skills is an open standard originally developed by Anthropic and now read by Claude Code, Cursor, GitHub Copilot, OpenAI Codex, and pi, among others. The [client list](https://agentskills.io/clients) names the rest.

The writing rules are in layers (see [Rule layers](docs/rule-layers.md)), and the skills fetch a general AI trope catalog at runtime from [tropes.fyi](https://tropes.fyi), its only source. The catalog names patterns such as negative parallelism, em-dash addiction, and rule-of-three groupings, and tags each with a status.

Stylistic checks require a problem in context and a replacement that preserves the argument, including purpose, distinctions, emphasis, and voice. Word matches, catalog statuses, and counts prompt inspection but do not require rewriting a passage that already works. Explicit conventions such as spelling and citation syntax still apply, and reviews identify those corrections separately from clarity problems.

## Versioning

The bundle uses CalVer with a per-month revision counter: `YYYY-MM` for the first release of a calendar month (the implicit `rev0`), then `YYYY-MM_rev1`, `YYYY-MM_rev2`, ... for subsequent releases that month. The version string appears at twelve callsites, and the smoke suite checks that they agree: `plugins/ai-slop/.claude-plugin/plugin.json` (canonical), `.claude-plugin/marketplace.json`, the `metadata.version` field of each of the nine `SKILL.md` files, and the `**Skill version:**` line in the report template `review/references/report-template.md`. `export_rules.py` and `build_writing.py` read the version from `plugin.json` when they write a file. Git tags follow the same scheme. The pi package manifest (`package.json`) has no version field, because pi pins a git install to a tag.

## Dependencies

The skills call small Python 3 helpers under `plugins/ai-slop/scripts/` for deterministic checks, such as LaTeX root detection, reference verification, and Markdown linting. Requirements:

- `python3` (latest stable, and CI pins to 3.14). The first-party helpers are stdlib-only. The Markdown linter is [PyMarkdown](https://github.com/jackdewinter/pymarkdown), vendored pure-Python with its dependencies under `plugins/ai-slop/scripts/_vendor/`. `lint_markdown.py` and the maintainer-side `check_baseline.py` run against that vendored tree. These two scripts, `refresh_vendor.py`, the vendored tree, and `bundled_licenses/` are synced from the upstream [pymarkdown-skill](https://github.com/se-uhd/pymarkdown-skill) repo and are not edited here. Users do not need to `pip install` anything.

The helpers have no other runtime dependencies. Three of them reach the network: the reference check (`verify_references.py`, CrossRef and doi.org), the grounding quote check (`check_quotes.py`, for a quote with a URL as its source), and the trope catalog download (`fetch_tropes.py`, tropes.fyi, which `export_rules.py` calls as well). Offline, the reference check reports each lookup as `unchecked-offline`, and the review still completes.

The reference check reads DBLP from a local database, since the DBLP web API rate-limits a long bibliography. Build the database once with `python3 plugins/ai-slop/scripts/setup_dblp.py`. It downloads the newest monthly DBLP snapshot (about 1.1 GB, checksum verified) and builds a SQLite database with a full-text title index (about 4 GB, five to ten minutes). The database is at `$AI_SLOP_DBLP`, else at `~/dblp/dblp.db`, and `setup_dblp.py --update` replaces it with the newest snapshot. A database with the same schema that another tool built works as well, so point `AI_SLOP_DBLP` at it instead of building a second one. Without a database, the check names the setup command, still verifies the DOIs, and reports an entry without a DOI that CrossRef does not hold as `unchecked`. Set `CROSSREF_MAILTO` to your email address, or pass `--mailto`, so that CrossRef serves the check from its polite pool, which allows more requests than the public one.

The catalog has one source and no bundled copy, so a run stops when fetching it fails, unless you pass a catalog file with `--tropes=<path>`. `fetch_tropes.py` accepts only a body structured like the catalog (a title and its trope headings) and prints the size, heading count, and content hash of what it accepted to stderr, which makes a changed catalog visible. The review skills pass the files of `--tropes` to `fetch_tropes.py --file`, which checks a local copy in the same way, and the report names the hash. The catalog is data that names candidate patterns. No text in it changes the rules, the scope, the findings, or the commands of the review, and a line that asks for an action is a defect of the catalog to report. A paper repository that needs a reproducible review keeps its own copy and passes it with `--tropes`.

If the download fails, stderr reports the underlying cause, such as a DNS lookup failure, an HTTP status, a TLS error, or a timeout. Empty or oversized responses and responses without a valid catalog are reported separately. A DNS failure can come from restricted network access in the calling environment, even when the site is reachable elsewhere. Run the command in an environment with network access or supply an explicit local catalog with `--tropes=<path>`.

## Install as a Claude Code plugin

```text
/plugin marketplace add se-uhd/ai-slop-skill
/plugin install ai-slop
```

Nine slash commands become available:

| Command | What it does |
|---|---|
| `/ai-slop:review` | Reviews one document against the rules and writes `ai-slop-report.md`. |
| `/ai-slop:review-diff` | Reviews only the lines that changed against a git base (default `HEAD`). |
| `/ai-slop:review-repo` | Reviews the files, code comments, user-facing strings, and commit messages of a whole repository. |
| `/ai-slop:revise` | Applies the suggested revisions of a report to the source. |
| `/ai-slop:ground` | Fills the missing `% GROUNDING` comments of a LaTeX paper with quotes from the cited sources. |
| `/ai-slop:glossary` | Creates or maintains `GLOSSARY.md` for one document and checks the document for competing terms. |
| `/ai-slop:glossary-repo` | Creates or maintains `GLOSSARY.md` for a whole repository and checks its files for competing terms. |
| `/ai-slop:writing` | Copies the rules into a project-local `WRITING.md` and references it from `AGENTS.md`. |
| `/ai-slop:init` | Sets up the general rules for the current client across projects. |

`review`, `review-diff`, and `writing` choose the rule layers by the table under [Rule layers](docs/rule-layers.md). `review-repo` loads the general layer, adds the scientific layer with `--scientific`, and never loads the LaTeX layer, since it reviews the prose and code comments of a repository rather than a single paper. `--ste` and `--economist` add their optional layers in `review`, `review-diff`, `review-repo`, `writing`, and `init`, and `--ste` also in `glossary` and `glossary-repo`.

Run the commands from your project directory. An explicit path as an argument overrides the input that a command detects there. The sections under [Skill workflows](docs/skill-workflows.md) describe each command. The skills also trigger on matching requests (e.g., "audit this draft for AI slop", "check my edits before I commit", "apply the review report", "ground the citations", "set up writing rules in this repo").

To pick up a new release, refresh the marketplace catalog and reload plugins:

```text
/plugin marketplace update ai-slop
/reload-plugins
```

The marketplace update reports `(1 plugin bumped)` when a new version is found and installs it. `/reload-plugins` activates the new skills in the running session. To skip the manual refresh, enable auto-update for the marketplace: run `/plugin`, open the **Marketplaces** tab, select `ai-slop`, and choose **Enable auto-update**. Claude Code then refreshes the marketplace and installs the latest plugin version at startup.

## Install in Codex

Codex accepts the existing Claude-compatible plugin and marketplace manifests, so both clients install the same bundle. With a Codex CLI that provides `codex plugin`:

```bash
codex plugin marketplace add se-uhd/ai-slop-skill
codex plugin add ai-slop@ai-slop
```

For a local checkout, pass its absolute path instead of `se-uhd/ai-slop-skill` to the marketplace command. In Codex, use `/skills` or type `$` to select one of the nine `ai-slop:` skills, then provide the path and flags. For example, select `ai-slop:review` and add `draft.md --ste`. The `/ai-slop:` examples throughout this README and the files under `docs/` are Claude Code slash commands. In Codex they refer to the corresponding skill. Natural-language requests can activate the skills in both clients.

See the official [plugin installation guidance](https://developers.openai.com/plugins/build/plugins) and [Codex skill invocation guidance](https://learn.chatgpt.com/docs/build-skills). Python 3 and the network requirements listed above apply to both clients.

## Install in pi

The repository root is a [pi package](https://pi.dev) whose `package.json` points pi at the nine skills. Install it from a release tag, replacing `<tag>` with a tag from the [tag list](https://github.com/se-uhd/ai-slop-skill/tags):

```bash
pi install git:github.com/se-uhd/ai-slop-skill@<tag>
```

Without `@<tag>`, pi follows the default branch instead of a release. `pi -e git:github.com/se-uhd/ai-slop-skill` loads the package for one session without adding it to your settings. For a local checkout, pass its absolute path to `pi install`.

Pi names the skills after their directories, so invoke them with `/skill:<name>` followed by the path and flags, for example `/skill:review draft.md --ste`. The `/ai-slop:<name>` examples throughout this README and the files under `docs/` correspond to `/skill:<name>` in pi. Natural-language requests can activate the skills as well.

A tag pins the install, and `pi update` does not move it. To pick up a new release, run `pi install` again with the new tag. Pi identifies a git package by its URL without the ref, so the new tag replaces the old one. `pi update git:github.com/se-uhd/ai-slop-skill` updates an install without a tag.

If another installed package provides a skill with the same name, such as `review`, pi keeps the skill that it discovers first and shows a warning at startup. Run `pi config` to disable one of the two. Python 3 and the network requirements listed above apply to pi as well. `/skill:ground` fetches the cited sources, so pi needs a way to read web pages, such as a web-fetch extension or shell access to a tool such as `curl`.

## Use in other Agent Skills clients

The skills follow the [Agent Skills specification](https://agentskills.io/specification). The `plugins/ai-slop/` bundle contains nine workflows under `skills/`, with shared content in `shared/` and helper scripts in `scripts/`. Keep the whole bundle together. Copying a single skill directory omits its shared dependencies. Each workflow resolves bundled paths from the location of its own `SKILL.md` supplied by the client, and runs helpers by absolute path while keeping the user's project as the working directory. No Claude-specific environment variable is needed.

For Claude Code, Codex, and pi, use the installation instructions above. For another client, register the nine skill directories while preserving their relative paths to `shared/` and `scripts/`. The [Agent Skills client list](https://agentskills.io/clients) links to each client's installation instructions.

## Use as a system prompt

For chat UIs or LLM APIs without Agent Skills support, paste the contents of the rule layers (`rules-general.md`, plus `rules-scientific.md`, `rules-latex.md`, `rules-economist.md`, and `rules-ste.md` as your text calls for) and the catalog from [tropes.fyi](https://tropes.fyi/tropes-md) into the system prompt. The catalog page has a download button, and the file behind it is plain markdown formatted for system-prompt use. `/ai-slop:init <path>` writes the general layer and the catalog into one file at `<path>`, ready to paste or to add to a claude.ai Project as knowledge.

## Documentation

- [Rule layers](docs/rule-layers.md) describes the five rule layers and the flags that select them.
- [Skill workflows](docs/skill-workflows.md) describes the steps, options, and output of each skill.
- [Maintainer notes](docs/maintainer-notes.md) describes how to refresh the vendored linter, release, write commit messages, check the Markdown files, and validate the manifests.
- [`AGENTS.md`](AGENTS.md) is the development guide for this repository, with the release protocol and the checks.
- [`CHANGELOG.md`](CHANGELOG.md) lists the changes of each release.

## Repository layout

The plugin is under `plugins/ai-slop/`: `skills/` holds the nine `SKILL.md` workflows (review, review-diff, review-repo, revise, ground, glossary, glossary-repo, writing, init), which Claude Code offers as the `/ai-slop:` slash commands, and `shared/` the five rule layers, the rationale doc, and the glossary format. `scripts/` holds the vendored Markdown linter under `_vendor/` and the stdlib Python helpers for scope and LaTeX root detection, repository prose extraction (`scan_repo.py`), the glossary scan (`scan_glossary.py`), the glyph, reference, repeat, and sentence scans (`scan_glyphs.py`, `scan_reference.py`, `scan_repeats.py`, `scan_sentences.py`), the trope catalog download, the export of the rules as one file (`export_rules.py`), the assembly of `WRITING.md` (`build_writing.py`), the citation, BibTeX, and reference checks, citation extraction, the grounding quote check, and grounding-comment insertion. The marketplace manifest is at `.claude-plugin/marketplace.json` and the plugin manifest at `plugins/ai-slop/.claude-plugin/plugin.json`. The root `package.json` is the pi package manifest, which lists `plugins/ai-slop/skills` under its `pi.skills` key.

## Acknowledgements

The general AI trope catalog is the work of [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi). This skill fetches the catalog at runtime and bundles no copy of it. All credit for the trope catalog goes to him. The layered writing rules (`rules-general.md`, `rules-scientific.md`, `rules-latex.md`, `rules-economist.md`, `rules-ste.md`) are maintained by the [Software Engineering Group at Heidelberg University](https://github.com/se-uhd). The STE layer adapts writing rules from the ASD-STE100 Simplified Technical English specification, which ASD maintains, and reproduces neither the specification nor its dictionary. The Economist layer distills core advice from Lane Greene's *Writing with Style: The Economist Guide* (2023), chiefly the introduction and chapters 1 through 5, into rules and examples written for this bundle. The book is not distributed or needed at runtime.

## License

First-party content is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [`LICENSE`](LICENSE).

Third-party software bundled under `plugins/ai-slop/scripts/_vendor/` is distributed verbatim under its own licenses (MIT, BSD-3-Clause, PSF-2.0). See [`plugins/ai-slop/scripts/_vendor/NOTICE`](plugins/ai-slop/scripts/_vendor/NOTICE) for per-package attribution and full license texts.

The AI trope catalog is third-party content by [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi), and it does not declare an explicit license. No copy of it is redistributed here. `plugins/ai-slop/scripts/fetch_tropes.py` fetches it at review time and passes it to the model, which is the use that upstream states on the page ("Add this file to your AI assistant's system prompt or context"). All rights to the catalog remain with the original author.
