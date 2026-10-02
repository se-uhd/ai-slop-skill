---
name: init
description: Set up the general writing rules and AI trope catalog for Claude Code or Codex across projects, or export them as one Markdown file for a system prompt. Use when the user wants the assistant's replies, edits, comments, and commit messages to follow these rules, or runs `/ai-slop:init`. Claude Code uses ~/.claude/rules/ai-slop.md. Codex uses ai-slop.md in its home directory with a reference in its global instructions. For an editable WRITING.md in one project, use `/ai-slop:writing`.
license: CC-BY-4.0
metadata:
  version: "2026-10_rev1"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Init Mode

This skill writes the general rule layer and the AI trope catalog (fetched live from tropes.fyi) into one Markdown file, under an instruction to apply them to all prose that the assistant writes: replies in chat, files that it creates or edits, code comments and docstrings, and commit messages. Claude Code loads the file from its rules directory. Codex reads it through a reference in its global instructions. The selected client determines the default destination and loading step.

**Audience and tone.** The user wants the assistant's own output to follow the rules everywhere, instead of auditing it afterward. The file applies to any prose, so it carries no rules for a single genre or file format.

**Init and writing.** `/ai-slop:writing` writes a `WRITING.md` into one project, with the layers that the project calls for (the scientific and LaTeX layers for a paper), for co-authors to read and edit and to commit with the project. Init writes one file for every session, with the general layer only (plus the STE layer on request), and replaces it on each run.

## Client and paths

This workflow works in Claude Code and Codex. Resolve `<skill-dir>` to the absolute directory containing this `SKILL.md`, using the skill path supplied by the client. Substitute that directory in every command below and keep the script path quoted. Resolve `../../shared/` and other bundled paths relative to that directory, while keeping the working directory at the user's project. No client-specific environment variable is required.

In Claude Code, invoke `/ai-slop:init`. In Codex, select the `ai-slop:init` skill through `/skills` or a `$` mention. References to other `/ai-slop:` commands below mean the corresponding sibling skill in either client.

## When to use

Invoke this skill when the user:

1. Wants the assistant to follow the writing rules in chat replies and in every file that it touches, across projects.
2. Asks for the rules as one file to load at startup, to add to a system prompt, or to upload to a claude.ai Project.
3. Runs `/ai-slop:init`.

Do not invoke when the user wants the rules of one project as an editable file (use `/ai-slop:writing`) or wants to audit text (use `/ai-slop:review` or its variants).

## Inputs

**Client.** Use the current client unless the user names a different target. If the client cannot be identified, ask which client to set up. An explicit export path needs no client selection.

**Output path.** A positional path sets the file to write and skips the automatic Codex registration step. With no path, Claude Code uses `~/.claude/rules/ai-slop.md`. Codex uses `<codex-home>/ai-slop.md`, where `<codex-home>` is the configured `CODEX_HOME` or `~/.codex` when unset. Expand these paths before passing them to the helper. Never export the full rules into an existing `AGENTS.md` or `AGENTS.override.md` as part of automatic setup.

**Flags.** `--ste` adds the Simplified Technical English layer (`../../shared/rules-ste.md`), which applies to any prose. `--tropes=<path>` (repeatable) reads the catalog from local files instead of tropes.fyi, concatenated in the order given, as in `/ai-slop:review`. The scientific and LaTeX layers are not available here, since they apply to research articles and LaTeX source. `/ai-slop:writing` writes them into a paper project's `WRITING.md`.

## Workflow

1. **Resolve the output path.** Take the positional path, or select the default for the target client as described in Inputs. Record whether the path was explicit.

2. **Write the file.** Run `python3 "<skill-dir>/../../scripts/export_rules.py" <output> [--ste] [--tropes=<path> ...]`. The script builds the file from `../../shared/rules-general.md` (and `rules-ste.md` with `--ste`) and the catalog, each under its own heading. It leaves out each layer's self-check, which restates the rules, and each catalog entry's status line, label, and `---` line. The script writes the file in one step, so do not compose or edit the file by hand. The next step depends on its exit code:
   - `0`: the file is written. The stderr line says whether it was created or replaced, and gives its size in bytes and approximate tokens.
   - `1`: there is no catalog. tropes.fyi is the only source and there is no bundled fallback, so stop and tell the user that fetching the catalog failed and that `--tropes=<path>` writes the file from a local copy.
   - `2`: a usage error, or a file that could not be read. Pass the message on and stop.
   - `3`: a file that this mode did not write already exists at the output path. The script replaces a file from an earlier run without asking, because running this mode again is how the rules and the catalog are refreshed. Any other file may hold the user's own rules, so ask before replacing it (e.g., "`<output>` exists and was not written by `/ai-slop:init`. Replace it (y/n)?"). On yes, run the script again with `--force`. On no, stop and leave the file as it is.

3. **Register the Codex default.** Only after a successful export, when setting up Codex without an explicit output path, add a reference in its global instructions. Use a nonempty `<codex-home>/AGENTS.override.md` if present, otherwise `<codex-home>/AGENTS.md`. Preserve all existing text. If the selected file already instructs Codex to read the exported rules, leave it alone. Otherwise append a `## Writing conventions` section with this instruction, substituting the absolute path:

    ```markdown
    Read `/absolute/path/to/ai-slop.md` before writing prose, and apply its rules to replies, edited files, comments, and commit messages. Project-specific writing conventions take precedence.
    ```

    Create the selected file if missing. Keep the rules themselves in the export file, because Codex limits the automatically loaded instruction files to 32 KiB by default. A Markdown link or Claude's `@path` syntax alone does not substitute for this explicit read instruction. If permissions prevent updating the global file, report that the export succeeded but registration did not, and show the reference to add. Claude Code needs no registration because it reads its rules directory automatically.

4. **Print a summary** in two or three lines:
   - The file: created or replaced at `<output>`, with the layers and its size in tokens, rounded to the nearest thousand. The whole file stays in the context of every session that loads it.
   - How it loads. For the Codex default, name the global instruction file updated or already referencing the export. For Claude Code, its user rules directory loads in every project and a repository's `.claude/rules/` loads in that project. An explicit path outside those Claude directories is an export only. Explain how to load it in the target client: an explicit read instruction in Codex's `AGENTS.md`, an `@<path>` import in Claude's `CLAUDE.md`, or a system prompt attachment.
   - Start a new session to use the setup automatically. The exported rules occupy context when read.

5. **Stop.** Do not review the project or edit files beyond the export and the Codex registration described above. Do not commit.

## Bundled files

- `../../scripts/export_rules.py` assembles and writes the file. Unless `--force` is passed, it replaces only a file from an earlier run, including one from `/ai-slop:export`, the former name of this mode.
- `../../scripts/fetch_tropes.py` fetches the catalog from tropes.fyi. `export_rules.py` calls it unless `--tropes=<path>` is passed.
- `../../shared/rules-general.md` and `../../shared/rules-ste.md` are the rule layers in the file.

## Constraints

- **Do not edit the file by hand.** The next run replaces it. The file's header tells the user to keep their own additions in a separate file, such as another Markdown file under `~/.claude/rules/`.
- **Ask before replacing a file that this mode did not write.** It may hold the user's own rules.
- **Preserve existing instructions.** Claude setup and explicit exports write only the output file. Automatic Codex setup also appends its reference to the effective global instruction file without replacing existing content. Do not change Codex configuration or instruction-size limits.
- **No commits.** A file written into a repository stays in the working tree for the user to inspect and commit.
