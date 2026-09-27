---
description: Write the general writing rules and the AI trope catalog into one Markdown file that Claude Code loads at the start of every session, so that Claude's replies, edited files, code comments, and commit messages follow the rules.
---

Use the `ai-slop:init` skill.

The skill's workflow is in `skills/init/SKILL.md`. It runs `scripts/export_rules.py`, which combines `shared/rules-general.md` with the AI trope catalog, fetched live from tropes.fyi and from no other source, under an instruction to apply the rules to all prose that Claude writes, and writes the result to `~/.claude/rules/ai-slop.md`. Claude Code reads every Markdown file in that directory at launch, in every project, so no `CLAUDE.md` needs an import. The file carries no rules for a single genre or file format. `/ai-slop:writing` writes the scientific and LaTeX layers into a paper project's `WRITING.md`, which serves a different purpose.

The output path is positional. Examples:

- `/ai-slop:init`: write `~/.claude/rules/ai-slop.md` for every session in every project.
- `/ai-slop:init .claude/rules/ai-slop.md`: write the file into the current repository, where it loads for that project only.
- `/ai-slop:init ~/Downloads/ai-slop-writing.md`: write the file elsewhere, for example to add it to a claude.ai Project's knowledge.

`--ste` adds the Simplified Technical English layer, and `--tropes=<path>` (repeatable) reads the catalog from local files. Running the mode again replaces the file with the current rules and catalog. The mode also replaces a file from `/ai-slop:export`, its former name. The skill asks before replacing any other file, does not modify `CLAUDE.md`, and does not commit. The file takes effect in the next session.
