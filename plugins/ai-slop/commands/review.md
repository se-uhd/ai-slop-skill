---
description: Review a paper draft for AI slop and violations of the SE writing rules. Generates a structured Markdown report with concrete suggested revisions.
---

Use the `ai-slop:review` skill.

The skill's workflow and report template live in `skills/review/SKILL.md`. By default the skill scans the current working directory for the paper to review (LaTeX root first, falling back to PDF). A path to a `.tex` or `.pdf` can be passed as an argument to override the scan.

The trope catalog can be updated dynamically before the review runs:

- `--tropes=<path>` — load the catalog from the given file (absolute or working-directory-relative) instead of the live source or bundled fallback.
- `--refresh-tropes` — re-fetch the upstream Gist and overwrite `shared/tropes-snapshot.md` before the review begins.
- `--edit-tropes` — pause to let the user edit `./tropes.local.md` (created from a template if missing). The contents are appended to the catalog after the upstream/bundled content.

A `./tropes.local.md` file in the working directory is appended automatically even without `--edit-tropes`, so users can keep project-specific additions checked in alongside the paper.

Do not modify the user's paper; the only output is `ai-slop-report.md` in the working directory.
