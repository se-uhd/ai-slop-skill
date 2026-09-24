---
name: export
description: Export the general writing rules and the AI trope catalog as one Markdown file that Claude Code loads at the start of every session, so that Claude's replies in chat, the files it edits, its code comments, and its commit messages follow the rules. Use when the user wants the writing rules applied to everything Claude writes, in every project, or asks for the rules as one file to load at startup or to add to a system prompt, or runs `/ai-slop:export`. Writes `~/.claude/rules/ai-slop.md` by default. For the editable WRITING.md of one project, use `/ai-slop:init`.
license: CC-BY-4.0
metadata:
  version: "2026-09_rev31"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Export Mode

This skill writes the general rule layer and the AI trope catalog (fetched live from tropes.fyi) into one Markdown file, under an instruction to apply them to all prose that Claude writes: replies in chat, files that it creates or edits, code comments and docstrings, and commit messages. Claude Code reads every Markdown file under `~/.claude/rules/` at launch, in every project, so a file at the default location is part of the context of each new session without an import in any `CLAUDE.md`.

**Audience and tone.** The user wants Claude's own output to follow the rules everywhere, instead of auditing it afterward. The file applies to any prose, so it carries no rules for a single genre or file format.

**Export and init.** The two modes serve different purposes. `/ai-slop:init` writes a `WRITING.md` into one project, with the layers that the project calls for (the scientific and LaTeX layers for a paper), for co-authors to read and edit and to commit with the project. Export writes one file for every session, with the general layer only (plus the STE layer on request), and replaces it on each run.

## When to use

Invoke this skill when the user:

1. Wants Claude to follow the writing rules in chat replies and in every file that it touches, across projects.
2. Asks for the rules as one file to load at startup, to add to a system prompt, or to upload to a claude.ai Project.
3. Runs `/ai-slop:export`.

Do not invoke when the user wants the rules of one project as an editable file (use `/ai-slop:init`) or wants to audit text (use `/ai-slop:review` or its variants).

## Inputs

**Output path.** A positional path sets the file to write. The default is `~/.claude/rules/ai-slop.md`, which every session in every project loads. `.claude/rules/ai-slop.md` inside a repository loads the file in that project only. Any other path writes the file there for the user to load another way.

**Flags.** `--ste` adds the Simplified Technical English layer (`../../shared/rules-ste.md`), which applies to any prose. `--tropes=<path>` (repeatable) reads the catalog from local files instead of tropes.fyi, concatenated in the order given, as in `/ai-slop:review`. The scientific and LaTeX layers are not available here, since they apply to research articles and LaTeX source. `/ai-slop:init` writes them into a paper project's `WRITING.md`.

## Workflow

1. **Resolve the output path.** Take the positional path, or `~/.claude/rules/ai-slop.md` when there is none.

2. **Write the file.** Run `python3 ${CLAUDE_SKILL_DIR}/../../scripts/export_rules.py <output> [--ste] [--tropes=<path> ...]`. The script builds the file from `../../shared/rules-general.md` (and `rules-ste.md` with `--ste`) and the catalog, each under its own heading, and writes it in one step, so do not compose or edit the file by hand. The next step depends on its exit code:
   - `0`: the file is written. The stderr line says whether it was created or replaced, and gives its size in bytes and approximate tokens.
   - `1`: there is no catalog. tropes.fyi is the only source and there is no bundled fallback, so stop and tell the user that fetching the catalog failed and that `--tropes=<path>` exports with a local copy.
   - `2`: a usage error, or a file that could not be read. Pass the message on and stop.
   - `3`: a file that is not an earlier export already exists at the output path. The script replaces an earlier export without asking, because running this mode again is how the rules and the catalog are refreshed. Any other file may hold the user's own rules, so ask before replacing it (e.g., "`~/.claude/rules/ai-slop.md` exists and was not written by `/ai-slop:export`. Replace it (y/n)?"). On yes, run the script again with `--force`. On no, stop and leave the file as it is.

3. **Print a summary** in two or three lines:
   - The file: created or replaced at `<output>`, with the layers and its size in tokens, rounded to the nearest thousand. The whole file stays in the context of every session that loads it.
   - How it loads. Under `~/.claude/rules/`, Claude Code loads it at the start of every new session, in every project. Under a repository's `.claude/rules/`, it loads in that project. Elsewhere, name the ways to load it: move it into `~/.claude/rules/`, import it with `@<path>` in a `CLAUDE.md`, or add it to a claude.ai Project's knowledge.
   - The current session does not load it. It takes effect in the next session.

4. **Stop.** Do not review or edit any other file, and do not commit.

## Bundled files

- `../../scripts/export_rules.py` assembles and writes the file, and replaces only an earlier export unless `--force` is passed.
- `../../scripts/fetch_tropes.py` fetches the catalog from tropes.fyi. `export_rules.py` calls it unless `--tropes=<path>` is passed.
- `../../shared/rules-general.md` and `../../shared/rules-ste.md` are the rule layers in the file.

## Constraints

- **Do not edit the exported file by hand.** A new export replaces it. The file's header tells the user to keep their own additions in a separate file, such as another Markdown file under `~/.claude/rules/`.
- **Do not replace a file that is not an earlier export without asking.** It may hold the user's own rules.
- **Do not modify `CLAUDE.md` or any other file.** A file in the rules directory loads without an import, and a file at another path is the user's to load.
- **No commits.** A file written into a repository stays in the working tree for the user to inspect and commit.
