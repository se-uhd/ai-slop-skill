#!/usr/bin/env python3
"""check_quotes.py <quotes.json> [--apply] [--sources-dir DIR]

Check that each grounding quote a workflow agent returned occurs in the source
the agent says it read. This is the mechanical half of the anti-fabrication
rule: the agent prompt forbids a quote from memory, and this script enforces
it wherever the source is text the script can read itself.

The quotes JSON is the file `/ai-slop:ground` assembles for insert_grounding.py.
Each key maps to either a quote or a todo, and a quote names its source:

    {
      "smith2020": {"quote": "the exact sentence", "source": "https://..."},
      "lee2019":   {"quote": "another sentence", "source": "sources/lee2019.txt"},
      "jones2019": {"todo": "paywalled"}
    }

For every key with a quote, the source is read and the quote is searched for
after normalization on both sides (whitespace collapsed, typographic quotes and
dashes folded to ASCII, soft hyphens dropped, ligatures expanded, case folded).
One tab-separated line per checked key goes to stdout:

    <key>\\t<verdict>\\t<detail>

Verdicts:
    confirmed      the quote occurs in the source text
    not-in-source  the source was read and the quote does not occur in it
    unverifiable   the source is not text this script can read: a PDF or other
                   binary, a missing `source` field, or a URL that served a
                   non-text content type. The caller checks these by hand.
    unreachable    the source could not be fetched or opened

A local `source` is resolved as given, then under --sources-dir when that is
passed. An http(s) source is fetched (User-Agent set, 20 s timeout, 5 MB cap)
and its HTML is reduced to text before the search.

With --apply, every `not-in-source` key is rewritten in place in the quotes
JSON as {"todo": "unverified", "source": "<the same source>"}, so
insert_grounding.py writes a TODO stub for it instead of the quote. Other keys
are left as they are. A one-line summary is printed to stderr. Exits 0 after a
run, whatever the verdicts, and 2 when the quotes JSON cannot be read or is not
an object.

The script never adds or edits a quote. It only removes one it could not find.
"""
import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "ai-slop-check-quotes/1.0 (+https://github.com/se-uhd/ai-slop-skill)"
TIMEOUT = 20
MAX_BYTES = 5_000_000
TEXT_SUFFIXES = {'.txt', '.text', '.md', '.markdown', '.tex', '.html', '.htm', '.xml', '.xhtml'}
HTML_SUFFIXES = {'.html', '.htm', '.xhtml', '.xml'}

_FOLD = {
    '‘': "'", '’': "'", '‚': "'", '‛': "'",
    '“': '"', '”': '"', '„': '"', '‟': '"',
    '–': '-', '—': '-', '‒': '-', '―': '-', '−': '-',
    ' ': ' ', '…': '...', '­': '',
}
_SCRIPT_RE = re.compile(r'<(script|style)\b.*?</\1\s*>', re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r'<[^>]+>')


def normalize(text):
    """Fold `text` for a tolerant substring comparison."""
    text = unicodedata.normalize('NFKC', text)
    text = ''.join(_FOLD.get(ch, ch) for ch in text)
    text = re.sub(r'-\s*\n\s*', '', text)  # a hyphenated line break inside a word
    return ' '.join(text.split()).casefold()


def html_to_text(markup):
    """Reduce HTML to its text: drop scripts and styles, strip tags, unescape."""
    markup = _SCRIPT_RE.sub(' ', markup)
    return html.unescape(_TAG_RE.sub(' ', markup))


def read_local(path):
    """Return ('text', contents) for a readable text file, ('unverifiable',
    reason) for a binary or unknown format, or ('unreachable', reason)."""
    p = Path(path)
    if not p.is_file():
        return 'unreachable', f'no such file: {path}'
    if p.suffix.lower() not in TEXT_SUFFIXES:
        return 'unverifiable', f'not a text source: {p.suffix.lower() or "no extension"}'
    try:
        data = p.read_bytes()
    except OSError as e:
        return 'unreachable', f'cannot read {path}: {e.strerror or e}'
    if b'\x00' in data[:4096]:
        return 'unverifiable', 'binary content'
    text = data.decode('utf-8', errors='replace')
    if p.suffix.lower() in HTML_SUFFIXES:
        text = html_to_text(text)
    return 'text', text


def fetch_url(url):
    """Return ('text', contents), ('unverifiable', reason), or ('unreachable',
    reason) for an http(s) source."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            ctype = (resp.headers.get('Content-Type') or '').lower()
            data = resp.read(MAX_BYTES + 1)
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 'unreachable', str(e)
    if len(data) > MAX_BYTES:
        return 'unverifiable', f'response over {MAX_BYTES} bytes'
    if not (ctype.startswith('text/') or 'xml' in ctype or 'json' in ctype):
        return 'unverifiable', f'content type {ctype.split(";")[0] or "unknown"}'
    text = data.decode('utf-8', errors='replace')
    if 'html' in ctype or 'xml' in ctype:
        text = html_to_text(text)
    return 'text', text


def load_source(source, sources_dir=None):
    """Dispatch on the source's form: URL, local path, or path under
    sources_dir."""
    if re.match(r'https?://', source, re.IGNORECASE):
        return fetch_url(source)
    if Path(source).is_file() or sources_dir is None:
        return read_local(source)
    under = Path(sources_dir) / source
    if under.is_file():
        return read_local(under)
    return read_local(source)


def check_quote(result, sources_dir=None):
    """Return (verdict, detail) for one quotes-JSON result."""
    quote = result.get('quote')
    if not isinstance(quote, str) or not quote.strip():
        return 'unverifiable', 'empty quote'
    source = result.get('source')
    if not isinstance(source, str) or not source.strip():
        return 'unverifiable', 'no source named'
    kind, payload = load_source(source.strip(), sources_dir)
    if kind != 'text':
        return kind, payload
    if normalize(quote) in normalize(payload):
        return 'confirmed', source
    return 'not-in-source', source


def main(argv):
    p = argparse.ArgumentParser(description="Check grounding quotes against the sources they name.")
    p.add_argument('quotes', help="JSON mapping each key to {quote, source} or {todo}")
    p.add_argument('--apply', action='store_true',
                   help="rewrite each not-in-source key as {todo: unverified} in place")
    p.add_argument('--sources-dir', default=None,
                   help="directory under which a relative local source is also looked up")
    args = p.parse_args(argv[1:])

    try:
        quotes = json.loads(Path(args.quotes).read_text(encoding='utf-8'))
    except OSError as e:
        print(f"error: cannot read {args.quotes!r}: {e.strerror or e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"error: {args.quotes!r} is not valid JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(quotes, dict):
        print(f"error: {args.quotes!r} is not a JSON object", file=sys.stderr)
        return 2

    counts = {'confirmed': 0, 'not-in-source': 0, 'unverifiable': 0, 'unreachable': 0}
    downgraded = 0
    for key, result in quotes.items():
        if not isinstance(result, dict) or 'quote' not in result:
            continue
        verdict, detail = check_quote(result, args.sources_dir)
        counts[verdict] += 1
        print(f"{key}\t{verdict}\t{detail}")
        if verdict == 'not-in-source' and args.apply:
            quotes[key] = {'todo': 'unverified', 'source': result.get('source')}
            downgraded += 1
    if args.apply and downgraded:
        Path(args.quotes).write_text(json.dumps(quotes, indent=2, ensure_ascii=False) + '\n',
                                     encoding='utf-8')
    checked = sum(counts.values())
    summary = (f"checked {checked} quote(s): {counts['confirmed']} confirmed, "
               f"{counts['not-in-source']} not in source, "
               f"{counts['unverifiable']} unverifiable, {counts['unreachable']} unreachable")
    if args.apply:
        summary += f"; {downgraded} downgraded to TODO verify -- unverified"
    print(summary, file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
