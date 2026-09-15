---
description: Generate a project-local WRITING.md file from the layered writing rules and add a reference to it in CLAUDE.md (creating CLAUDE.md if it does not exist).
---

Use the `ai-slop:init` skill.

The skill builds a `WRITING.md` file in the working directory from the bundled writing rules and the AI-trope catalog, which it fetches live from tropes.fyi, the only source. `scripts/detect_scope.py` selects the rule layers from the target directory. A LaTeX project gets `shared/rules-general.md`, `shared/rules-scientific.md`, and `shared/rules-latex.md`, and any other project gets the general layer. `--scientific` adds the scientific layer, `--general` forces the general layer alone, and `--ste` adds `shared/rules-ste.md`. The skill then creates a `CLAUDE.md` that references `WRITING.md`, or appends a reference to an existing one. The result is a repository where any Agent Skills client sees both the rules and the trope catalog through the standard CLAUDE.md mechanism, even if the user has not installed this plugin and even when offline.

WRITING.md is meant to be edited freely after generation. It is a project-local copy of the rules and catalog at the moment of generation, not a synced replica.

If `WRITING.md` already exists, the skill asks before overwriting. CLAUDE.md is updated idempotently. If it already references `WRITING.md`, nothing is appended.

The skill's workflow is in `skills/init/SKILL.md`. By default the skill writes into the current working directory. A target directory can be passed as an argument to override the default.

Run this once per project repository. Re-run it only to refresh `WRITING.md` from a newer skill release.
