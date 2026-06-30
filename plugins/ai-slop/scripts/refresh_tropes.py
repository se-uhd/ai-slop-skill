#!/usr/bin/env python3
"""refresh_tropes.py [output-path]

Refresh the bundled AI-trope snapshot from upstream, overwriting
`../shared/tropes-snapshot.md` (resolved relative to this script) — or the
path given as argv[1].

The snapshot is the offline fallback `fetch_tropes.py` serves when the
upstream Gist and the tropes.fyi viewer are both unreachable. This script
keeps it bit-identical to upstream. Maintainer-only: run it as part of every
release rev (see CLAUDE.md "Release protocol") so the fallback never drifts
from the live catalog. End users never run it — `fetch_tropes.py` fetches
live at review time and only falls back to the bundled copy.

Sources, in order — the same upstream chain as `fetch_tropes.py`, minus the
bundled fallback (refreshing the snapshot from the very copy we are about to
overwrite would be a meaningless no-op):
  1. Upstream Gist (raw markdown)
  2. tropes.fyi viewer (markdown body)

So if BOTH network sources are unreachable the script exits 1 and leaves the
snapshot untouched, rather than rewriting it with stale or empty content. A
fetch whose body is byte-identical to the current snapshot is reported as
already up to date and the file is not rewritten (no spurious diff).

One line is printed to stderr identifying the source and the outcome (e.g.
`source: gist; snapshot updated`); stdout is left empty.

Exit codes
----------
  0  snapshot written, or already identical (file left untouched).
  1  both upstream sources unreachable; snapshot left unchanged.
  2  usage error, or the resolved output path could not be written.
"""
import sys
from pathlib import Path

from fetch_tropes import GIST_URL, VIEWER_URL, try_fetch

DEFAULT_SNAPSHOT = (
    Path(__file__).resolve().parent.parent / "shared" / "tropes-snapshot.md"
)


def main(argv):
    if len(argv) > 2:
        print("usage: refresh_tropes.py [output-path]", file=sys.stderr)
        return 2
    out = Path(argv[1]) if len(argv) == 2 else DEFAULT_SNAPSHOT
    for name, url in (("gist", GIST_URL), ("tropes.fyi", VIEWER_URL)):
        body = try_fetch(url)
        if not body:
            continue
        try:
            current = out.read_text(encoding="utf-8") if out.exists() else None
        except OSError:
            current = None
        if current == body:
            print(f"source: {name}; snapshot already up to date ({out})",
                  file=sys.stderr)
            return 0
        try:
            out.write_text(body, encoding="utf-8")
        except OSError as e:
            print(f"error: cannot write snapshot {out}: {e.strerror or e}",
                  file=sys.stderr)
            return 2
        print(f"source: {name}; snapshot updated ({out})", file=sys.stderr)
        return 0
    print("error: both upstream sources unreachable; snapshot left unchanged",
          file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
