# AI Slop Review Skill

An [Agent Skill](https://agentskills.io/home) bundle that applies rules for writing and reviewing empirical software engineering research papers in LaTeX. The bundle catches AI slop in research drafts and enforces SE-specific conventions for voice and tense, vocabulary, statistical reporting, citations, and BibTeX. Agent Skills is an open standard originally developed by Anthropic and now read by Cursor, GitHub Copilot, OpenAI Codex, Gemini CLI, Claude Code, and JetBrains Junie, among others; see the [client list](https://agentskills.io/clients).

The skill keeps a curated set of SE-specific rules in `rules.md` and fetches the general AI-trope catalog (e.g., banned words, formulaic openings, formatting tics, anaphora and tricolon abuse) at runtime from [tropes.fyi](https://tropes.fyi) by [ossama.is](https://ossama.is). A snapshot of that catalog is bundled as a fallback.

## Versioning

The bundle uses CalVer with a per-month revision counter: `YYYY-MM` for the first release of a calendar month (the implicit `rev0`), then `YYYY-MM_rev1`, `YYYY-MM_rev2`, ... for subsequent releases that month. The canonical version lives in `plugins/ai-slop/.claude-plugin/plugin.json` and is mirrored in `.claude-plugin/marketplace.json` and the `version` field of each `SKILL.md`. Going-forward git tags follow the same scheme.

This scheme replaced an earlier date-string convention (`YYYY-MM-DD`); historical tags from before the switch (`2026-05-07`, `2026-05-08`) are kept under their original names.

## Dependencies

The skills shell out to small Python 3 helpers under `plugins/ai-slop/scripts/` for deterministic checks (LaTeX root detection, trope-catalog fetch chain, BibTeX required-field verification). Requirements:

- `python3` (latest stable; CI pins to 3.14), no third-party packages (stdlib only).

No other runtime dependencies. Smoke tests for the helpers live at `plugins/ai-slop/scripts/tests/run_smoke.py` and can be run with `python3 plugins/ai-slop/scripts/tests/run_smoke.py`.

## Install as a Claude Code plugin

```
/plugin marketplace add se-uhd/ai-slop-skill
/plugin install ai-slop
```

Four slash commands become available:

```
/ai-slop:review
/ai-slop:review-diff
/ai-slop:revise
/ai-slop:init
```

Run them from the directory of your paper. `/ai-slop:review` finds the LaTeX root (or PDF) in the current directory, walks the full draft against the rules, and writes a structured Markdown report to `ai-slop-report.md` in the working directory. `/ai-slop:review-diff` does the same but only on the lines you changed in the git working tree (default base `HEAD`; pass any git ref as an argument to compare against a different baseline, e.g., `/ai-slop:review-diff main`). `/ai-slop:revise` reads the report and applies its suggested revisions to the LaTeX source — the same report schema is used for both review modes. `/ai-slop:init` is a one-shot setup command: it copies the bundled writing rules into a project-local `WRITING.md` and wires it into the repository's `CLAUDE.md` (creating `CLAUDE.md` if missing) so co-authors and any Agent Skills client see the conventions even without this plugin installed. Explicit paths can be passed as arguments to override the auto-detection. The skills also auto-trigger on matching prompts (e.g., "audit this draft for AI slop", "check my edits before I commit", "apply the review report", "set up writing rules in this repo").

To pick up a new release, refresh the marketplace catalog and reload plugins:

```
/plugin marketplace update ai-slop
/reload-plugins
```

The marketplace update reports `(1 plugin bumped)` when a new version is found and installs it; `/reload-plugins` activates the new commands and skills in the running session.

To skip the manual refresh, enable auto-update for the marketplace: run `/plugin`, open the **Marketplaces** tab, select `ai-slop`, and choose **Enable auto-update**. Claude Code then refreshes the marketplace and installs the latest plugin version at startup.

## Use in other Agent Skills clients

The skill files live under `plugins/ai-slop/skills/review/`, `plugins/ai-slop/skills/review-diff/`, `plugins/ai-slop/skills/revise/`, and `plugins/ai-slop/skills/init/`, with shared content in `plugins/ai-slop/shared/` and helper scripts in `plugins/ai-slop/scripts/`. Each `SKILL.md` references the shared bundle via `../../shared/...` and the scripts via `${CLAUDE_SKILL_DIR}/../../scripts/...`. To consume the bundle outside Claude Code's plugin loader, reproduce the `plugins/ai-slop/` subtree under your client's skills directory so those paths resolve, and ensure the client exposes `${CLAUDE_SKILL_DIR}` (or a documented equivalent) when invoking shell commands from skills. Each client's docs are linked from the [Agent Skills client list](https://agentskills.io/clients).

## Use as a system prompt

For chat UIs or LLM APIs without Agent Skills support, paste the contents of `rules.md` and `tropes-snapshot.md` (or fetch the live Gist) into the system prompt. The bundled `tropes-snapshot.md` is plain markdown formatted for system-prompt use.

## What the skills do

Conventions specific to one paper, such as the venue's structural requirements (e.g., EMSE structured abstracts), preferred terminology, or a project glossary, belong in the paper repo's own `CLAUDE.md`, which loads alongside these skills.

### `/ai-slop:review`

Given a paper (`.tex` or `.pdf`), the review skill:

1. **Loads the rule set** from `shared/rules.md`: language conventions, the restricted-vocabulary table with alternatives, the "significant" statistical caveat, terminology consistency, voice and verb tense by section, punctuation (em-dash and colon limits), structure, tone, citation style, statistical reporting per APA/IEEE/ACM, figures and tables, threats to validity, BibTeX verification, and a 19-item self-check.
2. **Loads the AI-trope catalog** via `scripts/fetch_tropes.py`, which tries the upstream Gist (`https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/`), then the rendered viewer at `https://tropes.fyi/tropes-md`, then the bundled `shared/tropes-snapshot.md`. To override for a single run, pass `--tropes=<path>` (repeatable for multiple files); the named files replace the live fetch and are concatenated in the order given.
3. **Walks the paper section by section**, recording each violation as a finding with `Rule`, `Location` (`file:line` for LaTeX), `Quote` (verbatim, unique within the paper), and `Suggested revision` (concrete replacement text).
4. **Computes cross-cutting metrics** (em-dash density, colon density, restricted-word density per paragraph, sentence-length variance, verb-tense compliance, American-vs-British spelling, the "significant" audit, citation grounding).
5. **Writes `ai-slop-report.md`** in the working directory with a stable schema so revise mode can act on it.

Review mode does not modify the paper. The report is the only output.

### `/ai-slop:review-diff`

Diff mode is a variant of `/ai-slop:review` for git-versioned papers. Instead of walking the full draft, it runs `git diff <base>` (default `HEAD`) and restricts the rule and trope checks to the lines you added or modified in `.tex` files. The output is the same `ai-slop-report.md` schema with one extra header line (`**Diff scope:** base=<ref>, files=<list>`), so `/ai-slop:revise` can apply the suggestions unchanged.

A finding is in scope only when at least one line of its quote falls inside the changed-line set; pre-existing issues on untouched lines are not surfaced. Cross-cutting metrics that need full-paper context (e.g., em-dash *density* per page, sentence-length variance over runs of three sentences) are skipped, and only newly added or modified `\cite{}` calls are checked. Diff mode requires a git working tree; outside one, fall back to `/ai-slop:review`.

### `/ai-slop:revise`

Given a previously generated report and the paper's LaTeX source, the revise skill:

1. **Parses the report**, extracting the per-section findings.
2. **Locates each `Quote` in the paper** using the report's `Location` hint to disambiguate.
3. **Applies the `Suggested revision`** with one Edit call per finding (so each change is one diff hunk).
4. **Skips findings** whose `Quote` cannot be located uniquely or whose suggestion would break LaTeX, with reasons logged in the summary.
5. **Skips items in "Items requiring author judgment"** (they need manual decisions).
6. **Prints a summary** of applied, skipped, and author-judgment-required findings.

Revise mode does not regenerate the report and does not commit. The user runs `git diff` to inspect and `git commit` to keep the changes.

### `/ai-slop:init`

The init skill is a one-shot setup command for new (or existing) paper repositories. It builds a project-local `WRITING.md` by concatenating the bundled SE-specific writing rules from `shared/rules.md` with the AI-trope catalog (fetched live from the upstream Gist, with the tropes.fyi viewer and the bundled `shared/tropes-snapshot.md` as fallbacks), then either creates a `CLAUDE.md` that references the file or appends a reference to an existing one. Once both files are in place, every Agent Skills client that loads `CLAUDE.md` (Claude Code, Cursor, Copilot, Codex, Gemini CLI, JetBrains Junie) sees the writing conventions and the trope catalog through the standard mechanism, even when this plugin is not installed and even offline.

`WRITING.md` is meant to be edited freely after generation — it is a starting point, not a synced replica. The skill confirms before overwriting an existing `WRITING.md`, and the `CLAUDE.md` update is idempotent: if `CLAUDE.md` already references `WRITING.md`, nothing is appended on a re-run. The init skill does not modify the paper itself and does not commit.

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
      review-diff.md     /ai-slop:review-diff slash command
      revise.md          /ai-slop:revise slash command
      init.md            /ai-slop:init slash command
    skills/
      review/
        SKILL.md         review-mode skill (assess a draft, write report)
      review-diff/
        SKILL.md         diff-mode skill (review only git-modified lines)
      revise/
        SKILL.md         revise-mode skill (apply a report to the LaTeX source)
      init/
        SKILL.md         setup skill (emit WRITING.md, wire into CLAUDE.md)
    shared/              content shared across skills
      rules.md           SE-specific rule set
      tropes-snapshot.md bundled fallback of the tropes.fyi Gist
    scripts/             deterministic helpers invoked by the skills
      find_latex_root.py       LaTeX root detection
      fetch_tropes.py          trope-catalog fetch chain (Gist → viewer → bundled)
      find_citation_issues.py  cite-cluster + missing-grounding scan
      check_bib_fields.py      BibTeX required-field verification
      tests/run_smoke.py       smoke harness (asserts exit codes + stdout/stderr)
```

## Maintainer notes

### Refreshing the tropes.fyi snapshot

The bundled snapshot is a copy of the upstream Gist. To refresh it:

```bash
curl -sSf https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/ \
  -o plugins/ai-slop/shared/tropes-snapshot.md
```

Bump the version per the scheme above (`YYYY-MM` for the first release of a calendar month, `YYYY-MM_revN` thereafter — count tags matching this month's prefix and add one) in `plugins/ai-slop/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, the `version` field of each `SKILL.md` under `plugins/ai-slop/skills/`, and the `**Skill version:**` line in `review/SKILL.md`'s report template and `init/SKILL.md`'s WRITING.md header.

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
