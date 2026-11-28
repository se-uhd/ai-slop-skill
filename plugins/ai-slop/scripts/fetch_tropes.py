#!/usr/bin/env python3
"""fetch_tropes.py [--file <path> ...]

Fetch the AI trope catalog from tropes.fyi, or read a local copy of it, and
emit it on stdout.

One source, no fallback: <https://tropes.fyi/tropes-md>. When fetching the
catalog fails, the script says so and exits non-zero, and the caller stops
rather than reviewing against a catalog that is missing or out of date. To
review without the network, pass an explicit catalog file to the skill with
`--tropes=<path>`, which the review skills pass on as `--file <path>`.

The site serves the catalog inside a rendered HTML page rather than as raw
markdown. `extract_markdown` therefore unwraps it: first from the
`data:text/markdown` URI of the download link (percent-encoded or base64),
then from the `<pre>` block that renders the same text. Both copies come from the
generator of the site itself and carry the same bytes. Whatever is extracted,
and a body that arrives as plain text, is accepted only when it is structured
like the catalog (see `looks_like_catalog`): a Markdown H1 as its first
non-blank line and at least
MIN_HEADINGS `## ` trope headings. A plain-text error message, a JSON error
body, or an error page that happens to carry a `<pre>` block is rejected, so a
redesign or an outage stops the run with an error instead of returning other
text as the catalog. A body over MAX_BYTES is rejected too.

`--file <path>` (repeatable) reads local files instead of the site,
concatenated in the order given (see `read_files`). The concatenation gets
the checks of a download: at most MAX_BYTES, not empty, and structured like
the catalog. A local copy is the Markdown file that the download link of the
site gives, so the script does not unwrap a page from it. The copy must also
be valid UTF-8, so the hash on stderr is the SHA-256 of the bytes of the
files, which `cat <files> | shasum -a 256` reproduces. `code-slop tropes
--file` of code-slop-skill applies the same checks and prints the same hash.

What was accepted is described on stderr (byte count, heading count, and a
content hash), which makes a changed catalog visible in the run log and lets
a reader compare two runs. The content is third-party text. The review skills
hand it to the model as data that names candidate patterns, and a line in it
that asks for an action is a defect of the catalog to report, never an
instruction. A paper repository that needs a reproducible review keeps its
own copy and passes it with `--tropes=<path>`.

The site answers the default urllib user agent with 403, so requests carry
USER_AGENT (this skill and its repository URL).
Fetch errors go to stderr with the underlying network or response failure.
In particular, a DNS error can come from restricted network access in the
calling environment and does not establish that the site is down.

Exit codes
----------
  0  catalog written to stdout.
  1  the site was unreachable, the page carried no catalog, or a local copy
     could not be read or is not the catalog.
  2  usage error: an argument other than `--file <path>`.
"""
import base64
import binascii
import hashlib
import html
import http.client
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

VIEWER_URL = "https://tropes.fyi/tropes-md"
USER_AGENT = "ai-slop-skill (+https://github.com/se-uhd/ai-slop-skill)"
TIMEOUT = 10
MAX_BYTES = 2_000_000   # the catalog is tens of kilobytes, so a body this large is not the catalog
MIN_HEADINGS = 5        # the catalog carries dozens of `## ` trope headings

DATA_URI_RE = re.compile(r'href="(data:text/markdown[^"]*)"')
PRE_RE = re.compile(r'<pre[^>]*>(.*?)</pre>', re.DOTALL)
HEADING_RE = re.compile(r'^## \S', re.M)


def fetch_error_message(error):
    """Describe a transport error without losing a wrapped urllib cause."""
    if isinstance(error, urllib.error.HTTPError):
        return f"HTTP {error.code}: {error.reason}"
    if isinstance(error, urllib.error.URLError):
        error = error.reason
    if isinstance(error, socket.gaierror):
        return f"DNS lookup failed: {error}"
    if isinstance(error, TimeoutError):
        return f"request timed out (timeout: {TIMEOUT} seconds): {error}"
    if isinstance(error, ssl.SSLError):
        return f"TLS connection failed: {error}"
    return f"{type(error).__name__}: {error}"


def try_fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                print(f"error: fetching {url} failed: response exceeds "
                      f"{MAX_BYTES} bytes", file=sys.stderr)
                return None
            body = raw.decode('utf-8', errors='replace')
            if not body.strip():
                print(f"error: fetching {url} failed: empty response", file=sys.stderr)
                return None
            return body
    except (urllib.error.URLError, OSError, http.client.HTTPException) as error:
        print(f"error: fetching {url} failed: {fetch_error_message(error)}",
              file=sys.stderr)
        return None


def looks_like_catalog(text):
    """True when `text` is structured like the catalog: a Markdown H1 as its first
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
    unwrapped into candidates: the data URI of the download link first, then
    the rendered <pre> block. The first candidate structured like the catalog
    is returned. Returns None when no candidate looks like the catalog.
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


def parse_args(argv):
    """Return the paths of the `--file <path>` and `--file=<path>` arguments
    in their order, or None on a usage error, such as any other argument or an
    empty path."""
    paths, args, i = [], argv[1:], 0
    while i < len(args):
        if args[i] == '--file' and i + 1 < len(args):
            path, i = args[i + 1], i + 2
        elif args[i].startswith('--file='):
            path, i = args[i][len('--file='):], i + 1
        else:
            return None
        if not path:
            return None
        paths.append(path)
    return paths


def local_copy_problem(raw):
    """Return why the bytes `raw` of a local copy are not the catalog, or None.
    The checks are those of a download, and the copy must be valid UTF-8."""
    if len(raw) > MAX_BYTES:
        return f"exceeds {MAX_BYTES} bytes"
    try:
        body = raw.decode('utf-8')
    except UnicodeDecodeError:
        return "is not valid UTF-8"
    if not body.strip():
        return "is empty"
    if not looks_like_catalog(body):
        return (f"has no valid catalog (expected an H1 and at least "
                f"{MIN_HEADINGS} trope headings)")
    return None


def read_files(paths):
    """Return the catalog in the local files `paths`, concatenated in the given
    order, or None after the reason on stderr."""
    raw = b''
    for path in paths:
        try:
            with open(path, 'rb') as handle:
                raw += handle.read(MAX_BYTES + 1)
        except OSError as error:
            print(f"error: cannot read {path}: {error.strerror or error}",
                  file=sys.stderr)
            return None
        if len(raw) > MAX_BYTES:
            break
    problem = local_copy_problem(raw)
    if problem:
        print(f"error: the local copy {', '.join(paths)} {problem}",
              file=sys.stderr)
        return None
    return raw.decode('utf-8')


def main(argv):
    paths = parse_args(argv)
    if paths is None:
        print("usage: fetch_tropes.py [--file <path> ...]", file=sys.stderr)
        return 2
    if paths:
        body = read_files(paths)
        if body is None:
            return 1
    else:
        response = try_fetch(VIEWER_URL)
        body = extract_markdown(response)
        if not body:
            reason = ("catalog download failed" if response is None else
                      "response has no valid catalog (expected an H1 and at "
                      f"least {MIN_HEADINGS} trope headings)")
            print(f"error: {reason} from {VIEWER_URL}; pass --tropes=<path> to "
                  "review against a local copy", file=sys.stderr)
            return 1
    sys.stdout.write(body)
    print(describe(body), file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
