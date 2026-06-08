#!/usr/bin/env python3
"""verify_references.py <bibfile> [<bibfile> ...] [--mailto EMAIL]

Best-effort check that each BibTeX entry refers to a real publication, by
looking it up in academic databases. Online-first: it queries CrossRef (by DOI,
then by title) and DBLP (by title). When there is no network, the affected
entries are reported `unchecked-offline` and the run still exits 0, the same way
fetch_tropes.py falls back to the bundled snapshot.

Prints one tab-separated line per entry that is NOT cleanly verified:

    <key>\\t<verdict>\\t<detail>

Verdicts:
    doi-not-found      DOI present but CrossRef has no record (likely fabricated)
    title-mismatch     DOI resolves, but to a different title than the entry
    year-mismatch      record found, but the year differs
    venue-mismatch     record found, but the venue differs
    not-found          no DOI and no database match for the title
    unchecked-offline  a lookup could not run (no network)
    unchecked          entry has no DOI and no title to look up, or the per-run
                       lookup cap was reached

Cleanly verified entries (`ok`) are not printed. A one-line summary is always
printed to stderr. The run exits 0 when at least one bib file is read (network
reachable or not), and exits 2 only when none of the given paths could be read,
so nothing was checked.

This is advisory. It confirms, or fails to confirm; it never asserts a reference
is fabricated except where a DOI provably does not resolve. For an exhaustive,
non-LLM audit of someone else's submission, use the `hallucite` skill instead.

Canonical metadata: where DBLP and CrossRef disagree, prefer DBLP's curated
record for CS/SE venues, except when DBLP holds only a preprint and the
published version is available via the DOI.

Future (not yet wired): an optional local DBLP dump ($AI_SLOP_DBLP) for offline
and faster bulk checks; richer venue-abbreviation matching.
"""
import argparse
import errno
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Reuse the brace-counting entry splitter from the sibling field checker.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_bib_fields import find_entry_blocks  # noqa: E402

USER_AGENT = "ai-slop-verify-references/1.0 (+https://github.com/se-uhd/ai-slop-skill)"
TIMEOUT = 10
MAX_LOOKUPS = 200  # bound network calls per run; excess entries report `unchecked`
SKIP_TYPES = {'string', 'preamble', 'comment'}


class NetworkError(Exception):
    """A lookup could not complete because the network was unreachable."""


# ---------- BibTeX value parsing ----------

_FIELD_RE = re.compile(r'(\w+)\s*=\s*', re.IGNORECASE)


def _clean(raw):
    raw = raw.strip().rstrip(',').strip()
    if len(raw) >= 2 and ((raw[0] == '{' and raw[-1] == '}') or (raw[0] == '"' and raw[-1] == '"')):
        raw = raw[1:-1]
    return re.sub(r'\s+', ' ', raw.replace('{', '').replace('}', '')).strip()


def parse_entry_values(body):
    """Return (key, {field: value}) for one entry body. The first top-level
    comma ends the key; field values may be brace-, quote-, or bare-delimited."""
    depth = 0
    key_end = None
    for i, c in enumerate(body):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif c == ',' and depth == 0:
            key_end = i
            break
    if key_end is None:
        return body.strip(), {}
    key = body[:key_end].strip()
    rest = body[key_end + 1:]
    fields = {}
    i, n = 0, len(rest)
    while i < n:
        m = _FIELD_RE.match(rest, i)
        if not m:
            i += 1
            continue
        name = m.group(1).lower()
        j = m.end()
        if j < n and rest[j] == '{':
            depth, k = 0, j
            while k < n:
                if rest[k] == '{':
                    depth += 1
                elif rest[k] == '}':
                    depth -= 1
                    if depth == 0:
                        k += 1
                        break
                k += 1
            value = rest[j:k]
        elif j < n and rest[j] == '"':
            k = j + 1
            while k < n and rest[k] != '"':
                k += 1
            k += 1
            value = rest[j:k]
        else:
            k = j
            while k < n and rest[k] != ',':
                k += 1
            value = rest[j:k]
        fields[name] = _clean(value)
        i = k
    return key, fields


def bib_entries(text):
    """Yield a normalized dict per entry: key, type, doi, title, year, venue."""
    for etype, body in find_entry_blocks(text):
        if etype in SKIP_TYPES:
            continue
        key, f = parse_entry_values(body)
        yield {
            'key': key,
            'type': etype,
            'doi': f.get('doi', ''),
            'title': f.get('title', ''),
            'year': f.get('year', ''),
            'venue': f.get('journal') or f.get('booktitle') or '',
        }


# ---------- normalization + comparison (pure, no network) ----------

def _tokens(s):
    return [t for t in re.sub(r'[^a-z0-9 ]', ' ', (s or '').lower()).split() if t]


def title_match(a, b):
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= 0.7


def _venue_match(a, b):
    ta = {t for t in _tokens(a) if len(t) >= 4}
    tb = {t for t in _tokens(b) if len(t) >= 4}
    if not ta or not tb:
        return True  # cannot tell (e.g., an abbreviation) — do not flag
    return bool(ta & tb)


def compare_entry(entry, record):
    """Pure comparison of a bib entry against a database record dict
    ({title, year, venue}). Returns (verdict, detail)."""
    if not title_match(entry.get('title', ''), record.get('title', '')):
        return ('title-mismatch',
                f"entry={entry.get('title', '')[:60]!r} db={record.get('title', '')[:60]!r}")
    ey = str(entry.get('year', '')).strip()
    ry = str(record.get('year', '')).strip()
    if ey and ry and ey != ry:
        return ('year-mismatch', f"entry={ey} db={ry}")
    ev, rv = entry.get('venue', ''), record.get('venue', '')
    if ev and rv and not _venue_match(ev, rv):
        return ('venue-mismatch', f"entry={ev[:40]!r} db={rv[:40]!r}")
    return ('ok', '')


def best_title_match(title, candidates):
    for rec in candidates:
        if title_match(title, rec.get('title', '')):
            return rec
    return None


# ---------- fetch layer (network) ----------

def _get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise NetworkError(f"HTTP {e.code} for {url}")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise NetworkError(str(e))


def _crossref_record(msg):
    year = ''
    for k in ('published', 'issued', 'published-print', 'published-online'):
        dp = (msg.get(k) or {}).get('date-parts') or []
        if dp and dp[0]:
            year = str(dp[0][0])
            break
    return {
        'title': (msg.get('title') or [''])[0],
        'venue': (msg.get('container-title') or [''])[0],
        'year': year,
        'doi': msg.get('DOI', ''),
        'source': 'crossref',
    }


def crossref_by_doi(doi, mailto=None):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi)
    if mailto:
        url += '?mailto=' + urllib.parse.quote(mailto)
    data = _get_json(url)
    return None if data is None else _crossref_record(data.get('message', {}))


def crossref_by_title(title, mailto=None):
    params = {'query.bibliographic': title, 'rows': '5'}
    if mailto:
        params['mailto'] = mailto
    data = _get_json('https://api.crossref.org/works?' + urllib.parse.urlencode(params))
    if not data:
        return []
    return [_crossref_record(it) for it in data.get('message', {}).get('items', [])]


def dblp_by_title(title):
    url = 'https://dblp.org/search/publ/api?' + urllib.parse.urlencode(
        {'q': title, 'format': 'json', 'h': '5'})
    data = _get_json(url)
    if not data:
        return []
    hits = (((data.get('result') or {}).get('hits') or {}).get('hit')) or []
    out = []
    for h in hits:
        info = h.get('info', {})
        out.append({
            'title': info.get('title', ''),
            'venue': info.get('venue', ''),
            'year': str(info.get('year', '')),
            'doi': info.get('doi', ''),
            'source': 'dblp',
        })
    return out


# ---------- orchestration ----------

def verify_entry(entry, fetch_doi, fetch_dblp, fetch_title):
    """Resolve one entry to a verdict using the supplied fetchers (injected so
    this is testable without network). DBLP is consulted before CrossRef title
    search, so its curated record wins on CS/SE venues."""
    doi = (entry.get('doi') or '').strip()
    if doi:
        try:
            rec = fetch_doi(doi)
        except NetworkError:
            return ('unchecked-offline', f"doi={doi}")
        if rec is None:
            return ('doi-not-found', f"doi={doi}")
        return compare_entry(entry, rec)
    title = (entry.get('title') or '').strip()
    if not title:
        return ('unchecked', 'no doi or title')
    try:
        candidates = list(fetch_dblp(title)) + list(fetch_title(title))
    except NetworkError:
        return ('unchecked-offline', f"title={title[:40]}")
    best = best_title_match(title, candidates)
    if best is None:
        return ('not-found', f"title={title[:60]}")
    return compare_entry(entry, best)


def _cache_key(entry):
    doi = (entry.get('doi') or '').strip().lower()
    if doi:
        return ('doi', doi)
    return ('title', ' '.join(_tokens(entry.get('title', ''))))


def report_unreadable(path, err):
    """Print a friendly stderr warning for an unreadable path. Truncates the
    path so a runaway argument cannot flood the terminal, and adds a hint when
    the argument looks like several paths collapsed into one (the classic
    unquoted-variable-in-zsh mistake)."""
    shown = str(path)
    if len(shown) > 80:
        shown = shown[:77] + '...'
    print(f"warning: cannot read {shown!r}: {err.strerror or err}", file=sys.stderr)
    if getattr(err, 'errno', None) == errno.ENAMETOOLONG or '\n' in str(path):
        print(
            "  hint: this argument looks like several paths joined into one. "
            "Pass each file as a separate argument (in zsh, unquoted variables "
            "are not split on spaces; use an array or xargs).",
            file=sys.stderr,
        )


def main(argv):
    p = argparse.ArgumentParser(description="Verify BibTeX references against CrossRef and DBLP.")
    p.add_argument('bibfiles', nargs='+')
    p.add_argument('--mailto', default=None,
                   help="contact email for the CrossRef polite pool (recommended)")
    args = p.parse_args(argv[1:])

    def fetch_doi(d):
        return crossref_by_doi(d, args.mailto)

    def fetch_title(t):
        return crossref_by_title(t, args.mailto)

    cache = {}
    checked = flagged = lookups = capped = files_read = 0
    for path in args.bibfiles:
        try:
            text = Path(path).read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            report_unreadable(path, e)
            continue
        files_read += 1
        try:
            entries = list(bib_entries(text))
        except ValueError as e:
            print(f"{path}: {e}", file=sys.stderr)
            continue
        for entry in entries:
            checked += 1
            ckey = _cache_key(entry)
            needs_lookup = bool((entry.get('doi') or '').strip() or (entry.get('title') or '').strip())
            if ckey in cache:
                verdict, detail = cache[ckey]
            elif needs_lookup and lookups >= MAX_LOOKUPS:
                capped += 1
                print(f"{entry['key']}\tunchecked\tlookup cap {MAX_LOOKUPS} reached")
                continue
            else:
                if needs_lookup:
                    lookups += 1
                verdict, detail = verify_entry(entry, fetch_doi, dblp_by_title, fetch_title)
                cache[ckey] = (verdict, detail)
            if verdict != 'ok':
                flagged += 1
                print(f"{entry['key']}\t{verdict}\t{detail}")
    summary = (f"checked {checked} reference(s), {flagged} flagged, "
               f"{lookups} lookup(s)")
    if capped:
        summary += f"; {capped} skipped after the {MAX_LOOKUPS}-lookup cap"
    print(summary, file=sys.stderr)
    if files_read == 0:
        print(
            f"error: none of the {len(args.bibfiles)} bib file(s) given could be read; "
            "nothing was checked",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
