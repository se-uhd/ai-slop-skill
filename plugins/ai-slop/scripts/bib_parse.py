#!/usr/bin/env python3
"""bib_parse.py — shared BibTeX parsing primitives.

check_bib_fields.py (required-field presence), verify_references.py (database
lookups), and extract_cites.py (per-key metadata for grounding) all split a
.bib file into entries and read their fields. The brace-counting entry splitter
and the two field parsers — one returning field *names* (for the presence check)
and one returning field *values* — live here so the three tools share one parser
instead of re-implementing brace handling.

  - find_entry_blocks(text)   -> yields (etype, body) per @TYPE{...} entry
  - parse_entry(body)         -> (key, set_of_lowercase_field_names)
  - parse_entry_values(body)  -> (key, {field: value})
  - iter_entries(text)        -> yields (key, etype, {field: value}), skipping
                                 @string / @preamble / @comment

Assumes BibTeX keys contain no tabs (true in practice).
"""
import re

SKIP_TYPES = {'string', 'preamble', 'comment'}

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
    braces, collapse whitespace, and drop a trailing comma."""
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
        m = _FIELD_VALUE.match(rest, i)
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
