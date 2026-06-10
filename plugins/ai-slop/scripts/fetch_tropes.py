#!/usr/bin/env python3
"""fetch_tropes.py <bundled-fallback>

Fetch the AI-trope catalog with a three-step fallback chain and emit it on
stdout. On success (exit 0) the body is non-empty — a 200 response with an
empty body is rejected, and the bundled fallback guarantees content even when
offline. Exits 2 without emitting a body on a usage error or when the bundled
fallback itself is missing, unreadable, or empty (an intact install never hits
this; it means the bundle is broken).

Sources, in order:
  1. Upstream Gist (raw markdown):
     https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/
  2. tropes.fyi viewer (markdown body):
     https://tropes.fyi/tropes-md
  3. The bundled fallback file passed as argv[1].

A 200 response with an empty body is rejected (treated as a failed fetch) so
that the next source is tried.

Source attribution: one line is printed to stderr (e.g. `source: gist`,
`source: tropes.fyi`, `source: bundled`) so callers can record which source
was used without having to parse the catalog body. stdout stays a clean
markdown catalog.
"""
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

GIST_URL = "https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/"
VIEWER_URL = "https://tropes.fyi/tropes-md"
TIMEOUT = 10


def try_fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            body = response.read().decode('utf-8', errors='replace')
            return body if body.strip() else None
    except (urllib.error.URLError, socket.timeout, UnicodeDecodeError):
        return None


def main(argv):
    if len(argv) < 2:
        print("usage: fetch_tropes.py <bundled-fallback>", file=sys.stderr)
        return 2
    fallback = Path(argv[1])
    for name, url in (("gist", GIST_URL), ("tropes.fyi", VIEWER_URL)):
        body = try_fetch(url)
        if body:
            print(f"source: {name}", file=sys.stderr)
            sys.stdout.write(body)
            return 0
    try:
        body = fallback.read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        print(f"error: cannot read bundled fallback {fallback}: {e.strerror or e}",
              file=sys.stderr)
        return 2
    if not body.strip():
        print(f"error: bundled fallback {fallback} is empty", file=sys.stderr)
        return 2
    print("source: bundled", file=sys.stderr)
    sys.stdout.write(body)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
