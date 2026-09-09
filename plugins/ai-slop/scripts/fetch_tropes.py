#!/usr/bin/env python3
"""fetch_tropes.py

Fetch the AI-trope catalog from tropes.fyi and emit it on stdout.

One source, no fallback: <https://tropes.fyi/tropes-md>. When the fetch fails
the script says so and exits non-zero, and the caller stops rather than
reviewing against a catalog that is missing or out of date. To review without
the network, pass an explicit catalog file to the skill with `--tropes=<path>`.

The site serves the catalog inside a rendered HTML page rather than as raw
markdown, so `extract_markdown` unwraps it: first from the download link's
`data:text/markdown` URI, then from the `<pre>` block that renders the same
text. Both come from the site's own generator and carry the same bytes. A page
that yields neither is rejected, so a redesign or an error page fails loudly
instead of passing HTML off as a catalog.

The site answers the default urllib user agent with 403, so requests carry
USER_AGENT (this skill and its repository URL).

Exit codes
----------
  0  catalog written to stdout.
  1  the site was unreachable, or the page carried no catalog.
  2  usage error (this script takes no arguments).
"""
import html
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

VIEWER_URL = "https://tropes.fyi/tropes-md"
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
    if len(argv) > 1:
        print("usage: fetch_tropes.py", file=sys.stderr)
        return 2
    body = extract_markdown(try_fetch(VIEWER_URL))
    if not body:
        print(f"error: no catalog from {VIEWER_URL}; pass --tropes=<path> to "
              "review against a local copy", file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
