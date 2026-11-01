#!/usr/bin/env python3
"""verify_references.py <bibfile> [<bibfile> ...] [--mailto EMAIL] [--dblp DB]

Best-effort check that each BibTeX entry refers to a real publication, by
looking it up in academic databases. An entry with a DOI is resolved online at
CrossRef, and at doi.org when CrossRef does not hold the DOI, which covers the
DOIs that DataCite registers for arXiv and Zenodo. Its title is then looked up
in the local DBLP database so that DBLP's curated year and venue count in the
comparison (the rule layers name DBLP as the canonical record for CS/SE
venues). An entry without a DOI is looked up by title in the local DBLP
database, and online at CrossRef when DBLP has no match. The CrossRef search
sends the title with the first three author names, which rank the right work
first, and asks only for the fields that the comparison reads.

--mailto, which defaults to $CROSSREF_MAILTO, gives CrossRef a contact
address in the query and in the User-Agent. CrossRef then serves the run
from its polite pool, which allows more requests than the public one. A value
without a name before an `@` is not an address that CrossRef accepts, so it is
dropped with a warning.

DBLP lookups never go to the DBLP web API, which rate-limits a long
bibliography. They read the SQLite database that setup_dblp.py builds from the
monthly DBLP dump, at --dblp, else at $AI_SLOP_DBLP, else at ~/dblp/dblp.db.
Without that database the script says so on stderr, with the command that
builds it, and still checks the DOIs. An entry without a DOI that CrossRef does
not hold is then reported `unchecked`, not `not-found`, because DBLP was not
asked. Requests to one host are spaced MIN_INTERVAL apart, and a rate-limit
answer (HTTP 429 or 503) is retried after the wait that the server asks for.
When an online lookup still fails, the entry is reported `unchecked-offline`
and the run still exits 0.

The year and venue comparisons are deliberately lenient, because the strict
forms flagged correct entries. The year matches when it equals any year the databases record
for the work (CrossRef's online-first and print dates, DBLP's year), since a
journal paper legitimately carries either. The venue matches on shared words of
four or more letters. A common SE venue abbreviation (TOSEM, EMSE, ICSE, ...)
is expanded first (VENUE_ABBREVIATIONS). A database abbreviation such as
"Empir. Softw. Eng." matches by word prefix, and an initialism of the words
of the long form (TOSEM for "ACM Transactions on Software Engineering and
Methodology") also counts.

Prints one tab-separated line per entry that is NOT cleanly verified:

    <key>\\t<verdict>\\t<detail>

Verdicts:
    doi-not-found      DOI present, but neither CrossRef nor doi.org knows it
                       (likely fabricated)
    title-mismatch     DOI resolves, but to a different title than the entry
    year-mismatch      record found, but the year differs
    venue-mismatch     record found, but the venue differs
    not-found          no DOI, and neither DBLP nor CrossRef has the title
    unchecked-offline  an online lookup failed (no network, an HTTP error
                       other than 404 that persists after the retries, or an
                       unparseable response)
    unchecked          entry has no DOI and no title to look up, CrossRef does
                       not hold an entry without a DOI and there is no local
                       DBLP database to ask, or the per-run lookup cap was
                       reached

Cleanly verified entries (`ok`) are not printed. A one-line summary is always
printed to stderr, and it names the DBLP database or says that DBLP was not
checked. The run exits 0 when at least one bib file is read (network
reachable or not), and exits 2 when no bib file is given or none of the given
paths could be read, so nothing was checked.

This check is advisory. No verdict asserts that a reference is fabricated. For
an exhaustive,
non-LLM audit of someone else's submission, use the `hallucite` skill instead.

Canonical metadata: where DBLP and CrossRef disagree, prefer DBLP's curated
record for CS/SE venues, except when DBLP holds only a preprint and the
published version is available via the DOI. For an entry without a DOI, a DBLP
title match is used whenever one exists, so the preprint exception is not
applied. Among several DBLP records with the title, the published version
comes before a CoRR preprint.
"""
import argparse
import datetime as dt
import gzip
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Shared BibTeX parsing, the unreadable-path warning, and the location of the
# local DBLP database are in sibling modules.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bib_parse import iter_entries  # noqa: E402
from scan_io import report_unreadable  # noqa: E402
from setup_dblp import ENV_VAR as DBLP_ENV_VAR, db_path as dblp_db_path  # noqa: E402

USER_AGENT = "ai-slop-verify-references/1.0 (+https://github.com/se-uhd/ai-slop-skill)"
TIMEOUT = 10
DOI_ORG_TIMEOUT = 45  # doi.org redirects to the agency, and a DataCite record can take half a minute
MIN_INTERVAL = 0.25  # seconds between two requests to one host
RETRY_STATUSES = {429, 503}  # rate limited or busy, so worth asking again
MAX_RETRIES = 3
MAX_RETRY_DELAY = 30.0
MAX_LOOKUPS = 200  # at most this many entries are looked up per run, at up to two online requests each, and later entries are reported `unchecked`
DBLP_MAX_ROWS = 50  # full-text hits examined per DBLP query
SETUP_SCRIPT = Path(__file__).resolve().parent / 'setup_dblp.py'
CSL_JSON = 'application/vnd.citationstyles.csl+json'
DOI_SAFE = '/:()<>;-._'  # DOI characters sent unescaped, as DOIs such as 10.1016/S0164-1212(00)00029-7 need
# The fields that a CrossRef search returns. Without `select` every hit
# carries its whole reference list.
CROSSREF_SELECT = 'DOI,title,container-title,published,issued,published-print,published-online'
MAX_QUERY_AUTHORS = 3
MAILTO_ENV_VAR = 'CROSSREF_MAILTO'

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
    # Machine learning, NLP, and HCI venues that SE papers on LLMs cite. DBLP
    # gives their short names ("NeurIPS"), a bibliography often the long ones.
    'neurips': 'advances in neural information processing systems',
    'nips': 'advances in neural information processing systems',
    'icml': 'international conference on machine learning',
    'iclr': 'international conference on learning representations',
    'acl': 'annual meeting of the association for computational linguistics',
    'emnlp': 'empirical methods in natural language processing',
    'naacl': 'north american chapter of the association for computational linguistics',
    'kdd': 'knowledge discovery and data mining',
    'chi': 'human factors in computing systems',
    'cscw': 'computer supported cooperative work',
    # DBLP files arXiv preprints under the journal CoRR, and doi.org names
    # arXiv as their publisher.
    'corr': 'computing research repository arxiv',
}


class NetworkError(Exception):
    """A lookup failed because the network was unreachable, the server returned
    an HTTP error other than 404, or the response was not valid JSON."""


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
            'authors': author_names(f.get('author', '')),
        }


def author_names(field):
    """The names in a BibTeX author field as "First Last", without braces
    and without the closing "others"."""
    names = []
    for part in re.split(r'\s+and\s+', re.sub(r'[{}]', '', field or '')):
        part = ' '.join(part.split())
        if not part or part.lower() == 'others':
            continue
        if ',' in part:
            last, first = part.split(',', 1)
            part = f"{first.strip()} {last.strip()}".strip()
        names.append(part)
    return names


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
    """True when `short` is a single token of 3 to 8 letters and its letters
    appear in order among the initials of `long_`'s words."""
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
    """Every year a record carries, i.e., the `years` set together with `year`."""
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

_last_request = {}


def _pace(url):
    """Wait until MIN_INTERVAL has passed since the last request to the same
    host. CrossRef answers a burst from its public pool with HTTP 429."""
    host = urllib.parse.urlsplit(url).netloc
    wait = _last_request.get(host, 0.0) + MIN_INTERVAL - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request[host] = time.monotonic()


def _retry_delay(err, attempt):
    """Seconds to wait before retrying after `err`: the Retry-After header
    when it gives a number, else 2, 4, 8 seconds, at most MAX_RETRY_DELAY."""
    header = (err.headers.get('Retry-After') or '').strip() if err.headers else ''
    delay = float(header) if header.isdigit() else 2.0 ** (attempt + 1)
    return min(delay, MAX_RETRY_DELAY)


def is_contact(value):
    """True when CrossRef reads `value` as a contact address, i.e., a
    non-empty name before an `@`. Only such an address puts the caller in
    the polite pool."""
    value = value or ''
    return '@' in value and bool(value.split('@', 1)[0].strip())


def _user_agent(mailto=None):
    """USER_AGENT, with the contact address in it when there is one, as
    CrossRef asks of a caller in the polite pool."""
    return USER_AGENT[:-1] + f"; mailto:{mailto})" if mailto else USER_AGENT


def _body(resp):
    """The response body, decompressed when the server says it is gzipped.
    CrossRef compresses a large answer even when the client did not ask."""
    raw = resp.read()
    encoding = (getattr(resp, 'headers', None) or {}).get('Content-Encoding') or ''
    if 'gzip' in encoding.lower():
        try:
            return gzip.decompress(raw)
        except OSError:
            return raw
    return raw


def _get_json(url, headers=None, timeout=TIMEOUT):
    """GET `url` as JSON. Returns None on HTTP 404, retries HTTP 429 and 503
    up to MAX_RETRIES times, and raises NetworkError on any other failure."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, **(headers or {})})
    for attempt in range(MAX_RETRIES + 1):
        _pace(url)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(_body(resp).decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                time.sleep(_retry_delay(e, attempt))
                continue
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
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe=DOI_SAFE)
    if mailto:
        url += '?mailto=' + urllib.parse.quote(mailto)
    data = _get_json(url, {'User-Agent': _user_agent(mailto)})
    return None if data is None else _crossref_record(data.get('message', {}))


def crossref_by_title(title, mailto=None, authors=()):
    """CrossRef records for a title, asked together with the first
    MAX_QUERY_AUTHORS author names, which rank the right work first. A search
    that answers 404 or without a result list has not answered, so it raises
    NetworkError rather than return no match."""
    query = ' '.join([title, *list(authors)[:MAX_QUERY_AUTHORS]])
    params = {'query.bibliographic': query, 'rows': '5', 'select': CROSSREF_SELECT}
    if mailto:
        params['mailto'] = mailto
    data = _get_json('https://api.crossref.org/works?' + urllib.parse.urlencode(params),
                     {'User-Agent': _user_agent(mailto)})
    message = (data or {}).get('message')
    if not isinstance(message, dict) or 'items' not in message:
        raise NetworkError('CrossRef search returned no result list')
    return [_crossref_record(it) for it in message.get('items') or []]


def _first(value):
    """CSL JSON gives a title as a string or as a list of strings."""
    if isinstance(value, list):
        return value[0] if value else ''
    return value or ''


def _csl_record(data):
    """Project the CSL JSON that doi.org returns into {title, venue, year,
    years, doi}. A preprint or a dataset has no container, so its publisher
    (arXiv, Zenodo) is the venue."""
    years = []
    for k in ('issued', 'published', 'published-print', 'published-online'):
        dp = (data.get(k) or {}).get('date-parts') or []
        if dp and dp[0] and dp[0][0] is not None:
            y = str(dp[0][0])
            if y not in years:
                years.append(y)
    return {
        'title': _first(data.get('title')),
        'venue': _first(data.get('container-title')) or _first(data.get('publisher')),
        'year': years[0] if years else '',
        'years': set(years),
        'doi': data.get('DOI', ''),
        'source': 'doi.org',
    }


def doi_org_by_doi(doi):
    """Resolve a DOI at doi.org, which answers with the metadata of whichever
    agency registered it (CrossRef, DataCite, mEDRA, ...). None when doi.org
    does not know the DOI."""
    data = _get_json('https://doi.org/' + urllib.parse.quote(doi, safe=DOI_SAFE),
                     {'Accept': CSL_JSON}, timeout=DOI_ORG_TIMEOUT)
    return None if data is None else _csl_record(data)


def lookup_doi(doi, mailto=None):
    """CrossRef first, then doi.org for a DOI that CrossRef does not hold,
    such as the DataCite DOIs of arXiv (10.48550) and Zenodo (10.5281)."""
    rec = crossref_by_doi(doi, mailto)
    return rec if rec is not None else doi_org_by_doi(doi)


# ---------- local DBLP database ----------

def _index_tokens(text):
    """The words of a title as the FTS5 index stores them: lowercase, with
    diacritics removed, and without LaTeX markup."""
    text = re.sub(r'\\[\'"`^~=.]', '', text)        # accent commands: {\"u} -> {u}
    text = re.sub(r'\\[A-Za-z]+\*?', ' ', text)      # command names: \emph{X} -> {X}
    text = re.sub(r'\\.|[{}$]', '', text)
    nfkd = unicodedata.normalize('NFKD', text)
    folded = ''.join(c for c in nfkd if not unicodedata.combining(c)).lower()
    return re.findall(r'[^\W_]+', folded)


def _doi_of(ee):
    m = re.search(r'doi\.org/(10\.\S+)', ee or '')
    return m.group(1) if m else ''


class LocalDblp:
    """The SQLite database that setup_dblp.py builds from the DBLP dump,
    opened read-only. `error` says why it cannot be used, and is empty when
    it can."""

    def __init__(self, path):
        self.path = Path(path)
        self.con = None
        self.info = {}
        self.error = ''
        if not self.path.is_file():
            self.error = f"no local DBLP database at {self.path}"
            return
        try:
            con = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True)
            self.info = dict(con.execute('SELECT key, value FROM metadata'))
            con.execute('SELECT rowid FROM publications_fts LIMIT 1').fetchall()
        except sqlite3.Error as e:
            self.error = f"{self.path} is not a DBLP database that setup_dblp.py can read ({e})"
            return
        self.con = con

    def describe(self):
        stamp = self.info.get('last_updated', '')
        built = dt.date.fromtimestamp(int(stamp)).isoformat() if stamp.isdigit() else 'on an unknown date'
        count = self.info.get('publication_count', '')
        size = f"{int(count):,} publications, " if count.isdigit() else ''
        return f"local DBLP database {self.path} ({size}built {built})"

    def _query(self, match):
        try:
            return self.con.execute(
                'SELECT p.title, p.year, p.venue, p.ee FROM publications_fts f '
                'JOIN publications p ON p.id = f.rowid '
                'WHERE publications_fts MATCH ? LIMIT ?', (match, DBLP_MAX_ROWS)).fetchall()
        except sqlite3.Error:
            return []

    def by_title(self, title):
        """DBLP records whose title matches `title`, best first. The title is
        asked as a phrase, with a hyphen read as part of the word and as a
        space, and then as a set of words when no phrase matches. A published
        record comes before a CoRR preprint."""
        queries = []
        for variant in (title.replace('-', ''), title.replace('-', ' ')):
            tokens = _index_tokens(variant)
            if tokens:
                q = '"' + ' '.join(tokens) + '"'
                if q not in queries:
                    queries.append(q)
        rows = []
        for q in queries:
            rows += self._query(q)
        if not any(title_match(title, r[0]) for r in rows):
            tokens = _index_tokens(title.replace('-', ' '))
            if tokens:
                rows += self._query(' AND '.join(f'"{t}"' for t in tokens))
        records, seen = [], set()
        for t, year, venue, ee in rows:
            if (t, year, venue) in seen or not title_match(title, t):
                continue
            seen.add((t, year, venue))
            records.append({'title': t, 'venue': venue or '', 'year': str(year or ''),
                            'doi': _doi_of(ee), 'source': 'dblp'})
        records.sort(key=lambda r: (_tokens(r['title']) != _tokens(title), r['venue'] == 'CoRR'))
        return records


def missing_dblp_notice(dblp):
    """The stderr text that says DBLP was not checked and how to build the
    database."""
    rebuild = ' --update' if dblp.path.exists() else ''
    return '\n'.join([
        f"DBLP: {dblp.error}, so DBLP was not checked.",
        "  Download the monthly DBLP dump (about 1.1 GB) and build the database "
        "(about 4 GB, five to ten minutes) with:",
        f'    python3 "{SETUP_SCRIPT}" --out "{dblp.path}"{rebuild}',
        f"  To use a database in another place, set {DBLP_ENV_VAR} or pass --dblp.",
    ])


# ---------- checking entries ----------

def _merge_curated(rec, curated):
    """Fold DBLP's curated record into a CrossRef one: Both years are accepted
    and both venue strings count in the venue comparison."""
    merged = dict(rec)
    merged['years'] = _record_years(rec) | _record_years(curated)
    venues = [v for v in (rec.get('venue', ''), curated.get('venue', '')) if v]
    merged['venue'] = ' '.join(venues)
    merged['source'] = 'crossref+dblp'
    return merged


def verify_entry(entry, fetch_doi, fetch_dblp, fetch_title):
    """Resolve one entry to a verdict using the supplied fetchers (injected so
    this is testable without network). A DOI resolves at CrossRef or doi.org,
    and DBLP's record for the same title is then merged in so its curated year
    and venue count. Without a DOI, DBLP is asked first and CrossRef only when
    DBLP has no match, so a DBLP title match is used whenever one exists.
    `fetch_dblp` is None when there is no local DBLP database."""
    doi = (entry.get('doi') or '').strip()
    title = (entry.get('title') or '').strip()
    if doi:
        try:
            rec = fetch_doi(doi)
        except NetworkError:
            return ('unchecked-offline', f"doi={doi}")
        if rec is None:
            return ('doi-not-found', f"doi={doi}")
        if title and fetch_dblp:
            try:
                curated = best_title_match(title, fetch_dblp(title))
            except (NetworkError, sqlite3.Error):
                curated = None
            if curated:
                rec = _merge_curated(rec, curated)
        return compare_entry(entry, rec)
    if not title:
        return ('unchecked', 'no doi or title')
    try:
        best = best_title_match(title, fetch_dblp(title)) if fetch_dblp else None
        if best is None:
            best = best_title_match(title, fetch_title(title))
    except NetworkError:
        return ('unchecked-offline', f"title={title[:40]}")
    if best is None:
        if not fetch_dblp:
            return ('unchecked', f"not in CrossRef, and DBLP was not checked: title={title[:60]}")
        return ('not-found', f"title={title[:60]}")
    return compare_entry(entry, best)


def _cache_key(entry):
    doi = (entry.get('doi') or '').strip().lower()
    if doi:
        return ('doi', doi)
    return ('title', ' '.join(_tokens(entry.get('title', ''))))


def main(argv):
    p = argparse.ArgumentParser(description="Verify BibTeX references against CrossRef, doi.org, and DBLP.")
    p.add_argument('bibfiles', nargs='+')
    p.add_argument('--mailto', default=os.environ.get(MAILTO_ENV_VAR, '').strip(),
                   help=f"contact email for the CrossRef polite pool (default: ${MAILTO_ENV_VAR})")
    p.add_argument('--dblp', default=None,
                   help=f"local DBLP database (default: ${DBLP_ENV_VAR}, else ~/dblp/dblp.db)")
    args = p.parse_args(argv[1:])
    mailto = args.mailto if is_contact(args.mailto) else ''
    if args.mailto and not mailto:
        print(f"warning: {args.mailto!r} is not an email address, so CrossRef is asked without one",
              file=sys.stderr)

    dblp = LocalDblp(dblp_db_path(args.dblp))
    if dblp.error:
        print(missing_dblp_notice(dblp), file=sys.stderr)
    fetch_dblp = dblp.by_title if dblp.con else None

    def fetch_doi(d):
        return lookup_doi(d, mailto)

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
                authors = entry.get('authors') or []

                def fetch_title(t, authors=authors):
                    return crossref_by_title(t, mailto, authors)
                verdict, detail = verify_entry(entry, fetch_doi, fetch_dblp, fetch_title)
                cache[ckey] = (verdict, detail)
            if verdict != 'ok':
                flagged += 1
                print(f"{entry['key']}\t{verdict}\t{detail}")
    summary = (f"checked {checked} reference(s), {flagged} flagged, "
               f"{lookups} lookup(s)")
    if capped:
        summary += f"; {capped} skipped after the {MAX_LOOKUPS}-lookup cap"
    summary += f"; {dblp.describe()}" if dblp.con else "; DBLP not checked (no local database)"
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
