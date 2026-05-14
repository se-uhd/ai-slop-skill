# Attribution for `tropes-snapshot.md`

`tropes-snapshot.md` (in this directory) is third-party content, not
authored by this repository's maintainers. This sidecar file documents
its provenance and licensing status so the attribution survives any
future refresh of the snapshot from upstream.

## Source

- Author: Ossama Chaib (<https://ossama.is>)
- Project: <https://tropes.fyi>
- Upstream raw markdown:
  <https://gist.github.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1>
  (raw: <https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/>)

The bundled snapshot is kept bit-identical to the upstream gist body so
that diffs between bundled and online sources are minimal and a refresh
is a straightforward copy. Do not edit `tropes-snapshot.md` in place;
edits made here will be overwritten on the next refresh from upstream.

## License status

The upstream gist and the tropes.fyi site **do not declare an explicit
license**. Default copyright law applies, and all rights to the
catalog remain with the original author.

The catalog is bundled in this skill with attribution and used
consistently with the upstream's stated intent ("Add this file to your
AI assistant's system prompt or context to help it avoid common AI
writing patterns"). This is implied permission for the bundling and
runtime use this skill performs, but it is not a formal license grant.

## Scope of this repository's license

This repository's [`LICENSE`](../../../LICENSE) (CC BY 4.0) applies to
first-party content only. It does **not** apply to `tropes-snapshot.md`.

## Runtime behavior

At runtime, `plugins/ai-slop/scripts/fetch_tropes.py` prefers the live
upstream gist, then the tropes.fyi viewer, and falls back to this
bundled snapshot only when both are unreachable. The fetcher prints
one line to stderr identifying which source was used.

## If you maintain this skill

If you refresh the snapshot from upstream, you do not need to update
this NOTICE file as long as the source URL and author have not changed.
If they have, update this file at the same time.

If Ossama Chaib later declares an explicit license for the catalog
(e.g., CC BY 4.0, CC0, MIT), record the license here and update the
README's "License" section accordingly.
