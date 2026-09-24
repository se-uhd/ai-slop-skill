#!/usr/bin/env python3
"""scan_repeats.py <file> [<file> ...]

Recall aid for **Refer back instead of repeating** (`G.refer-back`). The review
pass is an LLM reading prose, and it misses a sentence that a writer pasted
from one place of a document into another, such as the weaknesses of a review
form copied into its detailed comments. The copy reads fluently where it
stands, and the first occurrence may be pages away. This scan lists every
sentence that repeats text from an earlier sentence of the same file. It prints
one tab-separated line per candidate to stdout:

    <file>:<line>:<col>\\trepeat\\t<context>

`<line>` and `<col>` (1-based) point at the first character of the later
sentence. `<context>` gives the line of the earlier sentence, then ` | `, then
the later sentence with whitespace collapsed, capped at 120 characters, as in
`line 25 | The comparison with cargo-fuzz is not fair because ...`.

A sentence is a candidate when it shares a run of at least MIN_RUN words with an
earlier sentence, or repeats an earlier sentence of at least MIN_EXACT words
whole, after case, punctuation, and whitespace are normalized. That covers a
verbatim copy, a copy with a changed ending, and a short sentence pasted twice.
A sentence that occurs word for word more than MAX_OCCURRENCES times is left
out, because a template or form label that every section repeats is not a
paste, and a paste usually occurs twice. Text that such a sentence shares with a
differently worded one is still listed. Each later sentence is listed once, at
the earliest sentence it repeats. Repeats inside one sentence are not listed.
On a set of 126 peer-review files, the scan listed about eight candidates per
file, and about half of them were form labels that the review skips.

This scan is a CANDIDATE finder, not a verdict, like scan_reference.py. The
caller applies the rule's test before reporting: a brief reminder that the
argument needs is acceptable, and a second copy is a finding. The paragraph and
sentence splitting come from scan_sentences.py, so the same text is skipped:
fenced code blocks, YAML front matter, Markdown headings, tables, block quotes,
and HTML comments, and in a `.tex` file the comments, the preamble, the
sectioning commands, and the verbatim, code, math, and tabular environments. A
quotation counts as one word, so a quote that two sentences share does not make
them repeats.

A one-line summary is always printed to stderr:

    scanned 1 file(s), 42 sentence(s); 2 repeat(s)

Exits 0 when at least one input file was read, whether or not repeats were
found. Exits 2 on a usage error: no arguments, or none of the given paths could
be read.
"""
import bisect
import re
import sys
from collections import Counter
from pathlib import Path

from scan_io import report_unreadable
from scan_sentences import (count_words, markdown_paragraphs, normalize,
                            split_sentences, tex_paragraphs, truncate)

MIN_RUN = 6
MIN_EXACT = 5
MAX_OCCURRENCES = 2
TOKEN_RE = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")


def sentences(segments, is_tex):
    """Yield (line, col, text, tokens) for the sentences of one paragraph."""
    starts, pos = [], 0
    for _, _, seg in segments:
        starts.append(pos)
        pos += len(seg) + 1
    ptext = ' '.join(seg for _, _, seg in segments)
    norm = normalize(ptext, is_tex)
    for s, e in split_sentences(norm):
        chunk = norm[s:e]
        s2 = s + len(chunk) - len(chunk.lstrip())
        e2 = s + len(chunk.rstrip())
        if not count_words(norm[s2:e2]):
            continue
        i = bisect.bisect_right(starts, s2) - 1
        line_idx, col, _ = segments[i]
        tokens = TOKEN_RE.findall(norm[s2:e2].lower())
        yield line_idx + 1, col + s2 - starts[i] + 1, ptext[s2:e2], tokens


def keys(tokens):
    """Return the word runs of a sentence, plus the whole sentence when it is
    long enough for an exact match."""
    out = [tuple(tokens[k:k + MIN_RUN]) for k in range(len(tokens) - MIN_RUN + 1)]
    if len(tokens) >= MIN_EXACT:
        out.append(('',) + tuple(tokens))
    return out


def scan_file(path, stats):
    """Scan one file, print one TSV row per repeat to stdout, and update
    `stats` in place."""
    try:
        text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError as e:
        report_unreadable(path, e)
        return
    stats['files'] += 1
    is_tex = Path(path).suffix.lower() == '.tex'
    paragraphs = tex_paragraphs(text) if is_tex else markdown_paragraphs(text)
    found = [row for segments in paragraphs for row in sentences(segments, is_tex)]
    stats['sentences'] += len(found)
    occurrences = Counter(k for *_, tokens in found for k in set(keys(tokens)))
    variants = {}  # key -> the distinct sentences that contain it
    for *_, tokens in found:
        for k in keys(tokens):
            variants.setdefault(k, set()).add(tuple(tokens))

    def template(k):
        return occurrences[k] > MAX_OCCURRENCES and len(variants[k]) == 1

    seen = {}  # key -> (sentence index, line)
    for index, (line, col, sentence, tokens) in enumerate(found):
        mine = [k for k in keys(tokens) if not template(k)]
        earlier = [seen[k] for k in mine if k in seen and seen[k][0] != index]
        if earlier:
            stats['repeats'] += 1
            first = min(earlier)[1]
            print(f"{path}:{line}:{col}\trepeat\t"
                  f"{truncate(f'line {first} | ' + ' '.join(sentence.split()))}")
        for k in mine:
            seen.setdefault(k, (index, line))


def main(argv):
    if len(argv) < 2:
        print("usage: scan_repeats.py <file> [<file> ...]", file=sys.stderr)
        return 2
    stats = {'files': 0, 'sentences': 0, 'repeats': 0}
    paths = argv[1:]
    for path in paths:
        scan_file(path, stats)
    print(f"scanned {stats['files']} file(s), {stats['sentences']} sentence(s); "
          f"{stats['repeats']} repeat(s)", file=sys.stderr)
    if stats['files'] == 0:
        print(f"error: none of the {len(paths)} path(s) given could be read; nothing was scanned",
              file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
