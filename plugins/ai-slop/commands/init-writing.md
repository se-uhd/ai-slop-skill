---
description: Generate a project-local WRITING.md file from the skill's writing rules and wire it into CLAUDE.md (creating CLAUDE.md if it does not exist).
---

Use the `ai-slop:init-writing` skill.

The skill copies the bundled SE-specific writing rules (`shared/rules.md`) into a `WRITING.md` file in the working directory and either creates a `CLAUDE.md` that references it or appends a reference to an existing one. The result is a paper repository where any Agent Skills client (e.g., Claude Code, Cursor, Copilot, Codex, Gemini CLI, JetBrains Junie) sees the writing conventions through the standard CLAUDE.md mechanism, even if the user has not installed this plugin.

WRITING.md is meant to be edited freely after generation. It is a project-local copy of the rules at the moment of generation, not a synced replica.

If `WRITING.md` already exists, the skill asks before overwriting. CLAUDE.md is updated idempotently: if it already references `WRITING.md`, nothing is appended.

The skill's workflow lives in `skills/init-writing/SKILL.md`. By default the skill writes into the current working directory. A target directory can be passed as an argument to override the default.

Run this once per paper repository. Re-run it only to refresh `WRITING.md` from a newer skill release.
