---
description: Generate a project-local WRITING.md file from the layered writing rules and add a reference to it in CLAUDE.md (creating CLAUDE.md if it does not exist).
---

Use the `ai-slop:init` skill.

The skill builds a `WRITING.md` file in the working directory by concatenating the bundled writing rules (the layered set in `shared/rules-general.md`, `shared/rules-scientific.md`, and `shared/rules-latex.md`; the layers are auto-detected from the target directory via `scripts/detect_scope.py`: a LaTeX project gets all three, any other project gets the general layer, or general + scientific with `--scientific`) with the AI-trope catalog (fetched live from the upstream Gist, falling back to the tropes.fyi viewer and then the bundled `shared/tropes-snapshot.md`), and either creates a `CLAUDE.md` that references it or appends a reference to an existing one. The result is a repository where any Agent Skills client (e.g., Claude Code, Cursor, Copilot, Codex, Gemini CLI, JetBrains Junie) sees both the rules and the trope catalog through the standard CLAUDE.md mechanism, even if the user has not installed this plugin and even when offline.

WRITING.md is meant to be edited freely after generation. It is a project-local copy of the rules and catalog at the moment of generation, not a synced replica.

If `WRITING.md` already exists, the skill asks before overwriting. CLAUDE.md is updated idempotently: if it already references `WRITING.md`, nothing is appended.

The skill's workflow lives in `skills/init/SKILL.md`. By default the skill writes into the current working directory. A target directory can be passed as an argument to override the default.

Run this once per project repository. Re-run it only to refresh `WRITING.md` from a newer skill release.
