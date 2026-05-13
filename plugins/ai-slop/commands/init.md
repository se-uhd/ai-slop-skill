---
description: Generate a project-local WRITING.md file from the skill's writing rules and wire it into CLAUDE.md (creating CLAUDE.md if it does not exist).
---

Use the `ai-slop:init` skill.

The skill builds a `WRITING.md` file in the working directory by concatenating the bundled SE-specific writing rules (`shared/rules.md`) with the AI-trope catalog (fetched live from the upstream Gist, falling back to the tropes.fyi viewer and then the bundled `shared/tropes-snapshot.md`), and either creates a `CLAUDE.md` that references it or appends a reference to an existing one. The result is a paper repository where any Agent Skills client (e.g., Claude Code, Cursor, Copilot, Codex, Gemini CLI, JetBrains Junie) sees both the rules and the trope catalog through the standard CLAUDE.md mechanism, even if the user has not installed this plugin and even when offline.

WRITING.md is meant to be edited freely after generation. It is a project-local copy of the rules and catalog at the moment of generation, not a synced replica.

If `WRITING.md` already exists, the skill asks before overwriting. CLAUDE.md is updated idempotently: if it already references `WRITING.md`, nothing is appended.

The skill's workflow lives in `skills/init/SKILL.md`. By default the skill writes into the current working directory. A target directory can be passed as an argument to override the default.

Run this once per paper repository. Re-run it only to refresh `WRITING.md` from a newer skill release.
