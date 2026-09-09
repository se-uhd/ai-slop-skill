#!/usr/bin/env python3
"""fetch_tropes.py

Fetch the AI-trope catalog from tropes.fyi and emit it on stdout.

One source, no fallback: <https://tropes.fyi/tropes-md>. When the fetch fails
the script says so and exits non-zero, and the caller stops rather than
reviewing against a catalog that is missing or out of date. To review without
the network, pass an explicit catalog file to the skill with `--tropes=<path>`.

The site serves the catalog inside a rendered HTML page rather than as raw
markdown, so `extract_markdown` unwraps it: first from the download link's
`data:text/markdown` URI (percent-encoded or base64), then from the `<pre>`
block that renders the same text. Both come from the site's own generator and
carry the same bytes. Whatever is extracted, and a body that arrives as plain
text, is accepted only when it has the catalog's shape (see
`looks_like_catalog`): a Markdown H1 as its first line and at least
MIN_HEADINGS `## ` trope headings. A plain-text error message, a JSON error
body, or an error page that happens to carry a `<pre>` block is rejected, so a
redesign or an outage fails loudly instead of passing something else off as the
catalog. A body over MAX_BYTES is rejected too.

What was accepted is described on stderr (byte count, heading count, and a
content hash), so a changed catalog is visible in the run's log and two runs
can be compared. The content is third-party text that the skills hand to the
model as rules to apply, so a paper repository that needs a reproducible
review keeps its own copy and passes it with `--tropes=<path>`.

The site answers the default urllib user agent with 403, so requests carry
USER_AGENT (this skill and its repository URL).

Exit codes
----------
  0  catalog written to stdout.
  1  the site was unreachable, or the page carried no catalog.
  2  usage error (this script takes no arguments).
"""
import base64
import binascii
import hashlib
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
MAX_BYTES = 2_000_000   # the catalog is tens of kilobytes; anything larger is not it
MIN_HEADINGS = 5        # the catalog carries dozens of `## ` trope headings

DATA_URI_RE = re.compile(r'href="(data:text/markdown[^"]*)"')
PRE_RE = re.compile(r'<pre[^>]*>(.*?)</pre>', re.DOTALL)
HEADING_RE = re.compile(r'^## \S', re.M)


def try_fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return None
            body = raw.decode('utf-8', errors='replace')
            return body if body.strip() else None
    except (urllib.error.URLError, socket.timeout, UnicodeDecodeError):
        return None


def looks_like_catalog(text):
    """True when `text` has the catalog's shape: a Markdown H1 as its first
    non-blank line and at least MIN_HEADINGS `## ` trope headings."""
    if not text or not text.lstrip().startswith('# '):
        return False
    return len(HEADING_RE.findall(text)) >= MIN_HEADINGS


def decode_data_uri(uri):
    """Return the text payload of a `data:` URI, decoding base64 when the
    header says so and percent-encoding otherwise. Returns '' when the payload
    is missing or malformed."""
    head, _, payload = uri.partition(',')
    if not payload:
        return ''
    if ';base64' in head.lower():
        try:
            return base64.b64decode(payload, validate=True).decode('utf-8', errors='replace')
        except (binascii.Error, ValueError):
            return ''
    return urllib.parse.unquote(payload)


def extract_markdown(body):
    """Return the markdown catalog in body, or None if it holds none.

    A body that is already markdown is a candidate as it is. An HTML page is
    unwrapped into candidates: the download link's data URI first, then the
    rendered <pre> block. The first candidate with the catalog's shape is
    returned. Returns None when no candidate looks like the catalog.
    """
    if not body or not body.strip():
        return None
    head = body.lstrip()[:200].lower()
    candidates = []
    if not head.startswith('<!doctype') and '<html' not in head:
        candidates.append(body)
    else:
        match = DATA_URI_RE.search(body)
        if match:
            candidates.append(decode_data_uri(html.unescape(match.group(1))))
        match = PRE_RE.search(body)
        if match:
            candidates.append(html.unescape(match.group(1)))
    for text in candidates:
        if looks_like_catalog(text):
            return text
    return None


def describe(body):
    """One-line identity of the catalog: size, heading count, content hash."""
    raw = body.encode('utf-8')
    digest = hashlib.sha256(raw).hexdigest()[:12]
    return (f"fetched {len(raw)} bytes, {len(HEADING_RE.findall(body))} trope "
            f"heading(s), sha256 {digest}")


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
    print(describe(body), file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
