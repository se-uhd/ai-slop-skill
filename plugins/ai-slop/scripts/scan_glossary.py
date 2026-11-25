#!/usr/bin/env python3
"""scan_glossary.py GLOSSARY [FILE ...] [--exclude=GLOB ...] [--root=DIR] [--no-strings]
                        [--counts] [--lint]

Recall aid for the terminology checks. It reads the vocabulary that a glossary
tells writers to avoid and lists every use of an avoided word in the text, so
that the caller judges each use against the scope that the glossary states.
`/ai-slop:glossary` and `/ai-slop:glossary-repo` run it when they check a
document or a repository against its glossary, and `/ai-slop:review`,
`/ai-slop:review-diff`, and `/ai-slop:review-repo` run it when a project
glossary exists. It prints one tab-separated line per candidate to stdout:

    <path>:<line>\\t<avoided>\\t<use instead>\\t<context>

`<avoided>` is the word or phrase as the glossary lists it, `<use instead>` is
the replacement that the glossary names for it (capped at 80 characters), and
`<context>` is the text of the line, whitespace collapsed and capped at 160
characters. A one-line summary goes to stderr.

With `--counts`, the script prints one line per avoided word instead, with
the number of candidates and of files, most candidates first, and the scope
that the glossary states for the word (capped at 120 characters). The words
without a candidate follow with zero counts, so the list shows every word that
the script read from the glossary:

    <candidates>\t<files>\t<avoided>\t<use instead>\t<scope>

A word that the glossary avoids only in one sense, such as "run" for a
session, can have hundreds of ordinary uses in a repository. The scope names
that sense, and the counts show which words to judge use by use and which to
sample before listing the uses of a word with `grep -P '\t<word>\t'` over the
full output.

Terms that the glossary avoids:
    A glossary term is never vocabulary to avoid, not even in one sense. When
    readers use a term for a neighboring concept, such as "rating" for the
    score of a rating, the definition of the term states the distinction
    (shared/glossary-format.md). The script names on stderr each avoided word
    that matches a term or a variant of one in full, such as "rating" for the
    terms "rating" and "ratings", and leaves the word out of the scan, since
    its uses are uses of the term. A word avoided only in lowercase does not
    conflict with a term in capitals, such as "system" with "SYSTEM". With
    `--lint`, the script checks only the glossary and reads no text.

Input:
    With FILE arguments, each file is read the way scan_repo.py reads it:
    Markdown and other prose files in full without code blocks, LaTeX with its
    comments, and the comments and prose string literals of source and config
    files (strings only without --no-strings). A file of a kind that
    scan_repo.py skips is read as plain text. Without FILE arguments, the
    script reads `<path>:<line>:<text>` lines from stdin, the output of
    scan_repo.py, so `scan_repo.py ROOT --no-commits | scan_glossary.py
    ROOT/GLOSSARY.md --root=ROOT` checks a repository. `--root=DIR` resolves
    the paths read from stdin against DIR (default: the current directory),
    which identifies the lines of the glossary itself.

    Lines of the glossary file are never listed. `--exclude=GLOB` (repeatable)
    drops the paths that match a shell pattern, such as `CHANGELOG.md` or
    `docs/adr/*`, for records that keep the terms of their date.

Avoided words:
    Every Markdown table whose first header cell names avoided vocabulary
    (Avoid, Do not use, Retired, Retired term(s), Draft wording, Original
    wording) contributes its rows. The first cell of a row holds the avoided
    words, and the replacement is the cell under a header that contains
    "instead", "treatment", "replacement", or "preferred", else the second
    cell. The other cells of the row are its scope. A line `Avoid: a, b, c`
    under a list entry `- **term**: ...` contributes a, b, and c with that
    term as the replacement. When the first cell or the Avoid line holds more
    than the words, such as a parenthetical that names a sense, its text is
    part of the scope too. A word that several rows or lines list is one
    avoided word, with their replacements and scopes joined by " / ".

    The format in shared/glossary-format.md lists plain words separated by
    commas, which the script reads exactly. Older formats are read on a best
    effort basis: emphasis and code-span markers are removed, a parenthetical
    is dropped, a cell with double-quoted parts contributes only those parts,
    so that a quotation in a parenthetical sense is not a word, the cell is
    split at commas, semicolons, slashes, and "or", and a part that opens
    with a qualifier (for, in, as, when, meaning, ...) is dropped, as in
    "conversation, for the messages of an email exchange".

Matching:
    Whole words, ignoring case, except for an acronym of two or more capital
    letters without a lowercase letter, which matches only in capitals, and a
    word with a scope that mentions capitals or case, such as "My Coffee (with
    a capital C)" or "system (in lowercase)", which matches only as written. A
    hyphen counts as part of a word, so "ai" does not match inside "ai-slop".
    The words of a phrase match across spaces, hyphens, and a line break
    between two consecutive lines of the same file, and the last word also
    matches with a plural "s" or "es". Code spans are removed from the text
    before matching, because they hold identifiers, paths, and commands, and
    so are the `[name]` and `{@link name}` references of doc-comments in
    source files. A line of a source file that is one template literal in
    backticks is a string, not a code span, and is matched, and so is a line
    of template text between the `>` and `<` markers of scan_repo.py.

    Matching ignores the part of speech. "event store" also matches the verb
    in "a DELETE event stores its id", and "log in" matches the noun and the
    preposition in "replays the log in order". The caller drops such a
    candidate as it drops a use in another sense.

    A use of a glossary term that contains an avoided word, such as "login
    name" for the avoided "login", is not a use of the avoided word. The
    terms are the names of the list entries and the Term cells of the concept
    tables, each variant in parentheses or after a slash counting as a term,
    except the terms that the glossary itself avoids.

Exit codes:
    0  the scan ran, with or without candidates, including a glossary that
       lists no vocabulary to avoid (noted on stderr), and with `--lint`, no
       avoided word is a term
    1  the glossary lists a term as vocabulary to avoid (named on stderr); the
       scan of the other words ran
    2  usage error, the glossary cannot be read, or none of the FILE
       arguments can be read

This scan is a candidate finder, not a verdict. A word that the glossary avoids
in one sense can be correct in another, and quotations, identifiers, and
records that keep the terms of their date stay as written. The caller reads
each candidate in context and applies the scope column of its row.
"""
import bisect
import fnmatch
import re
import sys
from itertools import groupby
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_io import report_unreadable  # noqa: E402
import scan_repo  # noqa: E402

AVOID_HEADERS = {
    'avoid', 'do not use', "don't use", 'retired', 'retired term', 'retired terms',
    'retired word', 'retired words', 'draft wording', 'original wording',
}
REPLACEMENT_HINTS = ('instead', 'treatment', 'replacement', 'preferred')
QUALIFIER_RE = re.compile(
    r'^(?:for|in|as|when|where|meaning|of|except|outside|unless|if|only)\b', re.IGNORECASE)
ENTRY_RE = re.compile(r'^\s*[-*+]\s+\*\*(?P<term>[^*]+)\*\*')
AVOID_LINE_RE = re.compile(r'^\s*(?:[-*+]\s+)?Avoid:\s*(?P<words>.+?)\s*$')
SEPARATOR_RE = re.compile(r'^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$')
CODE_SPAN_RE = re.compile(r'`[^`]*`')
# A scope that restricts a word to its capitals, as in "with a capital C" or
# "in lowercase".
CASE_SCOPE_RE = re.compile(
    r'\bcapital|\b(?:lower|upper)[- ]?case\b|\bcase[- ]sensitive\b', re.IGNORECASE)
TEMPLATE_LITERAL_RE = re.compile(r'^`[^`]*`$')
# A reference of a doc-comment: KDoc and Dokka `[name]`, Javadoc and JSDoc
# `{@link name}` and its relatives.
DOC_REF_RE = re.compile(r'\{@\w+[^}]*\}|\[[A-Za-z_][\w.#]*\](?![(\[:])')
QUOTED_RE = re.compile('"([^"]+)"|“([^”]+)”')
CONTEXT_CAP = 160
REPLACEMENT_CAP = 80
SCOPE_CAP = 120
JOIN_BREAK = '\n\x00\n'  # between lines that are not consecutive: no match crosses it


def split_row(line):
    """Split a Markdown table row into its cells. A `|` inside a code span or
    escaped as `\\|` does not end a cell."""
    body = line.strip()
    if body.startswith('|'):
        body = body[1:]
    if body.endswith('|') and not body.endswith('\\|'):
        body = body[:-1]
    cells, cur, in_code, i = [], [], False, 0
    while i < len(body):
        c = body[i]
        if c == '\\' and i + 1 < len(body) and body[i + 1] == '|':
            cur.append('|')
            i += 2
            continue
        if c == '`':
            in_code = not in_code
        if c == '|' and not in_code:
            cells.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append(''.join(cur).strip())
    return cells


def plain(text):
    """Remove code-span backticks (keeping their content) and emphasis markers."""
    text = text.replace('`', '').replace('**', '').replace('__', '')
    text = text.replace('*', '')
    return re.sub(r'(?<!\w)_|_(?!\w)', '', text).strip()


def avoided_words(cell):
    """Return the avoided words and phrases that one cell lists (see the module
    docstring for the rules)."""
    text = re.sub(r'\([^)]*\)', ' ', plain(cell))
    quoted = [a or b for a, b in QUOTED_RE.findall(text)]
    if quoted:
        parts = quoted
    else:
        parts = re.split(r'[,;/]|\s+or\s+', text)
    words = []
    for part in parts:
        part = re.sub(r'^\s*(?:and|or)\s+', '', part).strip().strip('.:;').strip()
        if not quoted and QUALIFIER_RE.match(part):
            continue
        if len(part) < 2 or not re.search(r'[A-Za-z]', part) or '...' in part:
            continue
        if part not in words:
            words.append(part)
    return words


def term_variants(cell):
    """The terms that one Term cell or entry name lists: the parts separated
    by slashes or commas, and the variants in parentheses."""
    text = plain(cell)
    inner = re.findall(r'\(([^)]*)\)', text)
    outer = re.sub(r'\([^)]*\)', ' ', text)
    terms = []
    for part in re.split(r'\s/\s|,', outer) + [v for i in inner for v in i.split(',')]:
        part = ' '.join(part.split()).strip('.:;')
        if len(part) >= 2 and re.search(r'[A-Za-z]', part) and part not in terms:
            terms.append(part)
    return terms


def read_terms(text):
    """Return the terms that a glossary defines: the names of its list entries
    (`- **term**: ...`) and the first cells of its tables headed Term."""
    terms, fence_open = [], False
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if scan_repo.FENCE_RE.match(line):
            fence_open = not fence_open
        if fence_open:
            continue
        m = ENTRY_RE.match(line)
        if m:
            terms += term_variants(m.group('term').rstrip(':'))
        elif (line.lstrip().startswith('|') and i + 1 < len(lines)
              and SEPARATOR_RE.match(lines[i + 1].strip())
              and plain(split_row(line)[0]).lower() == 'term'):
            for row in lines[i + 2:]:
                if not row.lstrip().startswith('|'):
                    break
                terms += term_variants(split_row(row)[0])
    return list(dict.fromkeys(terms))


def residue(cell, words):
    """The plain text of `cell` when it holds more than the list of `words`,
    such as a parenthetical or a qualifier that names a sense, else ''."""
    text = ' '.join(plain(cell).split()).rstrip('.').strip()
    return '' if text == ', '.join(words) else text


def read_entries(text):
    """Return (avoided, use_instead, scope) triples from the avoid tables and
    the `Avoid:` lines of a glossary, in the order of the glossary."""
    entries = []
    lines = text.splitlines()
    in_fence = scan_repo.FENCE_RE
    fence_open = False
    i = 0
    current_term = None
    while i < len(lines):
        line = lines[i]
        if in_fence.match(line):
            fence_open = not fence_open
            i += 1
            continue
        if fence_open:
            i += 1
            continue
        m = ENTRY_RE.match(line)
        if m:
            current_term = m.group('term').strip().rstrip(':')
        m = AVOID_LINE_RE.match(line)
        if m and current_term:
            words = avoided_words(m.group('words'))
            scope = residue(m.group('words'), words)
            for word in words:
                entries.append((word, current_term, scope))
            i += 1
            continue
        if (line.lstrip().startswith('|') and i + 1 < len(lines)
                and SEPARATOR_RE.match(lines[i + 1].strip())):
            header = [plain(c).lower() for c in split_row(line)]
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith('|'):
                rows.append(split_row(lines[j]))
                j += 1
            if header and header[0] in AVOID_HEADERS:
                col = next((k for k, h in enumerate(header)
                            if k > 0 and any(w in h for w in REPLACEMENT_HINTS)), 1)
                for row in rows:
                    if not row:
                        continue
                    use = plain(row[col]) if col < len(row) else ''
                    words = avoided_words(row[0])
                    notes = [residue(row[0], words)] + [
                        plain(c) for k, c in enumerate(row) if k not in (0, col)]
                    scope = '; '.join(n for n in notes if n)
                    for word in words:
                        entries.append((word, use, scope))
            i = j
            continue
        i += 1
    return entries


def is_acronym(word):
    return sum(c.isupper() for c in word) >= 2 and not any(c.islower() for c in word)


def merge_entries(entries):
    """Merge the triples that list the same word, ignoring case, into
    (avoided, use_instead, scope, ignore_case) in the order of first listing.
    The replacements and scopes are joined by " / ", and the word ignores case
    unless every listing spells it as an acronym or has a scope that mentions
    capitals (CASE_SCOPE_RE)."""
    merged = {}
    for word, use, scope in entries:
        m = merged.setdefault(word.lower(), [word, [], [], True])
        for value, seen in ((use, m[1]), (scope, m[2])):
            if value and value not in seen:
                seen.append(value)
        m[3] = m[3] and (is_acronym(word) or bool(CASE_SCOPE_RE.search(scope)))
    return [(word, ' / '.join(uses), ' / '.join(scopes), not acronym)
            for word, uses, scopes, acronym in merged.values()]


def word_pattern(word, ignore_case=None):
    """Compile the pattern that finds one avoided word or phrase. By default,
    an acronym matches only in capitals and any other word ignores case."""
    parts = [p for p in re.split(r'[\s-]+', word) if p]
    body = r'[\s-]+'.join(re.escape(p) for p in parts)
    if parts[-1][-1:].isalpha():
        body += '(?:s|es)?'
    if ignore_case is None:
        ignore_case = not is_acronym(word)
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(r'(?<![\w-])' + body + r'(?![\w-])', flags)


def truncate(text, cap):
    text = ' '.join(text.split())
    return text if len(text) <= cap else text[:cap - 3] + '...'


def matchable(path, text):
    """The text of one record with the parts that hold identifiers blanked:
    code spans, and in a source file the references of doc-comments. A source
    line that is one template literal in backticks is kept as a string."""
    if scan_repo.classify(path)[0] != 'comment':
        return CODE_SPAN_RE.sub(' ', text)
    if TEMPLATE_LITERAL_RE.match(text):
        return text
    if text.startswith('>') and text.endswith('<'):  # template text, see scan_repo.py
        return ' ' + text[1:-1] + ' '
    return DOC_REF_RE.sub(' ', CODE_SPAN_RE.sub(' ', text))


def term_conflicts(entries, terms):
    """Return (avoided, term) for each merged entry that names a glossary term
    or a variant of one, in a form that the avoided word matches in full, such
    as "rating" for the term "rating" or "ratings". A word avoided only in
    lowercase does not conflict with a term in capitals."""
    conflicts = []
    for word, _, _, ignore_case in entries:
        pattern = word_pattern(word, ignore_case)
        conflicts += [(word, t) for t in terms if pattern.fullmatch(t)]
    return conflicts


def candidates(records, entries, terms=()):
    """Yield (path, line, avoided, use_instead, context) for each use of an
    avoided word in `records`, a list of (path, line, text) in scan order.
    `entries` are the merged entries of merge_entries(), and a use inside one
    of the glossary `terms` that contains the avoided word is skipped."""
    avoided = {word.lower() for word, _, _, _ in entries}
    patterns = []
    for word, use, _, ignore_case in entries:
        pattern = word_pattern(word, ignore_case)
        guards = [word_pattern(t) for t in terms
                  if t.lower() not in avoided and pattern.search(t)]
        patterns.append((word, truncate(use, REPLACEMENT_CAP), pattern, guards))
    for path, group in groupby(records, key=lambda r: r[0]):
        starts, parts, pos, prev = [], [], 0, None
        for _, lineno, text in group:
            if parts:
                sep = ' ' if prev is not None and lineno == prev + 1 else JOIN_BREAK
                parts.append(sep)
                pos += len(sep)
            starts.append((pos, lineno, text))
            stripped = matchable(path, text)
            parts.append(stripped)
            pos += len(stripped)
            prev = lineno
        joined = ''.join(parts)
        offsets = [s[0] for s in starts]
        found, guarded = {}, {}
        for word, use, pattern, guards in patterns:
            spans = []
            for guard in guards:
                if guard.pattern not in guarded:
                    guarded[guard.pattern] = [g.span() for g in guard.finditer(joined)]
                spans += guarded[guard.pattern]
            for m in pattern.finditer(joined):
                if any(a <= m.start() and m.end() <= b for a, b in spans):
                    continue
                k = bisect.bisect_right(offsets, m.start()) - 1
                _, lineno, text = starts[k]
                key = (lineno, word, use)
                if key not in found:
                    found[key] = (path, lineno, word, use, truncate(text, CONTEXT_CAP))
        for key in sorted(found, key=lambda k: (k[0], k[1].lower())):
            yield found[key]


def stdin_records(glossary, excludes, root):
    """Read scan_repo.py output from stdin as (path, line, text) records, with
    each path resolved against `root` to recognize the glossary."""
    records = []
    for raw in sys.stdin:
        m = re.match(r'^(?P<path>.*?):(?P<line>\d+):(?P<text>.*)$', raw.rstrip('\n'))
        if not m:
            continue
        path = m.group('path')
        if skipped(path, glossary, excludes, root):
            continue
        records.append((path, int(m.group('line')), m.group('text')))
    return records


def file_records(paths, glossary, excludes, strings, unreadable):
    """Read FILE arguments as (path, line, text) records, extracted as
    scan_repo.py extracts them. Appends each unreadable path to `unreadable`."""
    records = []
    for path in paths:
        if skipped(path, glossary, excludes):
            continue
        try:
            text = Path(path).read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            report_unreadable(path, e)
            unreadable.append(path)
            continue
        kind, spec = scan_repo.classify(path)
        if kind == 'skip':
            kind, spec = 'prose', None
        for lineno, line, _ in scan_repo.extract_file(path, text, strings, kind, spec):
            records.append((path, lineno, line))
    return records


def skipped(path, glossary, excludes, root=None):
    """True for the glossary itself and for a path that an exclude pattern
    matches. A relative path is resolved against `root` when one is given."""
    if any(fnmatch.fnmatch(path, pat) for pat in excludes):
        return True
    try:
        return (Path(root or '.') / path).resolve() == glossary
    except OSError:
        return False


def report_conflicts(glossary_path, entries, conflicts):
    """Name each avoided word that is also a glossary term on stderr."""
    scopes = {word: scope for word, _, scope, _ in entries}
    by_word = {}
    for word, term in conflicts:
        by_word.setdefault(word, []).append(f'"{term}"')
    for word, terms in by_word.items():
        sense = f" ({truncate(scopes[word], SCOPE_CAP)})" if scopes[word] else ''
        print(f'scan_glossary: {glossary_path} defines the term{"s" * (len(terms) > 1)} '
              f'{" and ".join(terms)} and lists "{word}" as vocabulary to avoid{sense}. '
              'A term cannot also be avoided vocabulary. Remove the word from the '
              'avoided vocabulary and state the distinction in the definition of the '
              'term.', file=sys.stderr)


def main(argv):
    excludes, strings, counts, lint, root, positional = [], True, False, False, None, []
    for arg in argv[1:]:
        if arg.startswith('--exclude='):
            excludes.append(arg.split('=', 1)[1])
        elif arg.startswith('--root='):
            root = arg.split('=', 1)[1] or None
        elif arg == '--no-strings':
            strings = False
        elif arg == '--counts':
            counts = True
        elif arg == '--lint':
            lint = True
        elif arg.startswith('--'):
            print(f"scan_glossary: unknown option {arg}", file=sys.stderr)
            return 2
        else:
            positional.append(arg)
    if not positional:
        print("usage: scan_glossary.py GLOSSARY [FILE ...] [--exclude=GLOB ...] "
              "[--root=DIR] [--no-strings] [--counts] [--lint]", file=sys.stderr)
        return 2
    glossary_path, files = positional[0], positional[1:]
    try:
        glossary_text = Path(glossary_path).read_text(encoding='utf-8')
    except OSError as e:
        report_unreadable(glossary_path, e)
        return 2
    glossary = Path(glossary_path).resolve()
    entries = merge_entries(read_entries(glossary_text))
    terms = read_terms(glossary_text)
    conflicts = term_conflicts(entries, terms)
    report_conflicts(glossary_path, entries, conflicts)
    if lint:
        print(f"{len(terms)} term(s) and {len(entries)} avoided word(s) in {glossary_path}; "
              f"{len({w for w, _ in conflicts})} avoided word(s) that are terms.",
              file=sys.stderr)
        return 1 if conflicts else 0
    conflicting = {word for word, _ in conflicts}
    entries = [e for e in entries if e[0] not in conflicting]
    if not entries:
        print(f"scan_glossary: {glossary_path} lists no vocabulary to avoid "
              "(no table headed Avoid, Do not use, or Retired, and no Avoid: line)",
              file=sys.stderr)
        return 1 if conflicts else 0
    unreadable = []
    if files:
        records = file_records(files, glossary, excludes, strings, unreadable)
        if len(unreadable) == len(files):
            print(f"error: none of the {len(files)} file(s) given could be read",
                  file=sys.stderr)
            return 2
    else:
        records = stdin_records(glossary, excludes, root)
    scopes = {word: truncate(scope, SCOPE_CAP) for word, _, scope, _ in entries}
    n, paths, per_word = 0, set(), {}
    for path, lineno, word, use, context in candidates(records, entries, terms):
        if counts:
            count = per_word.setdefault((word, use), [0, set()])
            count[0] += 1
            count[1].add(path)
        else:
            print(f"{path}:{lineno}\t{word}\t{use}\t{context}")
        n += 1
        paths.add(path)
    for (word, use), (hits, files) in sorted(
            per_word.items(), key=lambda kv: (-kv[1][0], kv[0][0].lower())):
        print(f"{hits}\t{len(files)}\t{word}\t{use}\t{scopes[word]}")
    if counts:
        found_words = {word for word, _ in per_word}
        for word, use, scope, _ in entries:
            if word not in found_words:
                print(f"0\t0\t{word}\t{truncate(use, REPLACEMENT_CAP)}\t{scopes[word]}")
    print(f"{len(entries)} avoided word(s) from {glossary_path}; "
          f"{n} candidate(s) in {len(paths)} file(s).", file=sys.stderr)
    return 1 if conflicts else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
