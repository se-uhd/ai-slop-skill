---
name: writing
description: Generate a project-local WRITING.md file from the layered writing rules and add a reference to it in the AGENTS.md of the repository (creating AGENTS.md if it does not exist). Use when the user wants the writing conventions stored in their repo as an editable, project-local file. Triggers on prompts such as "set up writing rules in this repo", "generate WRITING.md", or `/ai-slop:writing`. Writes WRITING.md, updates AGENTS.md, and preserves Claude Code loading through a CLAUDE.md import. Does not modify your content. For rules that the assistant applies to its own output in every project, use `/ai-slop:init`.
license: CC-BY-4.0
metadata:
  version: "2026-10_rev10"
  homepage: https://github.com/se-uhd/ai-slop-skill
---

# AI Slop Review: Writing Mode

This skill builds a project-local `WRITING.md` by concatenating the layered writing rules with the AI trope catalog (fetched live from tropes.fyi), then either creates an `AGENTS.md` that references it or appends a reference to an existing one. Codex and pi read the reference through `AGENTS.md`, and Claude Code reads it through a `CLAUDE.md` import. All three can use the generated rules without this plugin installed and when offline.

**Audience and tone.** The default user is an author setting up a new project repository or retrofitting an existing one. After this mode runs, the user may edit WRITING.md to add project-specific conventions. The file is a starting point, not a synced replica of the bundled rules.

## Client and paths

This workflow works in Claude Code, Codex, and pi. Resolve `<skill-dir>` to the absolute directory containing this `SKILL.md`, using the skill path supplied by the client. Substitute that directory in every command below and keep the script path quoted. Resolve `../../shared/` and other bundled paths relative to that directory, while keeping the working directory at the user's project. No client-specific environment variable is required.

In Claude Code, invoke `/ai-slop:writing`. In Codex, select the `ai-slop:writing` skill through `/skills` or a `$` mention. In pi, invoke `/skill:writing`. References to other `/ai-slop:` commands below mean the corresponding sibling skill in any client.

## When to use

Invoke this skill when the user:

1. Asks to set up writing rules in their paper repo or to generate a WRITING.md.
2. Runs `/ai-slop:writing`.
3. Wants the writing rules visible to co-authors and to other Agent Skills clients without requiring this plugin to be installed.

Do not invoke when the user wants to audit a draft (use `/ai-slop:review` or `/ai-slop:review-diff`), to apply review findings (`/ai-slop:revise`), or to have the assistant follow the rules in every project (`/ai-slop:init`).

## Inputs

The skill operates on the current working directory. No arguments are required.

**Optional path override.** A target directory can be passed as the first positional argument. The default is the working directory.

## Workflow

1. **Resolve the target directory.** Default is the working directory. If the user passed a directory argument, use that. Verify that it exists and is writable.

2. **Determine which rule layers to include.** The layers under `../../shared/` are `rules-general.md` (always), `rules-scientific.md` (research article conventions), `rules-latex.md` (LaTeX-source mechanics), `rules-economist.md` (the optional core Economist advice), and `rules-ste.md` (the optional Simplified Technical English layer). Run `python3 "<skill-dir>/../../scripts/detect_scope.py" <target-directory>`. `latex` (the directory has a LaTeX root) includes the general, scientific, and LaTeX layers, which the helper selects with `--latex`. `general` includes `rules-general.md`, plus `rules-scientific.md` when the user passed `--scientific` (a non-LaTeX research article project), which the helper also selects with `--scientific`. `--general` overrides the detection and includes `rules-general.md` alone, for a code repository that happens to contain a paper under a subdirectory. `--economist` adds `rules-economist.md` to whatever the detection or `--general` chose, and `--ste` adds `rules-ste.md` for a project that writes in Simplified Technical English. Both flags can be combined, keeping project and research conventions and the stricter STE limits (`E.precedence`).

3. **Write WRITING.md.** Run `python3 "<skill-dir>/../../scripts/build_writing.py" <target>/WRITING.md [--latex | --scientific] [--economist] [--ste]` with the flags from step 2. The helper fetches the catalog from tropes.fyi and writes the whole file: a header for the contributors of the project with the skill version, the selected layers from their first `##` heading onward in the order general, scientific, LaTeX, Economist, STE, and the catalog under one `## AI Writing Tropes to Avoid` section with its headings demoted one level. Do not compose or edit the file by hand. The next step depends on its exit code:
   - `0`: the file is written. The stderr line names the layers and the size of the file.
   - `1`: there is no catalog. tropes.fyi is the only source and there is no bundled fallback, so stop and tell the user, rather than writing a `WRITING.md` with no trope catalog in it.
   - `2`: a usage error, or a file that could not be read. Pass the message on and stop.
   - `3`: `WRITING.md` already exists, and the user may have local edits that matter. Ask before overwriting (e.g., "`WRITING.md` already exists in this directory. Overwrite (y/n)?"). On yes, run the helper again with `--force`. On no, leave WRITING.md alone and continue to the AGENTS.md step.

4. **Update AGENTS.md.**

    **If `<target>/AGENTS.md` does not exist**, create it with this content:

    ````markdown
    # AGENTS.md

    This file guides coding agents working in this repository.

    ## Writing conventions

    Read [`WRITING.md`](./WRITING.md) and apply its rules to all prose in this repository. The file is derived from the [ai-slop-skill](https://github.com/se-uhd/ai-slop-skill) and can be edited to add project-specific conventions. Use the `ai-slop:review` or `ai-slop:review-diff` skill to audit a draft against these rules.
    ````

    **If `<target>/AGENTS.md` exists**, check whether it already references `WRITING.md` (a substring match for `WRITING.md` is sufficient). If found, leave AGENTS.md alone. The reference is already in place. If not found, append the following section to the end of the file, preceded by a blank line:

    ````markdown

    ## Writing conventions

    Read [`WRITING.md`](./WRITING.md) and apply its rules to all prose in this repository. The file is derived from the [ai-slop-skill](https://github.com/se-uhd/ai-slop-skill) and can be edited to add project-specific conventions. Use the `ai-slop:review` or `ai-slop:review-diff` skill to audit a draft against these rules.
    ````

    **Preserve Claude Code loading.** If `<target>/CLAUDE.md` does not exist, create it with `# CLAUDE.md`, a blank line, and `@AGENTS.md` on its own line. If it exists, preserve its contents and append `@AGENTS.md` on a separate line unless it already imports `AGENTS.md` or references `WRITING.md`. If it is a symlink to `AGENTS.md`, leave it alone and do not append a self-import. This keeps older Claude Code versions working and avoids depending on the client's instruction-file setting.

    **Respect Codex and pi overrides.** If a nonempty `<target>/AGENTS.override.md` exists, Codex and pi read it instead of `AGENTS.md`. Preserve it and append the same writing-conventions section there if it does not already reference `WRITING.md`.

5. **Lint and finalize.** For each instruction file created or appended in step 4, run `python3 "<skill-dir>/../../scripts/lint_markdown.py" --fix <path>`. If the linter exits non-zero on any file, read its stdout findings (one per line, tab-separated `<file>:<line>\t<rule>\t<message>`), revise that file in place to address each, and re-run. Repeat at most three iterations per file. After the third pass, proceed regardless of what the linter reports. The lint loop is internal quality control. Do not mention lint output, rule names, exit codes, or iteration counts in the user-facing summary.

6. **Print a summary.** Tell the user what happened to WRITING.md and each instruction file (created / appended / overwritten / left alone / declined).

7. **Stop.** Do not run a review. The user can invoke `/ai-slop:review` separately when ready, and is expected to inspect the new files with `git diff` and commit when satisfied.

## Bundled files

- `../../shared/rules-general.md`, `../../shared/rules-scientific.md`, `../../shared/rules-latex.md`, `../../shared/rules-economist.md`, and `../../shared/rules-ste.md` are the rule layers. The scope and the `--scientific`, `--general`, `--economist`, and `--ste` flags select which layers provide the rules section of WRITING.md.
- `../../scripts/build_writing.py` assembles and writes `WRITING.md` (step 3). It calls `../../scripts/fetch_tropes.py` for the catalog, so the inlined catalog is current at the moment of generation.
- `../../scripts/detect_scope.py` selects the rule layers (step 2), and `../../scripts/lint_markdown.py` lints the instruction files that the skill edits (step 5).

## Constraints

- **Do not silently overwrite WRITING.md.** Always confirm before replacing an existing file. The user may have edited it. The helper refuses to replace it without `--force`.
- **Idempotent AGENTS.md updates.** If AGENTS.md already references `WRITING.md`, do not append a duplicate section. Re-running this skill must be safe.
- **Let the helper write WRITING.md.** It copies the rules and the catalog verbatim. A hand-written copy can drop or alter rules.
- **Do not modify the paper itself.** This mode writes only `WRITING.md`, `AGENTS.md`, the Claude compatibility import in `CLAUDE.md`, and the reference in an existing `AGENTS.override.md` in the target directory.
- **No commits.** Leave the new files in the working tree. The user inspects the result with `git diff` and commits when satisfied.
