---
description: Generate a project-local WRITING.md file from the layered writing rules and add a reference to it in AGENTS.md (creating AGENTS.md if it does not exist).
---

Use the `ai-slop:writing` skill.

The skill builds a `WRITING.md` file in the working directory from the bundled writing rules and the AI trope catalog, which it fetches live from tropes.fyi and from no other source. `scripts/detect_scope.py` selects the rule layers from the target directory. A LaTeX project gets `shared/rules-general.md`, `shared/rules-scientific.md`, and `shared/rules-latex.md`, and any other project gets the general layer. `--scientific` adds the scientific layer, `--general` forces the general layer alone, and `--ste` adds `shared/rules-ste.md`. The skill then creates an `AGENTS.md` that references `WRITING.md`, or appends a reference to an existing one. It also creates a `CLAUDE.md` import of `AGENTS.md`, or preserves an existing Claude reference to the rules. Codex and Claude Code can then read the rules without this plugin installed and when offline.

WRITING.md is meant to be edited freely after generation. It is a project-local copy of the rules and catalog at the moment of generation, not a synced replica.

If `WRITING.md` already exists, the skill asks before overwriting. AGENTS.md is updated idempotently. If it already references `WRITING.md`, nothing is appended. Existing instruction files are preserved, including a nonempty `AGENTS.override.md`, which also receives the reference because Codex loads it instead of `AGENTS.md`.

The skill's workflow is in `skills/writing/SKILL.md`. By default the skill writes into the current working directory. A target directory can be passed as an argument to override the default.

Run this once per project repository. Re-run it only to refresh `WRITING.md` from a newer skill release.
