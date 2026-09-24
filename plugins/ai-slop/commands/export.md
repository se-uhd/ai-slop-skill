---
description: Export the general writing rules and the AI trope catalog as one Markdown file that Claude Code loads at the start of every session, so that Claude's replies, edited files, code comments, and commit messages follow the rules.
---

Use the `ai-slop:export` skill.

The skill's workflow is in `skills/export/SKILL.md`. It runs `scripts/export_rules.py`, which combines `shared/rules-general.md` with the AI trope catalog, fetched live from tropes.fyi and from no other source, under an instruction to apply the rules to all prose that Claude writes, and writes the result to `~/.claude/rules/ai-slop.md`. Claude Code reads every Markdown file in that directory at launch, in every project, so no `CLAUDE.md` needs an import. The file carries no rules for a single genre or file format. `/ai-slop:init` writes the scientific and LaTeX layers into a paper project's `WRITING.md`, which serves a different purpose.

The output path is positional. Examples:

- `/ai-slop:export`: write `~/.claude/rules/ai-slop.md` for every session in every project.
- `/ai-slop:export .claude/rules/ai-slop.md`: write the file into the current repository, where it loads for that project only.
- `/ai-slop:export ~/Downloads/ai-slop-writing.md`: write the file elsewhere, for example to add it to a claude.ai Project's knowledge.

`--ste` adds the Simplified Technical English layer, and `--tropes=<path>` (repeatable) reads the catalog from local files. Running the mode again replaces an earlier export with the current rules and catalog. The skill asks before replacing any other file, does not modify `CLAUDE.md`, and does not commit. The file takes effect in the next session.
