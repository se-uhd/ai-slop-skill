#!/usr/bin/env python3
r"""scan_crossrefs.py <root.tex> [<root.tex> ...]

Recall aid for the cross-reference rules of the scientific and LaTeX layers:
**Refer to every figure and table in the text** (`S.refer-to-every-figure`),
**Capitalize cross-references** (`S.capitalize-cross-references`), and **Use
cross-reference macros** (`L.cross-reference-macros`). A review that reads a
paper section by section does not notice that nothing references a figure
defined in an \input file, and it overlooks one lowercase "section~\ref" among
a few hundred references. This scan follows \input and \include from each root,
resolves labels and references across all files of the run, and prints one
tab-separated line per candidate to stdout:

    <file>:<line>:<col>\t<kind>\t<context>

`<line>` and `<col>` (1-based) point at the `\begin` of a float or at the
first character of the matched word. `<context>` is the source line with
whitespace collapsed, capped at 120 characters. For a float it is the list of
its labels (or `no label`), then ` | `, then the start of its caption. The root
is reported by the path as given, and an included file by its resolved path.

Kinds:

  - unreferenced-float:  a figure or table environment (figure, table, their
                         starred forms, wrapfigure, wraptable, sidewaysfigure,
                         sidewaystable) without a \label, or none of whose
                         labels appears in a reference. A label in a file that
                         the float pulls in with \input counts as a label of
                         the float, and so does a label of a subfigure. See
                         `S.refer-to-every-figure`.
  - lowercase-ref:       a lowercase name (section, figure, fig., table, tab.,
                         chapter, appendix, equation, eq., listing, algorithm,
                         and their plurals) directly before a reference that
                         does not print a name, as in "section~\ref{...}". See
                         `S.capitalize-cross-references`.
  - name-before-autoref: one of those names, in any case, directly before a
                         command that prints the name itself (\autoref,
                         \Autoref, \cref, \Cref, \zcref), which renders as
                         "Section Section 3". See `L.cross-reference-macros`.
  - hard-coded-ref:      one of those names, in any case, followed by a typed
                         number ("Table 2", "section 3.1") or, for an appendix,
                         a letter ("Appendix A"), instead of a reference. See
                         `L.cross-reference-macros`.

A reference is any command whose name ends in `ref` (\ref, \autoref, \cref,
\Cref, \vref, \pageref, \nameref, \subref, \eqref, \zcref, and custom macros
such as \figref), with comma-separated keys in its brace argument, plus
\crefrange and \Crefrange with both keys and \hyperref[<label>]{...}. \href
takes a URL and is not a reference.

Skipped text: `%` comments, \iffalse ... \fi blocks, the verbatim, Verbatim,
lstlisting, minted, and comment environments, and inline \verb and \lstinline.
A label or a reference inside them does not count, so a figure that only a
commented-out sentence references is listed. The three text kinds also skip
the keys and URLs in the arguments of labels, references, citations, and \url,
so a key such as `TABLE 1: Demographics` is not read as a hard-coded number.

This scan is a CANDIDATE finder, not a verdict, like scan_reference.py. The
caller applies the rules before reporting. A lowercase or doubled name is a
finding with a corrected revision. A hard-coded number is a finding when the
label it stands for is identifiable, and a reference to the section or table
of another paper ("Table 2 of \citet{...}") is not a finding. An unreferenced
float is a finding that adds the reference when a sentence already discusses
it, and goes to author judgment otherwise, since only the author can write that
sentence or remove the float.

Known limitations:
  - A float in a file that no root reaches through \input or \include (e.g.,
    \includestandalone or a subfiles chapter that is passed as no root) is not
    seen, and neither is a reference in such a file.
  - A reference macro whose name does not end in `ref` is not recognized, so a
    float that only such a macro references is listed.
  - The name that \autoref prints comes from the \...autorefname macros, which
    the scan does not read, so their capitalization is not checked.
  - Labels and references resolve across every file of the run. Two papers
    passed in one run can satisfy each other's references.

A one-line summary is always printed to stderr:

    scanned 4 file(s), 12 float(s), 87 referenced label(s); 3 candidate(s) \
[unreferenced-float=1 lowercase-ref=1 name-before-autoref=0 hard-coded-ref=1]

Exits 0 when at least one input file was read, whether or not candidates were
found. Exits 2 on a usage error: no arguments, or none of the given roots could
be read.
"""
import bisect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_scan import CITE_PATTERN, INPUT_PATTERN, gather_files, resolve_ref, split_code_and_comment  # noqa: E402

KINDS = ('unreferenced-float', 'lowercase-ref', 'name-before-autoref', 'hard-coded-ref')

FLOAT_ENVS = ('figure', 'table', 'wrapfigure', 'wraptable', 'sidewaysfigure', 'sidewaystable')
FLOAT_BEGIN_RE = re.compile(r'\\begin\s*\{(' + '|'.join(FLOAT_ENVS) + r')(\*?)\}')

SKIP_ENVS = ('verbatim', 'Verbatim', 'lstlisting', 'minted', 'comment')
SKIP_BEGIN_RE = re.compile(r'\\begin\s*\{(' + '|'.join(SKIP_ENVS) + r')(\*?)\}')
INLINE_VERB_RE = re.compile(r'\\(?:verb|lstinline)\*?(?:\[[^\]]*\])?([^A-Za-z\s{])(.*?)\1')
INLINE_LST_BRACE_RE = re.compile(r'\\lstinline(?:\[[^\]]*\])?\{[^}]*\}')
# An \if... token followed by a brace takes arguments and has no \fi
# (\ifthenelse, \iftoggle), so it does not open a conditional.
IF_TOKEN_RE = re.compile(r'\\(?:(if[A-Za-z]*)(?![A-Za-z])(?!\s*\{)|fi(?![A-Za-z]))')

LABEL_RE = re.compile(r'\\z?label\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}')
REF_RE = re.compile(r'\\([A-Za-z]*ref)(?![A-Za-z])\*?\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}')
RANGE_RE = re.compile(r'\\([A-Za-z]*refrange)\*?\s*(?:\[[^\]]*\]\s*)?\{([^}]*)\}\s*\{([^}]*)\}')
HYPERREF_RE = re.compile(r'\\hyperref\s*\[([^\]]*)\]')
NOT_REFS = {'href', 'hyperref'}
CAPTION_RE = re.compile(r'\\caption\s*(?:\[[^\]]*\]\s*)?\{')
URL_RE = re.compile(r'\\url\s*\{([^}]*)\}')
# The regex groups that hold a key or URL rather than text.
ARGUMENT_GROUPS = ((LABEL_RE, (1,)), (REF_RE, (2,)), (RANGE_RE, (2, 3)),
                   (HYPERREF_RE, (1,)), (URL_RE, (1,)), (CITE_PATTERN, (2,)))

# Commands that print the name of the target themselves.
NAME_PRINTING = {'autoref', 'cref', 'zcref'}

NAMES = (r'(?:sub)*sections?|chapters?|appendix|appendices|figures?|figs?\.|tables?|tabs?\.'
         r'|equations?|eqs?\.|listings?|algorithms?')
GAP = r'(?:\s*~\s*|\s+)'
NAME_BEFORE_REF_RE = re.compile(
    r'(?<![A-Za-z\\])(?P<name>' + NAMES + r')' + GAP + r'\\(?P<cmd>[A-Za-z]*ref)(?![A-Za-z])',
    re.IGNORECASE)
HARD_CODED_RE = re.compile(
    r'(?<![A-Za-z\\])(?:(?P<name>' + NAMES + r')' + GAP + r'\d'
    r'|(?P<app>appendix|appendices)' + GAP + r'(?-i:[A-Z])(?![A-Za-z]))',
    re.IGNORECASE)


def truncate(text, limit=120):
    """Collapse whitespace and cap the text at `limit` characters."""
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + '...'


def blank_span(chars, start, end):
    """Replace chars[start:end] with spaces, keeping newlines so line
    numbers stay put."""
    for i in range(start, end):
        if chars[i] != '\n':
            chars[i] = ' '


def iffalse_spans(code):
    """Return the (start, end) spans of \\iffalse ... \\fi blocks, honoring
    nested \\if... \\fi pairs. A block without a matching \\fi is left alone."""
    spans = []
    tokens = list(IF_TOKEN_RE.finditer(code))
    i = 0
    while i < len(tokens):
        if tokens[i].group(1) != 'iffalse':
            i += 1
            continue
        depth = 0
        for j in range(i, len(tokens)):
            depth += 1 if tokens[j].group(1) else -1
            if depth == 0:
                spans.append((tokens[i].start(), tokens[j].end()))
                i = j
                break
        i += 1
    return spans


def env_end(code, m):
    """Return the match of the \\end that closes the environment opened by
    the \\begin match `m`, or None when the environment does not close."""
    name = re.escape(m.group(1) + m.group(2))
    return re.compile(r'\\end\s*\{' + name + r'\}').search(code, m.end())


def mask(code):
    """Blank the text that holds no labels, references, or prose: \\iffalse
    blocks, the SKIP_ENVS environments, and inline \\verb / \\lstinline."""
    chars = list(code)
    for start, end in iffalse_spans(code):
        blank_span(chars, start, end)
    pos = 0
    while True:
        m = SKIP_BEGIN_RE.search(code, pos)
        if not m:
            break
        end_m = env_end(code, m)
        end = end_m.end() if end_m else len(code)
        blank_span(chars, m.start(), end)
        pos = end
    for rx in (INLINE_VERB_RE, INLINE_LST_BRACE_RE):
        for m in rx.finditer(code):
            blank_span(chars, m.start(), m.end())
    return ''.join(chars)


def mask_arguments(code):
    """Blank the keys and URLs in the arguments of labels, references,
    citations, and \\url, so a key such as `TABLE 1: Demographics` is not
    read as text. The command names stay for the patterns that need them."""
    chars = list(code)
    for rx, groups in ARGUMENT_GROUPS:
        for m in rx.finditer(code):
            for g in groups:
                blank_span(chars, m.start(g), m.end(g))
    return ''.join(chars)


def brace_text(text, open_idx):
    """Return the text inside the brace group that opens at text[open_idx],
    or the rest of the text when the group does not close."""
    depth = 0
    for j in range(open_idx, len(text)):
        if j > open_idx and text[j - 1] == '\\':
            continue  # an escaped brace
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:j]
    return text[open_idx + 1:]


class Source:
    """One scanned file: the comment-stripped and masked text, with helpers to
    turn an offset into a line and a column."""

    def __init__(self, shown, path, base, text):
        self.shown = shown
        self.path = path
        self.base = base
        self.lines = [split_code_and_comment(l)[0] for l in text.splitlines()]
        self.code = mask('\n'.join(self.lines))
        self.text = mask_arguments(self.code)
        self.starts = [0]
        for line in self.lines[:-1]:
            self.starts.append(self.starts[-1] + len(line) + 1)

    def where(self, offset):
        idx = bisect.bisect_right(self.starts, offset) - 1
        return idx + 1, offset - self.starts[idx] + 1

    def labels(self, start=0, end=None):
        """Label keys between `start` and `end`."""
        end = len(self.code) if end is None else end
        return [m.group(1).strip() for m in LABEL_RE.finditer(self.code, start, end)]

    def children(self, start=0, end=None):
        """Resolved paths of the files that \\input / \\include pull in
        between `start` and `end`."""
        end = len(self.code) if end is None else end
        out = []
        for m in INPUT_PATTERN.finditer(self.code, start, end):
            child = resolve_ref(m.group(1).strip(), self.path.parent, self.base, '.tex')
            if child:
                out.append(child.resolve())
        return out


def referenced_keys(src):
    keys = set()
    for m in REF_RE.finditer(src.code):
        if m.group(1) not in NOT_REFS:
            keys.update(k.strip() for k in m.group(2).split(','))
    for m in RANGE_RE.finditer(src.code):
        keys.update(k.strip() for k in (m.group(2), m.group(3)))
    for m in HYPERREF_RE.finditer(src.code):
        keys.add(m.group(1).strip())
    keys.discard('')
    return keys


def labels_with_inputs(path, by_path, seen):
    """Labels of the file at `path` plus those of every file it pulls in."""
    if path in seen or path not in by_path:
        return []
    seen.add(path)
    src = by_path[path]
    out = src.labels()
    for child in src.children():
        out += labels_with_inputs(child, by_path, seen)
    return out


def floats(src, by_path):
    """Yield (offset, labels, caption) for each float environment in `src`."""
    pos = 0
    while True:
        m = FLOAT_BEGIN_RE.search(src.code, pos)
        if not m:
            return
        end_m = env_end(src.code, m)
        end = end_m.start() if end_m else len(src.code)
        labels = src.labels(m.end(), end)
        for child in src.children(m.end(), end):
            labels += labels_with_inputs(child, by_path, set())
        cap = CAPTION_RE.search(src.code, m.end(), end)
        caption = brace_text(src.code, cap.end() - 1) if cap else ''
        yield m.start(), labels, caption
        pos = end


def text_rows(src):
    """Yield (offset, kind) for the lowercase, doubled, and hard-coded
    reference candidates in `src`."""
    for m in NAME_BEFORE_REF_RE.finditer(src.text):
        cmd = m.group('cmd')
        if cmd in NOT_REFS:
            continue
        if cmd.lower() in NAME_PRINTING:
            yield m.start('name'), 'name-before-autoref'
        elif m.group('name')[0].islower():
            yield m.start('name'), 'lowercase-ref'
    for m in HARD_CODED_RE.finditer(src.text):
        name = m.group('name') or ''
        if name.startswith('listing'):
            continue  # "listing 5 tools" is a verb, not a reference
        yield m.start(), 'hard-coded-ref'


def main(argv):
    if len(argv) < 2:
        print("usage: scan_crossrefs.py <root.tex> [<root.tex> ...]", file=sys.stderr)
        return 2
    paths = argv[1:]
    seen = set()
    sources = []
    for path in paths:
        given = Path(path)
        base = given.resolve().parent
        for rp, text in gather_files(given, seen):
            shown = path if rp == given.resolve() else str(rp)
            sources.append(Source(shown, rp, base, text))
    if not sources:
        print(f"error: none of the {len(paths)} root(s) given could be read; nothing was scanned",
              file=sys.stderr)
        return 2

    by_path = {s.path: s for s in sources}
    refs = set()
    for src in sources:
        refs |= referenced_keys(src)

    counts = dict.fromkeys(KINDS, 0)
    n_floats = 0
    for src in sources:
        rows = []
        for offset, labels, caption in floats(src, by_path):
            n_floats += 1
            if any(l in refs for l in labels):
                continue
            named = ', '.join(labels) if labels else 'no label'
            rows.append((offset, 'unreferenced-float', truncate(f"{named} | {caption}")))
        for offset, kind in text_rows(src):
            line, _ = src.where(offset)
            rows.append((offset, kind, truncate(src.lines[line - 1])))
        for offset, kind, context in sorted(rows):
            line, col = src.where(offset)
            counts[kind] += 1
            print(f"{src.shown}:{line}:{col}\t{kind}\t{context}")

    breakdown = ' '.join(f"{k}={counts[k]}" for k in KINDS)
    print(f"scanned {len(sources)} file(s), {n_floats} float(s), {len(refs)} referenced label(s); "
          f"{sum(counts.values())} candidate(s) [{breakdown}]", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
