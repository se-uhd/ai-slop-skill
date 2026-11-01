#!/usr/bin/env python3
"""setup_dblp.py [--out DB] [--dump DUMP] [--update] [--limit N]

Download the monthly DBLP snapshot and build the local database that
verify_references.py reads for every DBLP lookup. The reference check never
queries the DBLP web API, which rate-limits a review of a long bibliography,
so without this database DBLP is not checked at all.

Location: the database is at --out, else at $AI_SLOP_DBLP, else at
~/dblp/dblp.db, and the dump is saved beside it as dblp.xml.gz. verify_references.py
resolves the same way, so set $AI_SLOP_DBLP once to keep both somewhere else.
A database that another tool built with the same schema (tables
`publications`, `authors`, `publication_authors`, and `metadata`, plus the
FTS5 index `publications_fts`) works as well, without a rebuild.

Steps:
  1. Download. dblp publishes a snapshot on the first of each month at Schloss
     Dagstuhl (DROPS, CC0, https://doi.org/10.4230/dblp.xml), with an MD5
     checksum beside it, and releases it a few weeks later. The script takes
     the newest release of the last six months, reads its checksum, streams
     the dump to a `.part` file, and keeps it only when the checksum matches
     and the file starts with the gzip header. When no checksum can be read,
     it says so and relies on the gzip header alone. The download is about 1.1 GB. An existing dump is reused
     unless --update is passed, and --dump names a dump that is already on
     disk.
  2. Build. The dump is about 4.5 GB of XML with about 8.7 million
     publications. It is parsed as a stream into SQLite, with a full-text
     index on the titles built once at the end. The database is about 4 GB,
     and the build takes five to ten minutes. It is written to a `.part`
     file and moved into place only when it is complete.

The dump declares HTML entities such as `&uuml;` in an external DTD that an
XML parser without that DTD rejects. They are replaced by numeric character
references in the byte stream before the parser reads it, so an author name
with a diacritic keeps its letters. A build in which no author name carries a
non-ASCII character dropped them, and it is refused.

Options:
  --out DB      the database to build (default: $AI_SLOP_DBLP, else ~/dblp/dblp.db)
  --dump DUMP   build from this dump instead of downloading one
  --update      download the newest snapshot even when a dump exists, and
                replace an existing database
  --limit N     stop after N publications (a quick test build)

Exit codes: 0 when the database is in place (built now or already there), 1
when the download or the build failed, 2 on a usage error.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import html.entities
import io
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ENV_VAR = 'AI_SLOP_DBLP'
DEFAULT_DB = Path.home() / 'dblp' / 'dblp.db'
SNAPSHOT_BASE = 'https://drops.dagstuhl.de/storage/artifacts/dblp/xml'
LOOKBACK_MONTHS = 6
USER_AGENT = 'ai-slop-setup-dblp/1.0 (+https://github.com/se-uhd/ai-slop-skill)'

# The record types that are publications. A `www` record is the homepage of a
# person, whose name would otherwise enter the title index.
KINDS = ('article', 'inproceedings', 'proceedings', 'book', 'incollection',
         'phdthesis', 'mastersthesis')
VENUE_OF = {'article': 'journal', 'inproceedings': 'booktitle', 'incollection': 'booktitle',
            'proceedings': 'booktitle', 'book': 'publisher', 'phdthesis': 'school',
            'mastersthesis': 'school'}

SCHEMA = """
CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE publications (
    id INTEGER PRIMARY KEY, key TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
    year INTEGER, venue TEXT, ee TEXT, kind TEXT, volume TEXT, number TEXT, pages TEXT);
CREATE TABLE publication_authors (
    pub_id INTEGER NOT NULL, author_id INTEGER NOT NULL, PRIMARY KEY (pub_id, author_id));
"""
SCHEMA_VERSION = '3'

ENTITY_RE = re.compile(rb'&([A-Za-z][A-Za-z0-9]{1,31});')
XML_ENTITIES = {b'amp', b'lt', b'gt', b'quot', b'apos'}


def db_path(arg=None):
    """The database location: `arg`, else $AI_SLOP_DBLP, else ~/dblp/dblp.db."""
    if arg:
        return Path(arg).expanduser()
    env = os.environ.get(ENV_VAR)
    return Path(env).expanduser() if env else DEFAULT_DB


# ---------- download ----------

def snapshot_url(day):
    """The release dated the first of the month of `day`."""
    return f"{SNAPSHOT_BASE}/{day.year}/dblp-{day.year:04d}-{day.month:02d}-01.xml.gz"


def months_back(today, n):
    year, month = today.year, today.month - n
    while month <= 0:
        year, month = year - 1, month + 12
    return dt.date(year, month, 1)


def _open(url, method='GET'):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT}, method=method)
    return urllib.request.urlopen(req, timeout=120)


def _published(url):
    try:
        with _open(url, 'HEAD') as resp:
            return resp.status == 200
    except OSError:
        return False


def newest_snapshot(today, published=_published):
    """The URL of the newest published release of the last LOOKBACK_MONTHS
    months, or None."""
    for n in range(LOOKBACK_MONTHS):
        url = snapshot_url(months_back(today, n))
        if published(url):
            return url
    return None


def download(dump):
    """Download the newest snapshot to `dump`. Returns '' on success, else
    the reason for the failure. `dump` is replaced only by a download whose
    checksum matches and that starts with the gzip header."""
    url = newest_snapshot(dt.date.today())
    if url is None:
        return (f"no snapshot published in the last {LOOKBACK_MONTHS} months under "
                f"{SNAPSHOT_BASE}")
    # The checksum is read first, so a failed request for it cannot cost the
    # download that follows.
    try:
        with _open(url + '.md5') as resp:
            expected = (resp.read(200).decode('ascii', 'replace').split() or [''])[0].lower()
    except OSError as e:
        expected = ''
        print(f"note: no checksum for {url} ({e}), so only the gzip header is checked",
              file=sys.stderr)
    print(f"downloading {url} (about 1.1 GB) ...", flush=True)
    dump.parent.mkdir(parents=True, exist_ok=True)
    part = dump.with_name(dump.name + '.part')
    digest = hashlib.md5()
    try:
        with _open(url) as resp, open(part, 'wb') as out:
            total = int(resp.headers.get('Content-Length') or 0)
            got = 0
            while chunk := resp.read(1 << 20):
                out.write(chunk)
                digest.update(chunk)
                got += len(chunk)
                if total and got % (1 << 27) < (1 << 20):
                    print(f"  {got / 1e9:.2f} of {total / 1e9:.2f} GB", flush=True)
    except OSError as e:
        part.unlink(missing_ok=True)
        return f"download failed: {e}"
    with open(part, 'rb') as fh:
        magic = fh.read(2)
    if expected and digest.hexdigest() != expected:
        part.unlink(missing_ok=True)
        return (f"the download does not match the published checksum "
                f"(got {digest.hexdigest()}, expected {expected})")
    if magic != b'\x1f\x8b':
        part.unlink(missing_ok=True)
        return "the download is not a gzip file"
    part.replace(dump)
    checked = 'checksum verified' if expected else 'gzip header checked'
    print(f"saved {dump} ({dump.stat().st_size / 1e9:.2f} GB), {checked}", flush=True)
    return ''


# ---------- build ----------

def resolve_entities(data):
    """Replace the HTML entities in `data` with numeric character references.
    The five XML entities stay, and so does an entity that HTML does not
    define, so no name loses a letter."""
    def one(m):
        name = m.group(1)
        if name in XML_ENTITIES:
            return m.group(0)
        code = html.entities.name2codepoint.get(name.decode('ascii'))
        return b'&#%d;' % code if code else m.group(0)
    return ENTITY_RE.sub(one, data)


class EntityResolvingReader(io.RawIOBase):
    """A readable stream over `raw` with its HTML entities resolved. An `&`
    near the end of a chunk without a closing `;` is held back until the next
    chunk, so an entity split across two chunks is resolved whole."""

    def __init__(self, raw):
        super().__init__()
        self.raw = raw
        self.pending = b''
        self.pos = 0
        self.tail = b''
        self.eof = False

    def readable(self):
        return True

    def readinto(self, out):
        while len(self.pending) - self.pos < len(out) and not self.eof:
            chunk = self.raw.read(1 << 20)
            if chunk:
                data = self.tail + chunk
                cut = data.rfind(b'&')
                if cut >= 0 and len(data) - cut <= 34 and b';' not in data[cut:]:
                    data, self.tail = data[:cut], data[cut:]
                else:
                    self.tail = b''
            else:
                self.eof = True
                data, self.tail = self.tail, b''
            self.pending = self.pending[self.pos:] + resolve_entities(data)
            self.pos = 0
        n = min(len(out), len(self.pending) - self.pos)
        out[:n] = self.pending[self.pos:self.pos + n]
        self.pos += n
        return n


def _text(elem, tag):
    child = elem.find(tag)
    if child is None:
        return None
    return ' '.join(''.join(child.itertext()).split()) or None


def build(dump, out, limit=None, progress_every=500000):
    """Build the database at `out` from `dump`. Returns '' on success, else
    the reason for the failure. `out` must not exist."""
    con = sqlite3.connect(str(out))
    con.executescript('PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA cache_size=-200000;')
    con.executescript(SCHEMA)
    cur = con.cursor()
    authors = {}
    pubs = 0
    started = time.monotonic()
    root = None
    with gzip.open(dump, 'rb') as raw:
        for event, elem in ET.iterparse(EntityResolvingReader(raw), events=('start', 'end')):
            if root is None:
                root = elem
            if event != 'end' or elem.tag not in KINDS:
                continue
            key, title = elem.get('key') or '', _text(elem, 'title')
            if key and title:
                pubs += 1
                cur.execute(
                    'INSERT OR IGNORE INTO publications'
                    '(id, key, title, year, venue, ee, kind, volume, number, pages)'
                    ' VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (pubs, key, title, _text(elem, 'year'), _text(elem, VENUE_OF[elem.tag]),
                     _text(elem, 'ee'), elem.tag, _text(elem, 'volume'), _text(elem, 'number'),
                     _text(elem, 'pages')))
                # An edited volume names its editors where a paper names its
                # authors, and a citation of the volume names the editors.
                for person in elem.findall('author') or elem.findall('editor'):
                    name = ' '.join(''.join(person.itertext()).split())
                    if not name:
                        continue
                    aid = authors.get(name)
                    if aid is None:
                        cur.execute('INSERT OR IGNORE INTO authors(name) VALUES(?)', (name,))
                        aid = authors[name] = cur.lastrowid
                    cur.execute('INSERT OR IGNORE INTO publication_authors(pub_id, author_id) '
                                'VALUES(?,?)', (pubs, aid))
                if progress_every and pubs % progress_every == 0:
                    rate = pubs / max(1e-6, time.monotonic() - started)
                    print(f"  {pubs:>9,} publications ({rate:,.0f} per second)", flush=True)
            root.clear()
            if limit and pubs >= limit:
                break
    print(f"  indexing {pubs:,} titles ...", flush=True)
    con.commit()
    con.executescript(
        "CREATE VIRTUAL TABLE publications_fts USING fts5"
        "(title, content='publications', content_rowid='id');"
        "INSERT INTO publications_fts(publications_fts) VALUES('rebuild');")
    con.executemany('INSERT OR REPLACE INTO metadata(key, value) VALUES(?,?)', [
        ('schema_version', SCHEMA_VERSION),
        ('last_updated', str(int(time.time()))),
        ('publication_count', str(pubs)),
        ('author_count', str(len(authors))),
        ('built_by', 'ai-slop setup_dblp.py'),
        ('source', dump.name),
    ])
    con.commit()
    con.close()
    accented = sum(1 for name in authors if any(ord(c) > 127 for c in name))
    print(f"built {out}: {pubs:,} publications, {len(authors):,} authors, "
          f"in {(time.monotonic() - started) / 60:.1f} min", flush=True)
    if pubs == 0:
        return 'the dump holds no publications'
    if pubs > 1000 and not accented:
        return 'no author name carries a non-ASCII character, so the build dropped them'
    return ''


def main(argv):
    p = argparse.ArgumentParser(description='Download the DBLP dump and build the local database.')
    p.add_argument('--out', default=None, help=f'database to build (default: ${ENV_VAR}, else {DEFAULT_DB})')
    p.add_argument('--dump', default=None, help='build from this dump instead of downloading one')
    p.add_argument('--update', action='store_true',
                   help='download the newest snapshot and replace an existing database')
    p.add_argument('--limit', type=int, default=None, help='stop after N publications')
    args = p.parse_args(argv[1:])

    out = db_path(args.out)
    if out.exists() and not args.update:
        print(f"{out} exists. Pass --update to rebuild it.")
        return 0
    if args.dump:
        dump = Path(args.dump).expanduser()
        if not dump.is_file():
            print(f"error: no dump at {dump}", file=sys.stderr)
            return 2
    else:
        dump = out.parent / 'dblp.xml.gz'
        if args.update or not dump.is_file():
            failure = download(dump)
            if failure:
                print(f"error: {failure}. Nothing was changed.", file=sys.stderr)
                return 1
        else:
            print(f"using the dump at {dump} (pass --update to download the newest one)")

    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name + '.part')
    part.unlink(missing_ok=True)
    try:
        failure = build(dump, part, args.limit)
    except (ET.ParseError, OSError, sqlite3.Error) as e:
        failure = f"{type(e).__name__}: {e}"
    if failure:
        part.unlink(missing_ok=True)
        print(f"error: {failure}. {out} was not changed.", file=sys.stderr)
        return 1
    part.replace(out)
    print(f"the DBLP database is ready at {out}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
