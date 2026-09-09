#!/usr/bin/env python3
r"""extract_cites.py [PATH]

Gather, for grounding, every citation in a LaTeX document together with the
claim the surrounding sentence attributes to it, and the bibliographic metadata
for each cited key. PATH is a `.tex` file or a directory (default: cwd); a
directory is resolved to its LaTeX root the same way find_latex_root.py does.
The root and every file it pulls in with `\input` / `\include` are scanned.

This script opens the loop that find_citation_issues.py reports: that script lists the
`\cite` calls missing a grounding comment; this script collects what each
of them needs grounded (the enclosing claim) and the source identity needed to
find a supporting quote (title / author / year / DOI / URL / eprint). A
grounding workflow then fetches each source once and returns a verbatim quote
(or a `TODO verify -- <reason>`); insert_grounding.py writes the result back.

This script fabricates nothing: it only extracts text already in the `.tex`
and `.bib` files. The anti-fabrication rule, which allows a quote only when
the source was actually retrieved, is enforced downstream by the workflow that
fills the quotes.

Output is one JSON object on stdout:

    {
      "root":  "<resolved root path>",
      "sites": [ {"file","line","end_line","command","keys","claim",
                  "groundable","grounded"} ],
      "by_key": { "<key>": {"claims": [...], "sites": [{"file","line","end_line",
                            "command","groundable","grounded"}]} },
      "meta":  { "<key>": {"type","title","author","year","doi","url",
                           "eprint","howpublished"} }
    }

`line` is the line the cite call starts on and `end_line` the line it ends on
(the same line except for a key list that spans lines). insert_grounding.py
places the comment after `end_line`.

`groundable` is True for the cite macros that require a grounding comment
(\cite, \citep, \citet, \parencite, ...); style-only helpers (\citeauthor,
\citeyear) are recorded with groundable=False so their claims enrich `by_key`
without becoming insertion targets. `grounded` is True only when the site has a
grounding comment carrying a retrieved quote; a quote-less `TODO verify` stub
(planted by revise mode or by an earlier grounding run) counts as ungrounded,
so a grounding workflow picks the site up and insert_grounding.py fills the
quote the stub only promises. A one-line summary is printed to stderr.

Exit codes:
  0  at least one source file was scanned.
  2  no LaTeX root could be resolved, multiple ambiguous roots were found, or
     the resolved root could not be read (nothing was scanned).

Recognized cite macros, the comment-stripping, the key parsing, the cite-call
scanner, and the \input / \include walker are shared with
find_citation_issues.py via cite_scan.py, so both tools see the same files and
calls. The `.bib` parsing is shared with check_bib_fields.py /
verify_references.py via bib_parse.py. Limitations of the cite scan (only the
first {key} group of multi-cite biblatex forms is read; constructs other than
`%` comments are not stripped) are inherited from there.
"""
import bisect
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cite_scan import (  # noqa: E402
    CITATION_COMMANDS, CITE_PATTERN, GROUNDED_COMMANDS, gather_files,
    grounding_quality, resolve_ref, scan_cite_calls, split_code_and_comment,
)
from bib_parse import iter_entries  # noqa: E402
from find_latex_root import find_roots  # noqa: E402
from scan_io import report_unreadable  # noqa: E402

BIB_DIRECTIVE = re.compile(r'\\(?:bibliography|addbibresource)\s*\{([^}]+)\}')

# Bibliographic fields carried through to `meta` for each used key, enough for a
# workflow agent to identify and locate the source.
META_FIELDS = ('title', 'author', 'year', 'doi', 'url', 'eprint', 'howpublished')

CLAIM_LIMIT = 500

# Tokens that end in a period without ending a sentence. Lowercased, period(s)
# stripped, so "e.g." -> "e.g", "al." (of "et al.") -> "al".
ABBREV = {
    'e.g', 'i.e', 'cf', 'al', 'etc', 'vs', 'viz', 'resp', 'approx', 'ca',
    'fig', 'figs', 'eq', 'eqs', 'sec', 'secs', 'no', 'nos', 'vol', 'vols',
    'pp', 'p', 'ch', 'chap', 'ed', 'eds', 'esp', 'incl', 'st',
    'dr', 'prof', 'mr', 'mrs', 'ms', 'jr', 'sr', 'inc', 'ltd', 'co',
}

_SENT_PUNCT = re.compile(r'[.!?]')

# A claim also begins after a paragraph break (blank line or \par) and after a
# structural / sectioning command, so the enclosing sentence of the first cite
# in a section does not swallow the preamble or the section heading.
_PARA_BREAK = re.compile(r'\n[ \t]*\n|\\par\b')
_STRUCTURAL = re.compile(
    r'\\(?:section|subsection|subsubsection|paragraph|subparagraph|chapter|part'
    r'|title|author|date|maketitle|tableofcontents|frontmatter|mainmatter'
    r'|label|caption|begin|end|bibliography|addbibresource|input|include'
    r'|usepackage|documentclass)\*?\s*(?:\[[^\]]*\])?(?:\{[^}]*\})*'
)

# In a claim, drop reference/label/structural macros together with their braced
# arguments (the argument is a target or preamble token, not prose)...
_DROP_WITH_ARG = re.compile(
    r'\\(?:label|ref|autoref|cref|Cref|vref|eqref|pageref|nameref|input|include'
    r'|bibliography|addbibresource|caption|begin|end|usepackage|documentclass'
    r'|title|author|date)\*?\s*(?:\[[^\]]*\])?(?:\{[^}]*\})*'
)
# ...then drop any remaining control word (keeping its braced text, e.g.
# \emph{important} -> important once the braces are stripped).
_CONTROL_WORD = re.compile(r'\\[a-zA-Z]+\*?\s*(?:\[[^\]]*\])?')
# Common single-character LaTeX escapes that should render as the literal char.
_ESCAPES = {r'\&': '&', r'\%': '%', r'\_': '_', r'\#': '#', r'\$': '$'}


class RootError(Exception):
    """No usable single LaTeX root could be resolved from the given path."""


def resolve_root(target):
    """Resolve PATH to a single root .tex, mirroring find_latex_root.py's
    preference order. Raises RootError on no root or ambiguous multiple roots."""
    p = Path(target)
    if p.is_file():
        return p
    if p.is_dir():
        roots = find_roots(p)
        if not roots:
            raise RootError(
                f"no LaTeX root (\\documentclass + \\begin{{document}}) found under {target}")
        if len(roots) == 1:
            return roots[0]
        for preferred in ('main.tex', 'paper.tex'):
            for r in roots:
                if r.name == preferred:
                    return r
        listing = "\n  ".join(str(r) for r in roots)
        raise RootError("multiple candidate roots; pass one explicitly:\n  " + listing)
    if p.suffix.lower() == '.tex':
        return p  # nonexistent .tex: let the read fail loudly downstream
    raise RootError(f"{target}: not a .tex file or directory")


def sentence_boundaries(text):
    """Return a sorted list of offsets at which a new claim begins: after a
    sentence-ending `.`/`!`/`?` (abbreviation- and decimal-aware), after a
    blank-line / `\\par` paragraph break, and after a structural or sectioning
    command. The structural and paragraph boundaries keep the first cite in a
    section from swallowing the preamble or the heading."""
    bounds = set()
    n = len(text)
    for m in _SENT_PUNCT.finditer(text):
        i = m.start()
        if text[i] == '.':
            if 0 < i < n - 1 and text[i - 1].isdigit() and text[i + 1].isdigit():
                continue  # decimal like 3.14
            j = i - 1
            while j >= 0 and (text[j].isalpha() or text[j] == '.'):
                j -= 1
            token = text[j + 1:i].lower().strip('.')
            if token in ABBREV:
                continue
        k = i + 1
        while k < n and text[k] in ' \t\n\r':
            k += 1
        if k >= n:
            bounds.add(k)
            continue
        nxt = text[k]
        if nxt.isupper() or nxt.isdigit() or nxt in '\\`"\'([':
            bounds.add(k)
    for m in _PARA_BREAK.finditer(text):
        bounds.add(m.end())
    for m in _STRUCTURAL.finditer(text):
        bounds.add(m.end())
    return sorted(bounds)


def clean_claim(text):
    """Reduce the enclosing sentence to plain prose: drop cite macros, reference
    and structural macros (with their arguments), and remaining control words
    (keeping their braced text); resolve common escapes and the `~` tie; collapse
    whitespace; and cap length."""
    text = CITE_PATTERN.sub(' ', text)
    text = _DROP_WITH_ARG.sub(' ', text)
    text = _CONTROL_WORD.sub(' ', text)
    text = text.replace('{', ' ').replace('}', ' ').replace('~', ' ')
    for esc, ch in _ESCAPES.items():
        text = text.replace(esc, ch)
    text = ' '.join(text.split())
    text = re.sub(r'\s+([.,;:!?])', r'\1', text).strip(' ,;')
    if len(text) > CLAIM_LIMIT:
        text = text[:CLAIM_LIMIT - 3].rstrip() + '...'
    return text


def enclosing_sentence(text, pos, bounds):
    """Return the cleaned sentence of `text` that contains offset `pos`."""
    lo = bisect.bisect_right(bounds, pos)
    start = bounds[lo - 1] if lo > 0 else 0
    end = bounds[lo] if lo < len(bounds) else len(text)
    return clean_claim(text[start:end])


def scan_text(path, text):
    """Yield a site dict per citation in one file's text. Cites are matched on
    the comment-stripped, line-joined body (so multi-line calls are caught) by
    the scanner shared with find_citation_issues.py, and each site carries the
    line the call starts on and the line it ends on."""
    raw_lines = text.splitlines()
    joined, calls = scan_cite_calls(raw_lines, CITATION_COMMANDS)
    bounds = sentence_boundaries(joined)

    for call in calls:
        _, same_comment = split_code_and_comment(raw_lines[call.end])
        # A quote-less TODO stub classifies as 'todo', not 'quote', so the
        # site stays an insertion target until a retrieved quote lands. The
        # comment block is looked up below the line the call ends on.
        grounded = grounding_quality(raw_lines, call.end, same_comment) == 'quote'
        yield {
            'file': str(path),
            'line': call.start + 1,
            'end_line': call.end + 1,
            'command': call.command,
            'keys': call.keys,
            'claim': enclosing_sentence(joined, call.pos, bounds),
            'groundable': call.command in GROUNDED_COMMANDS,
            'grounded': grounded,
        }


def resolve_bib_files(files, base):
    """Return the resolved, de-duplicated .bib paths referenced by
    \\bibliography / \\addbibresource across the gathered files."""
    found = []
    seen = set()
    for path, text in files:
        for raw_line in text.splitlines():
            code, _ = split_code_and_comment(raw_line)
            for m in BIB_DIRECTIVE.finditer(code):
                for ref in m.group(1).split(','):
                    ref = ref.strip()
                    if not ref:
                        continue
                    cand = resolve_ref(ref, path.parent, base, '.bib')
                    if cand:
                        rp = cand.resolve()
                        if rp not in seen:
                            seen.add(rp)
                            found.append(rp)
    return found


def collect_meta(bib_files, used_keys):
    """Return {key: {field: value}} for every used key found in the .bib files."""
    meta = {}
    for bib in bib_files:
        try:
            text = Path(bib).read_text(encoding='utf-8', errors='replace')
        except OSError as e:
            report_unreadable(bib, e)
            continue
        try:
            entries = list(iter_entries(text))
        except ValueError as e:
            print(f"{bib}: {e}", file=sys.stderr)
            continue
        for key, etype, fields in entries:
            if key in used_keys and key not in meta:
                meta[key] = {'type': etype}
                meta[key].update({f: fields.get(f, '') for f in META_FIELDS})
    return meta


def build_by_key(sites):
    """Aggregate sites into {key: {claims, sites}}, de-duplicating claims."""
    by_key = {}
    for site in sites:
        for key in site['keys']:
            d = by_key.setdefault(key, {'claims': [], 'sites': []})
            d['sites'].append({
                'file': site['file'], 'line': site['line'],
                'end_line': site['end_line'], 'command': site['command'],
                'groundable': site['groundable'], 'grounded': site['grounded'],
            })
            if site['claim'] and site['claim'] not in d['claims']:
                d['claims'].append(site['claim'])
    return by_key


def main(argv):
    target = argv[1] if len(argv) > 1 else '.'
    try:
        root = resolve_root(target)
    except RootError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    files = gather_files(root)
    if not files:
        print(f"error: could not read the LaTeX root {root}; nothing was scanned",
              file=sys.stderr)
        return 2

    sites = []
    for path, text in files:
        sites.extend(scan_text(path, text))

    by_key = build_by_key(sites)
    bib_files = resolve_bib_files(files, Path(root).resolve().parent)
    meta = collect_meta(bib_files, set(by_key))

    print(json.dumps(
        {'root': str(Path(root).resolve()), 'sites': sites, 'by_key': by_key, 'meta': meta},
        indent=2, ensure_ascii=False,
    ))

    ungrounded = sum(1 for s in sites if s['groundable'] and not s['grounded'])
    print(
        f"extracted {len(sites)} cite site(s), {len(by_key)} unique key(s), "
        f"{ungrounded} groundable site(s) without a quote-backed grounding comment; "
        f"metadata for {len(meta)}/{len(by_key)} key(s); "
        f"scanned {len(files)} file(s), {len(bib_files)} bib file(s)",
        file=sys.stderr,
    )
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
