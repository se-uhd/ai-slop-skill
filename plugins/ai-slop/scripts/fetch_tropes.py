#!/usr/bin/env python3
"""fetch_tropes.py <bundled-fallback>

Fetch the AI-trope catalog with a three-step fallback chain and emit it on
stdout. On success (exit 0) the body is non-empty: a 200 response with an
empty body is rejected, and the bundled fallback guarantees content even when
offline. Exits 2 without emitting a body on a usage error or when the bundled
fallback itself is missing, unreadable, or empty (an intact install never hits
this; it means the bundle is broken).

Sources, in order:
  1. tropes.fyi viewer (the maintained catalog, currently v2):
     https://tropes.fyi/tropes-md
  2. Upstream Gist (a mirror the author last updated in March 2026, so it
     still carries the v1 catalog):
     https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/
  3. The bundled fallback file passed as argv[1].

The viewer serves the catalog inside a rendered HTML page rather than as raw
markdown, so `extract_markdown` pulls the body out of the page: first from the
download link's `data:text/markdown` URI, then from the `<pre>` block that
renders the same text. Both come from the site's own generator and carry the
same bytes. A page that yields neither is rejected, so a redesign of the site
or an error page falls through to the next source instead of passing HTML off
as a catalog.

The site answers the default urllib user agent with 403, so requests carry
USER_AGENT (this skill and its repository URL).

Source attribution: one line is printed to stderr (e.g. `source: tropes.fyi`,
`source: gist`, `source: bundled`) so callers can record which source was used
without having to parse the catalog body. stdout stays a clean markdown
catalog.
"""
import html
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GIST_URL = "https://gist.githubusercontent.com/ossa-ma/f3baa9d25154c33095e22272c631f5a1/raw/"
VIEWER_URL = "https://tropes.fyi/tropes-md"
SOURCES = (("tropes.fyi", VIEWER_URL), ("gist", GIST_URL))
USER_AGENT = "ai-slop-skill (+https://github.com/se-uhd/ai-slop-skill)"
TIMEOUT = 10

DATA_URI_RE = re.compile(r'href="(data:text/markdown[^"]*)"')
PRE_RE = re.compile(r'<pre[^>]*>(.*?)</pre>', re.DOTALL)


def try_fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode('utf-8', errors='replace')
            return body if body.strip() else None
    except (urllib.error.URLError, socket.timeout, UnicodeDecodeError):
        return None


def extract_markdown(body):
    """Return the markdown catalog in body, or None if it holds none.

    A body that is already markdown is returned unchanged. An HTML page is
    unwrapped: the download link's data URI first, then the rendered <pre>
    block. Returns None when neither yields a non-empty body.
    """
    if not body or not body.strip():
        return None
    head = body.lstrip()[:200].lower()
    if not head.startswith('<!doctype') and '<html' not in head:
        return body
    match = DATA_URI_RE.search(body)
    if match:
        uri = html.unescape(match.group(1))
        text = urllib.parse.unquote(uri.split(',', 1)[1]) if ',' in uri else ''
        if text.strip():
            return text
    match = PRE_RE.search(body)
    if match:
        text = html.unescape(match.group(1))
        if text.strip():
            return text
    return None


def main(argv):
    if len(argv) < 2:
        print("usage: fetch_tropes.py <bundled-fallback>", file=sys.stderr)
        return 2
    fallback = Path(argv[1])
    for name, url in SOURCES:
        body = extract_markdown(try_fetch(url))
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
