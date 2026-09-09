#!/usr/bin/env python3
"""bib_parse.py: shared BibTeX parsing primitives.

check_bib_fields.py (required-field presence), verify_references.py (database
lookups), and extract_cites.py (per-key metadata for grounding) all split a
.bib file into entries and read their fields. The brace-counting entry splitter
and the two field parsers, one returning field *names* (for the presence check)
and one returning field *values*, are defined here so the three tools share
one parser instead of re-implementing brace handling. Values may be brace-,
quote-, or bare-delimited, a quoted value may contain backslash-escaped quotes,
and the `#` concatenation of several parts is joined. Common TeX accent
commands (\\"u, \\'e, \\c{c}, \\ss, ...) are resolved to their Unicode letters so
a title compares cleanly against a database record.

  - find_entry_blocks(text)   -> yields (etype, body) per @TYPE{...} entry
  - parse_entry(body)         -> (key, set_of_lowercase_field_names)
  - parse_entry_values(body)  -> (key, {field: value})
  - iter_entries(text)        -> yields (key, etype, {field: value}), skipping
                                 @string / @preamble / @comment

Assumes BibTeX keys contain no tabs (true in practice).
"""
import re
import unicodedata

SKIP_TYPES = {'string', 'preamble', 'comment'}

# TeX accent commands: the symbol or letter after the backslash -> combining
# mark. Applied to the letter that follows (braced or not) after the braces
# are stripped, so {\"u}, \"{u}, and \"u all become ü.
_COMBINING = {
    '"': '\u0308', "'": '\u0301', '`': '\u0300', '^': '\u0302', '~': '\u0303',
    '=': '\u0304', '.': '\u0307', 'c': '\u0327', 'v': '\u030c', 'u': '\u0306',
    'H': '\u030b', 'k': '\u0328', 'r': '\u030a',
}
_SYMBOL_ACCENT_RE = re.compile(r'\\(["\'`^~=.])\{?([A-Za-z])\}?')
_LETTER_ACCENT_RE = re.compile(r'\\([cvuHkr])(?:\{([A-Za-z])\}|\s+([A-Za-z]))')
_SPECIAL_LETTERS = {
    r'\ss': 'ß', r'\o': 'ø', r'\O': 'Ø', r'\ae': 'æ', r'\AE': 'Æ', r'\oe': 'œ',
    r'\OE': 'Œ', r'\aa': 'å', r'\AA': 'Å', r'\l': 'ł', r'\L': 'Ł', r'\i': 'i',
    r'\j': 'j',
}
_SPECIAL_RE = re.compile('|'.join(re.escape(k) for k in sorted(_SPECIAL_LETTERS, key=len, reverse=True)) + r'(?![A-Za-z])')


def deaccent(text):
    """Resolve TeX accent commands and special letters in `text` to Unicode."""
    text = _LETTER_ACCENT_RE.sub(
        lambda m: unicodedata.normalize('NFC', (m.group(2) or m.group(3)) + _COMBINING[m.group(1)]), text)
    text = _SPECIAL_RE.sub(lambda m: _SPECIAL_LETTERS[m.group(0)], text)
    text = _SYMBOL_ACCENT_RE.sub(
        lambda m: unicodedata.normalize('NFC', m.group(2) + _COMBINING[m.group(1)]), text)
    return text

ENTRY_HEAD = re.compile(r'@(\w+)\s*\{', re.IGNORECASE)
_FIELD_NAME = re.compile(r'(\w+)\s*=', re.IGNORECASE)
_FIELD_VALUE = re.compile(r'(\w+)\s*=\s*', re.IGNORECASE)


def find_entry_blocks(text):
    """Yield (etype, body) for each @TYPE{...} entry, using brace counting
    so entries with closing `}` on the same line as the last field, or
    nested braces inside field values, are bounded correctly."""
    pos = 0
    while pos < len(text):
        m = ENTRY_HEAD.search(text, pos)
        if not m:
            return
        etype = m.group(1).lower()
        body_start = m.end()
        depth = 1
        i = body_start
        while i < len(text) and depth > 0:
            c = text[i]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            i += 1
        if depth != 0:
            raise ValueError(f"unbalanced braces in @{etype} starting at offset {m.start()}")
        yield etype, text[body_start:i - 1]
        pos = i


def parse_entry(body):
    """Return (key, set_of_lowercase_field_names) for one entry body.

    The first top-level comma terminates the key. Field names are detected
    as 'name =' tokens at brace depth 0 outside quoted strings.
    """
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
        return body.strip(), set()
    key = body[:key_end].strip()
    rest = body[key_end + 1:]

    fields = set()
    depth = 0
    i = 0
    n = len(rest)
    while i < n:
        c = rest[i]
        if c == '{':
            depth += 1
            i += 1
        elif c == '}':
            depth -= 1
            i += 1
        elif c == '"' and depth == 0:
            i += 1
            while i < n and rest[i] != '"':
                if rest[i] == '\\' and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
        elif depth == 0 and (c.isalpha() or c == '_'):
            m = _FIELD_NAME.match(rest, i)
            if m:
                fields.add(m.group(1).lower())
                i = m.end()
            else:
                i += 1
        else:
            i += 1
    return key, fields


def clean_value(raw):
    """Strip a BibTeX field value's outer brace/quote delimiters and inner
    braces, resolve TeX accents, collapse whitespace, and drop a trailing
    comma."""
    raw = raw.strip().rstrip(',').strip()
    if len(raw) >= 2 and ((raw[0] == '{' and raw[-1] == '}') or (raw[0] == '"' and raw[-1] == '"')):
        raw = raw[1:-1]
    text = deaccent(raw)
    return re.sub(r'\s+', ' ', text.replace('{', '').replace('}', '')).strip()


def _read_value(rest, j):
    """Read one field value starting at offset `j` of `rest`: a sequence of
    parts joined by `#`, each brace-delimited (nested braces balanced),
    quote-delimited (backslash escapes honored), or bare (a macro name or a
    number). Returns (text, k) with the parts' contents concatenated, their
    delimiters removed, and `k` the offset after the value."""
    n = len(rest)
    parts = []
    while True:
        while j < n and rest[j] in ' \t\r\n':
            j += 1
        if j >= n:
            break
        if rest[j] == '{':
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
            parts.append(rest[j + 1:k - 1] if rest[k - 1:k] == '}' else rest[j + 1:k])
        elif rest[j] == '"':
            k = j + 1
            while k < n and rest[k] != '"':
                k += 2 if rest[k] == '\\' else 1
            parts.append(rest[j + 1:k].replace('\\"', '"'))
            k += 1
        else:
            k = j
            while k < n and rest[k] not in ',#' and not rest[k].isspace():
                k += 1
            parts.append(rest[j:k])
        j = k
        while j < n and rest[j] in ' \t\r\n':
            j += 1
        if j < n and rest[j] == '#':
            j += 1
            continue
        break
    return ''.join(parts), j


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
        m = _FIELD_VALUE.match(rest, i)
        if not m:
            i += 1
            continue
        name = m.group(1).lower()
        value, k = _read_value(rest, m.end())
        fields[name] = clean_value(value)
        i = k
    return key, fields


def iter_entries(text):
    """Yield (key, etype, {field: value}) for each non-skipped @entry in text."""
    for etype, body in find_entry_blocks(text):
        if etype in SKIP_TYPES:
            continue
        key, fields = parse_entry_values(body)
        yield key, etype, fields
