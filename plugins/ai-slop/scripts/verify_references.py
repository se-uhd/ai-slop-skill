#!/usr/bin/env python3
"""verify_references.py <bibfile> [<bibfile> ...] [--mailto EMAIL]

Best-effort check that each BibTeX entry refers to a real publication, by
looking it up in academic databases. Online-first: an entry with a DOI is
resolved at CrossRef, and its title is then looked up at DBLP so DBLP's
curated year and venue take part in the comparison (the rule layers name DBLP
as the canonical record for CS/SE venues). An entry without a DOI is looked up
by title at DBLP and then CrossRef. When there is no network, the affected
entries are reported `unchecked-offline` and the run still exits 0.

Two comparisons are deliberately lenient, because the strict form flagged
correct entries. The year matches when it equals any year the databases record
for the work (CrossRef's online-first and print dates, DBLP's year), since a
journal paper legitimately carries either. The venue matches on shared words of
four or more letters, where a common SE venue abbreviation (TOSEM, EMSE, ICSE,
...) is expanded first (VENUE_ABBREVIATIONS), a database abbreviation such as
"Empir. Softw. Eng." matches by word prefix, and an initialism of the long
form's words (TOSEM for "ACM Transactions on Software Engineering and
Methodology") also counts.

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

This check is advisory. It confirms, or fails to confirm. It never asserts a reference
is fabricated except where a DOI provably does not resolve. For an exhaustive,
non-LLM audit of someone else's submission, use the `hallucite` skill instead.

Canonical metadata: where DBLP and CrossRef disagree, prefer DBLP's curated
record for CS/SE venues, except when DBLP holds only a preprint and the
published version is available via the DOI. In code that means the years of
both are accepted and the venues of both are compared against the entry.

Future (not yet wired): an optional local DBLP dump ($AI_SLOP_DBLP) for offline
and faster bulk checks; richer venue-abbreviation matching.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Shared BibTeX parsing + the unreadable-path warning are in sibling modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bib_parse import iter_entries  # noqa: E402
from scan_io import report_unreadable  # noqa: E402

USER_AGENT = "ai-slop-verify-references/1.0 (+https://github.com/se-uhd/ai-slop-skill)"
TIMEOUT = 10
MAX_LOOKUPS = 200  # bound network calls per run; excess entries report `unchecked`

# Common software-engineering venue abbreviations, expanded before venues are
# compared. A recall aid for the venue check, not a canonical list.
VENUE_ABBREVIATIONS = {
    'tse': 'ieee transactions on software engineering',
    'tosem': 'acm transactions on software engineering and methodology',
    'emse': 'empirical software engineering',
    'jss': 'journal of systems and software',
    'ist': 'information and software technology',
    'icse': 'international conference on software engineering',
    'fse': 'foundations of software engineering',
    'esec': 'european software engineering conference',
    'ase': 'automated software engineering',
    'msr': 'mining software repositories',
    'icsme': 'international conference on software maintenance and evolution',
    'saner': 'software analysis evolution and reengineering',
    'issta': 'international symposium on software testing and analysis',
    'icpc': 'international conference on program comprehension',
    'esem': 'empirical software engineering and measurement',
    'ease': 'evaluation and assessment in software engineering',
    'icst': 'software testing verification and validation',
    'csur': 'acm computing surveys',
    'oopsla': 'object oriented programming systems languages and applications',
    'chase': 'cooperative and human aspects of software engineering',
    'models': 'model driven engineering languages and systems',
    'icsa': 'international conference on software architecture',
    'seams': 'software engineering for adaptive and self managing systems',
    'msr': 'mining software repositories',
}


class NetworkError(Exception):
    """A lookup could not complete because the network was unreachable."""


# ---------- BibTeX entry projection ----------


def bib_entries(text):
    """Yield a normalized dict per entry: key, type, doi, title, year, venue.
    The brace-counting splitter and field-value parser are in bib_parse.py."""
    for key, etype, f in iter_entries(text):
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


def _venue_tokens(s):
    """Words of four or more letters in a venue string, with a known
    abbreviation replaced by the words of its expansion."""
    out = set()
    for t in _tokens(s):
        expansion = VENUE_ABBREVIATIONS.get(t)
        if expansion:
            out.update(w for w in _tokens(expansion) if len(w) >= 4)
        elif len(t) >= 4:
            out.add(t)
    return out


def _words_overlap(ta, tb):
    """True when a word of one set equals, or is a prefix of, a word of the
    other ("empir" against "empirical", as DBLP abbreviates)."""
    for a in ta:
        for b in tb:
            if a == b or a.startswith(b) or b.startswith(a):
                return True
    return False


def _is_initialism(short, long_):
    """True when `short` is a single 3- to 8-letter token whose letters appear
    in order among the initials of `long_`'s words."""
    st = _tokens(short)
    if len(st) != 1 or not st[0].isalpha() or not 3 <= len(st[0]) <= 8:
        return False
    initials = ''.join(w[0] for w in _tokens(long_))
    it = iter(initials)
    return all(ch in it for ch in st[0])


def _venue_match(a, b):
    ta, tb = _venue_tokens(a), _venue_tokens(b)
    if not ta or not tb:
        return True  # cannot tell (e.g., an abbreviation), so do not flag
    if _words_overlap(ta, tb):
        return True
    return _is_initialism(a, b) or _is_initialism(b, a)


def _record_years(record):
    """Every year a record carries: the `years` set when present, else `year`."""
    years = {str(y).strip() for y in (record.get('years') or []) if str(y).strip()}
    single = str(record.get('year', '')).strip()
    if single:
        years.add(single)
    return years


def compare_entry(entry, record):
    """Pure comparison of a bib entry against a database record dict
    ({title, year, venue}, optionally {years}). Returns (verdict, detail)."""
    if not title_match(entry.get('title', ''), record.get('title', '')):
        return ('title-mismatch',
                f"entry={entry.get('title', '')[:60]!r} db={record.get('title', '')[:60]!r}")
    ey = str(entry.get('year', '')).strip()
    ry = _record_years(record)
    if ey and ry and ey not in ry:
        return ('year-mismatch', f"entry={ey} db={'/'.join(sorted(ry))}")
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
    """Project a CrossRef work into {title, venue, year, years, doi}. `years`
    holds every publication year the record carries (online-first and print
    often differ by one), and `year` the first of them."""
    years = []
    for k in ('published', 'issued', 'published-print', 'published-online'):
        dp = (msg.get(k) or {}).get('date-parts') or []
        if dp and dp[0] and dp[0][0] is not None:
            y = str(dp[0][0])
            if y not in years:
                years.append(y)
    return {
        'title': (msg.get('title') or [''])[0],
        'venue': (msg.get('container-title') or [''])[0],
        'year': years[0] if years else '',
        'years': set(years),
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

def _merge_curated(rec, curated):
    """Fold DBLP's curated record into a CrossRef one: both years are accepted
    and both venue strings take part in the venue comparison."""
    merged = dict(rec)
    merged['years'] = _record_years(rec) | _record_years(curated)
    venues = [v for v in (rec.get('venue', ''), curated.get('venue', '')) if v]
    merged['venue'] = ' '.join(venues)
    merged['source'] = 'crossref+dblp'
    return merged


def verify_entry(entry, fetch_doi, fetch_dblp, fetch_title):
    """Resolve one entry to a verdict using the supplied fetchers (injected so
    this is testable without network). A DOI resolves at CrossRef, and DBLP's
    record for the same title is then merged in so its curated year and venue
    count. Without a DOI, DBLP is consulted before CrossRef title search, so
    its curated record wins on CS/SE venues."""
    doi = (entry.get('doi') or '').strip()
    title = (entry.get('title') or '').strip()
    if doi:
        try:
            rec = fetch_doi(doi)
        except NetworkError:
            return ('unchecked-offline', f"doi={doi}")
        if rec is None:
            return ('doi-not-found', f"doi={doi}")
        if title:
            try:
                curated = best_title_match(title, fetch_dblp(title))
            except NetworkError:
                curated = None
            if curated:
                rec = _merge_curated(rec, curated)
        return compare_entry(entry, rec)
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
