# AI Slop Review Skill

An [Agent Skill](https://agentskills.io/home) bundle that applies rules for writing and reviewing empirical software engineering research papers in LaTeX. The bundle catches AI slop in research drafts and enforces SE-specific conventions for voice and tense, vocabulary, statistical reporting, citations, and BibTeX. Agent Skills is an open standard originally developed by Anthropic and now read by Cursor, GitHub Copilot, OpenAI Codex, Gemini CLI, Claude Code, and JetBrains Junie, among others; see the [client list](https://agentskills.io/clients).

The skill keeps a curated set of SE-specific rules in `rules.md` and fetches the general AI-trope catalog (banned words, formulaic openings, formatting tics, anaphora and tricolon abuse) at runtime from [tropes.fyi](https://tropes.fyi) by [ossama.is](https://ossama.is). A snapshot of that catalog is bundled as a fallback.

## Versioning

The bundle uses CalVer with the release date (`YYYY-MM-DD`). The canonical version lives in `plugins/ai-slop/.claude-plugin/plugin.json` and is mirrored in `.claude-plugin/marketplace.json` and the `version` field of each `SKILL.md`.

## Install as a Claude Code plugin

```
/plugin marketplace add se-uhd/ai-slop-skill
/plugin install ai-slop
```

Two slash commands become available:

```
/ai-slop:review
/ai-slop:revise
```

Run them from the directory of your paper. `/ai-slop:review` finds the LaTeX root (or PDF) in the current directory, walks the draft against the rules, and writes a structured Markdown report to `ai-slop-report.md` in the working directory. `/ai-slop:revise` reads that report and applies its suggested revisions to the LaTeX source. Explicit paths can still be passed as arguments to override the auto-detection. The two skills also auto-trigger on matching prompts ("audit this draft for AI slop", "apply the review report").

To pick up a new release, refresh the marketplace catalog and reload plugins:

```
/plugin marketplace update ai-slop
/reload-plugins
```

The marketplace update reports `(1 plugin bumped)` when a new version is found and installs it; `/reload-plugins` activates the new commands and skills in the running session.

## Use in other Agent Skills clients

The skill files live under `plugins/ai-slop/skills/review/`, `plugins/ai-slop/skills/revise/`, and `plugins/ai-slop/shared/`. Each `SKILL.md` references the shared bundle via `../../shared/...`. To consume the bundle outside Claude Code's plugin loader, reproduce the `plugins/ai-slop/` subtree under your client's skills directory so the relative paths resolve. Each client's docs are linked from the [Agent Skills client list](https://agentskills.io/clients).

## Use as a system prompt

For chat UIs or LLM APIs without Agent Skills support, paste the contents of `rules.md` and `tropes-snapshot.md` (or fetch the live Gist) into the system prompt. The bundled `tropes-snapshot.md` is plain markdown formatted for system-prompt use.

## What the skills do

Conventions specific to one paper, such as the venue's structural requirements (e.g., EMSE structured abstracts), preferred terminology, or a project glossary, belong in the paper repo's own `CLAUDE.md`, which loads alongside these skills.

### `/ai-slop:review`

Given a paper (`.tex` or `.pdf`), the review skill:

1. **Loads the rule set** from `shared/rules.md`: language conventions, the restricted-vocabulary table with alternatives, the "significant" statistical caveat, terminology consistency, voice and verb tense by section, punctuation (em-dash and colon limits), structure, tone, citation style, statistical reporting per APA/IEEE/ACM, figures and tables, threats to validity, BibTeX verification, and a 19-item self-check.
2. **Loads the AI-trope catalog** from the upstream Gist (`https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/`), falling back to the rendered viewer at `https://tropes.fyi/tropes-md` and then to the bundled `shared/tropes-snapshot.md`. The catalog can be updated dynamically before the review runs: pass `--tropes=<path>` to use a custom file, `--refresh-tropes` to re-fetch and overwrite the bundled snapshot, or `--edit-tropes` to pause and edit `./tropes.local.md`. Any `./tropes.local.md` in the working directory is appended to the catalog automatically.
3. **Walks the paper section by section**, recording each violation as a finding with `Rule`, `Location` (`file:line` for LaTeX), `Quote` (verbatim, unique within the paper), and `Suggested revision` (concrete replacement text).
4. **Computes cross-cutting metrics** (em-dash density, colon density, restricted-word density per paragraph, sentence-length variance, verb-tense compliance, American-vs-British spelling, the "significant" audit, citation grounding).
5. **Writes `ai-slop-report.md`** in the working directory with a stable schema so revise mode can act on it.

Review mode does not modify the paper. The report is the only output.

### `/ai-slop:revise`

Given a previously generated report and the paper's LaTeX source, the revise skill:

1. **Parses the report**, extracting the per-section findings.
2. **Locates each `Quote` in the paper** using the report's `Location` hint to disambiguate.
3. **Applies the `Suggested revision`** with one Edit call per finding (so each change is one diff hunk).
4. **Skips findings** whose `Quote` cannot be located uniquely or whose suggestion would break LaTeX, with reasons logged in the summary.
5. **Skips items in "Items requiring author judgment"** (they need manual decisions).
6. **Prints a summary** of applied, skipped, and author-judgment-required findings.

Revise mode does not regenerate the report and does not commit. The user runs `git diff` to inspect and `git commit` to keep the changes.

## Repository layout

```
.claude-plugin/
  marketplace.json       marketplace entry (single-plugin)
plugins/
  ai-slop/
    .claude-plugin/
      plugin.json        plugin manifest
    commands/
      review.md          /ai-slop:review slash command
      revise.md          /ai-slop:revise slash command
    skills/
      review/
        SKILL.md         review-mode skill (assess a draft, write report)
      revise/
        SKILL.md         revise-mode skill (apply a report to the LaTeX source)
    shared/              content shared by both skills
      rules.md           SE-specific rule set
      tropes-snapshot.md bundled fallback of the tropes.fyi Gist
```

## Maintainer notes

### Refreshing the tropes.fyi snapshot

The bundled snapshot is a copy of the upstream Gist. To refresh it:

```bash
curl -sSf https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/ \
  -o plugins/ai-slop/shared/tropes-snapshot.md
```

Bump the version (today's date in `YYYY-MM-DD`) in `plugins/ai-slop/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, and the `version` field of each `SKILL.md` under `plugins/ai-slop/skills/`.

### Validating the manifests

Before committing changes to the manifests, validate them:

```bash
claude plugin validate plugins/ai-slop
claude plugin validate .claude-plugin/marketplace.json
```

If a user reports `Failed to install: This plugin uses a source type your Claude Code version does not support`, do **not** assume the problem is the `source` field. Claude Code emits that same message for any unrecognized key in either manifest. Run `claude plugin validate` first; the validator surfaces the real error.

## Acknowledgements

The general AI-trope catalog is the work of [Ossama Chaib](https://ossama.is) at [tropes.fyi](https://tropes.fyi). This skill bundles a snapshot of his Gist for offline use and otherwise fetches it at runtime; all credit for the trope catalog goes to him. The SE-specific rules in `rules.md` are maintained by the [Software Engineering Group at Heidelberg University](https://github.com/se-uhd).

## License

Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE`.
