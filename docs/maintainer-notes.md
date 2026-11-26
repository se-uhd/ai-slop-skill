# Maintainer notes

## Refreshing the vendored Markdown linter

The bundled `_vendor/` tree under `plugins/ai-slop/scripts/` holds PyMarkdown plus its pure-Python deps. Like the other upstream-owned paths that `AGENTS.md` lists, it is refreshed in [pymarkdown-skill](https://github.com/se-uhd/pymarkdown-skill), which pins the vendored versions and builds the tree with its `refresh_vendor.py`. To pull a newer release, release it there and sync it in from a checkout of that repo:

```bash
/path/to/pymarkdown-skill/sync/sync_to_skill.sh --target plugins/ai-slop/scripts/
```

The sync replaces `lint_markdown.py`, `check_baseline.py`, `refresh_vendor.py`, `_vendor/`, and `bundled_licenses/`, keeps `schema_checks.py`, `lint_markdown.yaml`, and `tests/`, and records the upstream release in `scripts/.pymarkdown-skill-version`. Do not run the synced `refresh_vendor.py` here, because a tree refreshed in this repo matches no upstream release and the next sync overwrites it.

## Releasing

Releases follow the release protocol in `AGENTS.md`. Run the smoke suite with `python3 plugins/ai-slop/scripts/tests/run_smoke.py` before every commit.

## Commit messages

Commit messages follow Conventional Commits with a body of short bullets, as `AGENTS.md` describes. `scripts/check_commit_message.py` checks the format. Enable its Git hook in your clone with `git config core.hooksPath .githooks`. Claude Code runs the check after each commit through the hook in `.claude/settings.json`, and the workflow `commit-messages.yml` runs it on each pull request and on each push to `main`.

## Validating the manifests

Before committing changes to the manifests, validate them:

```bash
claude plugin validate plugins/ai-slop
claude plugin validate .claude-plugin/marketplace.json
```

To check the pi manifest, run `pi -e .` from the repository root. Pi lists the nine skills at startup and reports any skill warnings.

If a user reports `Failed to install: This plugin uses a source type your Claude Code version does not support`, do not assume that the problem is the `source` field. Claude Code emits that same message for any unrecognized key in either manifest. Run `claude plugin validate` first. The validator reports the real error.
