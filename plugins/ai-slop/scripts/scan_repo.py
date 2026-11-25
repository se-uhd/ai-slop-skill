#!/usr/bin/env python3
"""scan_repo.py [REPO_ROOT] [--commits=<N|all|RANGE>] [--no-commits] [--no-strings]
                    [--exclude=GLOB ...]

Extract the natural-language text from a whole code repository so the ai-slop
skills can read prose outside a single document or a diff: Markdown and
plain-text files in full, the comments, doc-comments, and prose string literals
of source and config files, and the commit messages of the repository. This
script drives `/ai-slop:review-repo`, the repo-wide counterpart to
`/ai-slop:review` (one document) and `/ai-slop:review-diff` (changed lines
only), and `/ai-slop:glossary-repo`, which builds and checks the glossary of a
repository. `scan_glossary.py` imports `extract_file` to read the files that it
is given in the same way.

REPO_ROOT is a directory and defaults to the current working directory.

Output (stdout): one natural-language line per output line, in grep form

    <relpath>:<line>:<text>

where <relpath> is relative to REPO_ROOT, <line> is 1-based, and <text> is the
prose with its comment markers stripped. Lines are grouped by file and files are
emitted in sorted order, so the output is stable across runs. Commit messages
follow the files, newest first, under a `commit <short-sha>` pseudo-path (no real
file is named that) so the reviewer can group and locate findings by commit. A
one-line summary is printed to stderr (files scanned, how many were prose vs
comment-bearing, how many commit messages, and how many text lines were emitted).

Options:
    --commits=<spec>  Which commit messages to scan. <spec> is a count (the most
                      recent N commits, 200 by default), the word `all` (the
                      full reachable history), or a git revision
                      range such as `main..HEAD` (the commits on a branch). Merge
                      commits and the standard trailer lines (Co-authored-by,
                      Signed-off-by, ...) are skipped either way. A spec that
                      starts with a dash is a usage error, so no value reaches
                      git as an option, and a range git cannot resolve stops the
                      run with exit 2 and git's message instead of an empty
                      commit section.
    --no-commits      Do not scan commit messages at all.
    --no-strings      Do not extract string literals from source and config
                      files, only their comments.
    --exclude=<glob>  Skip the files whose path relative to REPO_ROOT matches
                      the shell pattern, such as `data/*` for collected data or
                      `CHANGELOG.md` for a record that keeps the terms of its
                      date. Repeatable.

Exit codes:
    0  scanned successfully (even if nothing matched)
    2  REPO_ROOT does not exist or is not a directory, more than one REPO_ROOT
       is given, a --commits value is malformed, or git rejected the --commits
       range

What is scanned:
    File list. In a git repository the file set comes from `git ls-files` at
    REPO_ROOT, so `.gitignore`d build output, dependencies, and untracked files
    are excluded automatically. Outside a git repository the tree is walked
    instead. In both cases, files under a denylisted build, dependency,
    vendored, or test-fixture directory (DENY_DIRS) are skipped.

    Prose files (reviewed in full): .md .markdown .mdx .txt .text .rst .adoc
    .asciidoc .org .tex. Every non-blank line is emitted, so the `%` comments
    in a LaTeX file are reviewed alongside its body (just as comments are in source
    files). In Markdown, fenced code blocks are skipped, except fences labeled
    with a prose format (markdown, md, mdx, text, txt, plain), which are
    reviewed as prose.

    Comment-bearing files (only the comments and string literals are
    reviewed): source and config files with a known comment syntax, by
    extension or name (see COMMENT_SPECS / NAME_SPECS). Both line comments (`//`, `#`, `--`, `;`) and block comments
    (`/* */`, `<!-- -->`, Python `\"\"\" \"\"\"`/`''' '''`) are extracted, and a
    leading decoration run (`*`, `/`, `!`) is stripped from each extracted line.

    String literals (unless --no-strings): a string literal on one line that
    reads as prose (see prose_literal), such as an error message, a help text,
    or a label that users see, is emitted with its quote characters, so a
    reader can tell it from a comment. Strings are not extracted from test
    files (see is_test_path), whose strings are inputs and expected output
    rather than text that users read, or from CSS and Lisp files and other
    markup (NO_STRING_SPECS), where quotes delimit values or symbols.

    Templates (unless --no-strings, and not in test files): the text that users
    read in HTML, Vue, and Svelte files, in the multi-line template literals
    of JavaScript and TypeScript, such as an inline Angular template, and in
    the JSX of `.js`, `.jsx`, and `.tsx` files. The text between the tags is
    emitted line by line without the tags, between `>` and `<` as markers that
    tell it from a comment, and the value of an attribute named
    `alt` or ending in label, tooltip, title, placeholder, hint, message,
    description, or text is emitted with its quotes, as is a quoted string that
    starts with a capital letter in a bound attribute or an interpolation. In
    JSX, a string that is the whole of a child expression, such as
    `{' changed '}`, is emitted too, and a string elsewhere in an expression
    when it reads as prose. Comments, interpolations, Angular control flow, and the
    content of script, style, code, pre, svg, and mat-icon elements are left
    out. A multi-line template literal without markup is read as one string
    and emitted line by line, each line in backticks, when it reads as prose
    and is not CSS. The comments in a template literal are read in any case.

    A string literal under a key or named argument that names text, such as
    `label: 'Manage users'`, `title: '...'`, or `summary = "..."`, is
    emitted whatever its length. JSON is read in two cases: the values of a
    translation catalog in a locale directory (JSON_TEXT_DIRS, such as
    `i18n/` or `locales/`), and the name and description of a web app
    manifest (`.webmanifest`). Other JSON holds configuration or data and is
    skipped. Gherkin `.feature` files are read in full as prose.

    Skipped: binary/asset extensions, lockfiles, dependency pins
    (requirements*.txt), license texts, source maps, files above a size cap, and
    generated files, since fixing prose in generated output is futile. A file is
    generated when one of its first ten lines is a comment line (by the comment
    syntax of the file itself, or `<!--` / `%` in a prose file) that carries a marker
    such as "DO NOT EDIT", "@generated", or "Code generated by", or when one of
    those ten lines carries the `@generated` tag or the uppercase `DO NOT EDIT`
    banner outright. A prose line that merely mentions the phrase ("do not edit
    generated files under build/") is not a marker, and neither is a marker
    followed on its line by words that say the file was edited by hand since
    (EDITED_RE), as in "generated by `ng new` and then tuned". Skipped generated files are
    named on stderr (the first 20, then `...`), so a dropped file is visible.

    In Markdown, YAML front matter and indented code blocks (four spaces or a
    tab after a blank line, outside a list) are skipped along with fenced code.

    Commit messages (unless --no-commits): the subject and body of each selected
    commit, from `git log` (so this applies only in a git work tree). The standard
    trailer lines (Co-authored-by, Signed-off-by, Reviewed-by, ...) and merge
    commits are skipped, since neither is hand-written prose. Pushed history is
    rewritten only by a deliberate repair, so findings here are mostly advisory
    (a guide for future messages, or for rewording the commits on a branch before
    they are pushed) rather than something `/ai-slop:revise` can apply.

Known limitations (this is a heuristic extractor, not a lexer for every language):
    - Comment-opener detection is string-aware for the common quote characters
      (" ' `) so a `//` or `#` inside a string literal is not mistaken for a
      comment, but it does not model the string rules of every language (e.g.,
      heredocs, raw strings, regex literals). A stray false positive is harmless
      noise that the reviewer ignores, while a comment that the extractor misses
      is never reviewed.
    - The prose test for a string literal is a heuristic: at least three words
      of letters, which make up most of its tokens, and no leading SQL keyword.
      A command or a list of CSS classes can pass it, and the reader drops
      such a line. A string concatenated over several lines is extracted line
      by line, so a phrase split at a `+` is not seen as one. A multi-line
      string of another language, such as a Kotlin raw string, is not
      extracted, except a Python triple-quoted string, which counts as a block
      comment.
    - A JSX element is recognized where an expression starts, after an
      operator, an opening bracket, `return`, `yield`, or `default`, and only
      when its closing tag matches its opening tag, so a TypeScript generic
      such as `<T,>` is not read as an element. JSX in a `.ts` file is not
      read, since TypeScript does not allow it there. A regular expression
      literal that holds a quote or a backtick can hide the text after it on
      its line, or a template literal.
    - LaTeX (`.tex`) is reviewed as prose (its body and `%` comments, with markup
      the reviewer ignores) against the layers repo mode loads, which never
      include the LaTeX layer. `/ai-slop:review` with that layer remains the tool
      for citations, BibTeX, and section-aware checks.
"""
import bisect
import fnmatch
import html
import os
import re
import subprocess
import sys
from pathlib import Path

# Per-language comment syntax: (line_markers, block_pairs). A block pair is
# (open, close). Order within line_markers/block_openers does not matter. The
# scanner picks the earliest match on the line.
HASH = (('#',), ())
SLASH = (('//',), (('/*', '*/'),))
SLASH_HASH = (('//', '#'), (('/*', '*/'),))
BLOCK_ONLY = ((), (('/*', '*/'),))
HTML = ((), (('<!--', '-->'),))
SQL = (('--',), (('/*', '*/'),))
LUA = (('--',), (('--[[', ']]'),))
SEMI = ((';',), ())
JSON = ((), ())
PY = (('#',), (('"""', '"""'), ("'''", "'''")))

# Extension (lowercased, no dot) -> comment spec.
COMMENT_SPECS = {
    # hash-comment scripts and config
    'py': PY, 'pyi': PY, 'rb': HASH, 'sh': HASH, 'bash': HASH, 'zsh': HASH,
    'fish': HASH, 'ps1': HASH, 'yaml': HASH, 'yml': HASH, 'toml': HASH,
    'ini': HASH, 'cfg': HASH, 'conf': HASH, 'properties': HASH, 'env': HASH,
    'r': HASH, 'pl': HASH, 'pm': HASH, 'tf': HASH, 'tfvars': HASH, 'mk': HASH,
    'cmake': HASH, 'dockerfile': HASH, 'gitignore': HASH, 'gitattributes': HASH,
    'editorconfig': HASH,
    # slash-comment source
    'java': SLASH, 'kt': SLASH, 'kts': SLASH, 'groovy': SLASH, 'gradle': SLASH,
    'js': SLASH, 'mjs': SLASH, 'cjs': SLASH, 'jsx': SLASH, 'ts': SLASH,
    'tsx': SLASH, 'c': SLASH, 'h': SLASH, 'cc': SLASH, 'cpp': SLASH, 'cxx': SLASH,
    'hpp': SLASH, 'cs': SLASH, 'go': SLASH, 'rs': SLASH, 'swift': SLASH,
    'scala': SLASH, 'dart': SLASH, 'json5': SLASH, 'jsonc': SLASH,
    'scss': SLASH, 'less': SLASH, 'css': BLOCK_ONLY, 'php': SLASH_HASH,
    # markup (block only)
    'html': HTML, 'htm': HTML, 'xml': HTML, 'xhtml': HTML, 'vue': HTML,
    'svelte': HTML,
    # JSON without comments: a web app manifest, and a translation catalog in
    # a locale directory (see JSON_TEXT_DIRS); other JSON is skipped
    'webmanifest': JSON, 'json': JSON,
    # other line-comment families
    'sql': SQL, 'lua': LUA, 'el': SEMI, 'lisp': SEMI, 'clj': SEMI, 'cljs': SEMI,
}

# Files that the extension does not identify, matched on the full basename.
NAME_SPECS = {
    'Dockerfile': HASH, 'Makefile': HASH, 'makefile': HASH, 'CMakeLists.txt': HASH,
    '.gitignore': HASH, '.gitattributes': HASH, '.editorconfig': HASH,
    '.dockerignore': HASH, '.npmignore': HASH, '.env': HASH,
}

PROSE_EXTS = {'md', 'markdown', 'mdx', 'txt', 'text', 'rst', 'adoc', 'asciidoc', 'org', 'tex',
              'feature'}

# Lockfiles and other tracked-but-not-prose files, matched on the basename.
SKIP_NAMES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.lock',
    'Cargo.lock', 'poetry.lock', 'Gemfile.lock', 'go.sum', 'gradle.lockfile',
}

# Directories skipped in both modes: pruned from the walk of a non-git tree and
# filtered out of the `git ls-files` list (see in_denylisted_dir).
DENY_DIRS = {
    '.git', 'node_modules', 'build', 'dist', 'out', 'target', '.gradle', '.idea',
    '.vscode', 'vendor', '__pycache__', '.venv', 'venv', '.next', '.angular',
    '.nuxt', 'coverage', 'bin', 'obj', '_vendor', '.mypy_cache', '.pytest_cache',
    'fixtures', 'testdata',
}

MAX_BYTES = 1_000_000  # skip a file larger than this (generated/vendored blobs)
DEFAULT_COMMIT_LIMIT = 200  # most recent N commits scanned when --commits is unset
# Standard git trailer lines: metadata, not hand-written prose, so not reviewed.
TRAILER_RE = re.compile(
    r'^(?:Co-authored-by|Signed-off-by|Reviewed-by|Acked-by|Tested-by|'
    r'Reported-by|Suggested-by|Reviewed-on|Change-Id|Cc|Fixes|Closes|Refs|'
    r'Link|See-also):',
    re.IGNORECASE,
)
GENERATED_RE = re.compile(
    r'@generated|do not edit|auto-?generated|code generated by|generated by',
    re.IGNORECASE,
)
HEAD_LINES = 10  # a generated-file marker is looked for in the first N lines
# Words after a marker such as "generated by" that say the file was edited by
# hand since, as in "generated by `ng new` and then tuned for this project".
EDITED_RE = re.compile(
    r'\b(?:then|since|afterwards|later)\b|\b(?:edited|modified|tuned|adapted|customi[sz]ed|maintained)\b',
    re.IGNORECASE)
PROSE_COMMENT_OPENERS = ('<!--', '%')  # comment openers in a prose file
# Files that are tracked text but not prose: dependency pins, license texts.
SKIP_NAME_RE = re.compile(
    r'^(?:requirements[^/]*\.txt|constraints[^/]*\.txt|robots\.txt'
    r'|(?:LICENSE|LICENCE|COPYING|NOTICE)(?:\.[^/]*)?)$',
    re.IGNORECASE,
)
INDENTED_RE = re.compile(r'^(?: {4,}|\t)\S')
LIST_ITEM_RE = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s+')
QUOTE_CHARS = ('"', "'", '`')
DECORATION_RE = re.compile(r'^[*/!]+\s?')  # leading ` * `, `///`, `//!` decoration

# Comment specs of files whose quotes do not delimit program text: attribute
# values in markup, values in CSS, and quoted symbols in Lisp.
NO_STRING_SPECS = (HTML, BLOCK_ONLY, SEMI)
# Directories and file names of tests, whose strings are not read as prose.
TEST_DIRS = {'test', 'tests', '__tests__', 'spec', 'specs', 'e2e'}
TEST_NAME_RE = re.compile(
    r'^(?:test_[^/]*\.py|[^/]*_test\.(?:py|go|rb|exs?)'
    r'|[^/]*\.(?:test|spec)\.[cm]?[jt]sx?'
    r'|[^/]*Tests?\.(?:java|kt|kts|scala|cs|swift|groovy)|[^/]*_spec\.rb)$'
)
STRING_MIN_WORDS = 3  # a string literal with fewer words is not prose
# Markup files whose text between the tags users read. XML is left out, since
# its text is mostly configuration values.
MARKUP_EXTS = {'html', 'htm', 'xhtml', 'vue', 'svelte'}
# JavaScript and TypeScript, whose template literals can span lines.
TEMPLATE_EXTS = {'js', 'mjs', 'cjs', 'jsx', 'ts', 'tsx'}
# The files that can hold JSX. A `.ts` file cannot, and its type assertions
# (`<Type>value`) would read as elements.
JSX_EXTS = {'js', 'mjs', 'cjs', 'jsx', 'tsx'}
JSX_NAME_RE = re.compile(r'[A-Za-z_$][\w$.:-]*')
JSX_CLOSE_RE = re.compile(r'</\s*([A-Za-z_$][\w$.:-]*)?\s*>')
# The characters after which a `<` in code starts a JSX element, as in
# `return (<p>`, `x = <p>`, `cond && <p>`, or `() => <p>`.
JSX_LEAD_CHARS = set('(,=?:&|{[!>')
JSX_LEAD_WORD_RE = re.compile(r'(?:^|[^\w$])(?:return|yield|default)\s*$')
JSX_DEPTH_LIMIT = 100
# Attributes whose values users read or hear: `alt`, and any name that ends
# in one of the suffixes, such as `aria-label`, `matTooltip`, or the input
# `toggleAriaLabel` of a component.
TEXT_ATTR_SUFFIXES = ('label', 'tooltip', 'title', 'placeholder', 'hint',
                      'message', 'description', 'text', 'summary')
# The key or named argument before a string literal, as in `label: '...'`,
# `"title": "..."`, or `summary = "..."`.
KEY_BEFORE_RE = re.compile(r'["\']?([\w$-]+)["\']?\s*[:=]\s*$')
# The directories of translation catalogs, whose JSON values users read.
JSON_TEXT_DIRS = {'i18n', 'l10n', 'locale', 'locales', 'lang', 'langs', 'translations', 'messages'}
# Elements whose content is code, an icon name, or graphics rather than text.
SKIP_ELEMENTS = {'script', 'style', 'code', 'pre', 'kbd', 'samp', 'svg', 'math', 'mat-icon'}
TAG_RE = re.compile(r'<(/?)([A-Za-z][\w:.-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>')
ATTR_RE = re.compile(r'([^\s=/>"\']+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')')
MARKUP_HINT_RE = re.compile(r'<[A-Za-z][\w:.-]*[\s/>]')
# A line that opens a CSS rule, sets a property, or holds a whole rule, in a
# template literal.
CSS_HINT_RE = re.compile(
    r'\{\s*$|^\s*[\w-]+\s*:\s*[^;{}\n]+;\s*$|\{[^{}\n]*:[^{}\n]*\}', re.M)
MARKUP_COMMENT_RE = re.compile(r'<!--.*?(?:-->|$)', re.S)
# Interpolations ({{ x }}, ${x}), Angular control flow (@if (...) {, @let ...;),
# Svelte blocks ({#if x}), and the braces that close them: not text.
INTERPOLATION_RE = re.compile(r'\{\{.*?\}\}|\$\{(?:[^{}]|\{[^{}]*\})*\}', re.S)
CONTROL_FLOW_RE = re.compile(
    r'@(?:else\s+if|if|else|for|switch|case|default|empty|defer|placeholder|loading|error)'
    r'\b\s*(?:\((?:[^()]|\((?:[^()]|\([^()]*\))*\))*\))?\s*\{?|@let\b[^;]*;|\{[^{}]*\}|[{}]')
# A quoted string in a binding expression or an interpolation, and the start
# that marks it as text for users rather than a key, a format, or a class.
EXPR_STRING_RE = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"")
UI_STRING_RE = re.compile(r'^\s*[A-Z][a-z]')
LETTER_RE = re.compile(r'[^\W\d_]')
WORD_TOKEN_RE = re.compile(
    "^[(\"'`\u201c\u2018\\[]*[A-Za-z][A-Za-z'\u2019-]*[)\"'`\u201d\u2019\\].,;:!?]*$")
SQL_START_RE = re.compile(
    r'^\s*(?:select|insert|update|delete|create|alter|drop|with)\b', re.IGNORECASE)


def in_denylisted_dir(relpath):
    """True if any parent directory of relpath is denylisted (a vendored or build
    directory). Applied to the git file list too, so committed third-party code
    (e.g. a tracked `vendor/` or `_vendor/`) is not reviewed as the prose of the repo."""
    return any(part in DENY_DIRS for part in Path(relpath).parts[:-1])


def list_files(root):
    """Return (relpath, abspath) pairs for the files to consider. Prefers
    `git ls-files` (tracked files, .gitignore honored) and falls back to an os.walk
    with DENY_DIRS pruned when root is not a git working tree. Denylisted
    directories are excluded in both modes."""
    try:
        res = subprocess.run(
            ['git', '-C', str(root), 'ls-files', '-z'],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        res = None
    if res is not None and res.returncode == 0:
        rels = [p for p in res.stdout.split('\0') if p and not in_denylisted_dir(p)]
        return [(r, str(Path(root) / r)) for r in rels]
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in DENY_DIRS]
        for name in filenames:
            ab = Path(dirpath) / name
            out.append((str(ab.relative_to(root)), str(ab)))
    return out


def classify(relpath):
    """Return ('prose'|'comment'|'skip', spec_or_None) for a path."""
    name = os.path.basename(relpath)
    if name in SKIP_NAMES or SKIP_NAME_RE.match(name):
        return ('skip', None)
    if name in NAME_SPECS:
        return ('comment', NAME_SPECS[name])
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    if ext in PROSE_EXTS:
        return ('prose', None)
    if ext == 'json' and not any(part.lower() in JSON_TEXT_DIRS
                                 for part in Path(relpath).parts[:-1]):
        return ('skip', None)
    if ext in COMMENT_SPECS:
        return ('comment', COMMENT_SPECS[ext])
    return ('skip', None)


def looks_generated(text, spec=None):
    """True if a generated-file marker is in the first HEAD_LINES lines on a
    comment line (the comment openers for a source or config file
    per `spec`, or `<!--` / `%` for a prose file, where `spec` is None), or if
    one of those lines carries the `@generated` tag or the uppercase
    `DO NOT EDIT` banner, the two forms generators emit regardless of language.
    A prose line that merely
    mentions the phrase is not a marker."""
    if spec is None:
        openers = PROSE_COMMENT_OPENERS
    else:
        line_markers, block_pairs = spec
        openers = tuple(line_markers) + tuple(op for op, _ in block_pairs) + ('*', '/', '!')
    for line in text.splitlines()[:HEAD_LINES]:
        m = GENERATED_RE.search(line)
        if not m:
            continue
        token = m.group(0)
        if token.lower() == '@generated' or token == 'DO NOT EDIT':
            return True
        if line.lstrip().startswith(openers) and not EDITED_RE.search(line, m.end()):
            return True
    return False


def is_test_path(relpath):
    """True if relpath is a test file: under a test directory (TEST_DIRS) or
    named as a test by a common convention (TEST_NAME_RE)."""
    path = Path(relpath)
    return (any(part in TEST_DIRS for part in path.parts[:-1])
            or bool(TEST_NAME_RE.match(path.name)))


def prose_literal(content):
    """True if the content of a string literal reads as prose: at least
    STRING_MIN_WORDS whitespace-separated tokens are words of letters, they make
    up at least 60 percent of the tokens, at least one letter is lowercase, and
    the string does not start with an SQL keyword."""
    tokens = content.split()
    words = sum(1 for t in tokens if WORD_TOKEN_RE.match(t))
    return (words >= STRING_MIN_WORDS and words >= 0.6 * len(tokens)
            and any(c.islower() for c in content)
            and not SQL_START_RE.match(content))


def find_opener(line, start, line_markers, block_openers, literals=None):
    """Scan line from `start` for the earliest comment opener that lies outside a
    string literal. Returns (index, 'line'|'block', marker) or None. String-aware
    for the common quote characters. A block opener (e.g. Python `\"\"\"`) is
    tested before the quote-state update, so a triple-quote is not mistaken for
    a one-character string. When `literals` is a list, the (start, end) span of
    each string literal that closes before the opener is appended to it, with
    both quote characters inside the span."""
    i, n, quote, qstart = start, len(line), None, start
    while i < n:
        c = line[i]
        if quote is not None:
            if c == '\\':
                i += 2
                continue
            if c == quote:
                quote = None
                if literals is not None:
                    literals.append((qstart, i + 1))
            i += 1
            continue
        for m in block_openers:
            if line.startswith(m, i):
                return (i, 'block', m)
        for m in line_markers:
            if line.startswith(m, i):
                return (i, 'line', m)
        if c in QUOTE_CHARS:
            quote, qstart = c, i
        i += 1
    return None


def clean(text):
    """Strip whitespace and a leading comment-decoration run from comment text."""
    return DECORATION_RE.sub('', text.strip()).strip()


def extract_comments(text, spec, strings=False):
    """Yield (lineno, text, source) for the comment content of a source/config
    file, where source is 'comment', and with `strings` also for each string
    literal on one line that reads as prose (prose_literal), where source is
    'string' and the text keeps its quote characters. Items on one line come in
    the order of their columns. `spec` is (line_markers, block_pairs)."""
    line_markers, block_pairs = spec
    block_openers = [op for op, _ in block_pairs]
    close_for = {op: cl for op, cl in block_pairs}
    in_block_close = None
    for lineno, raw in enumerate(text.split('\n'), 1):
        line = raw.rstrip('\r')
        if lineno == 1 and line.startswith('#!'):
            continue  # a shebang is an interpreter directive, not prose
        pos = 0
        while True:
            if in_block_close is not None:
                ci = line.find(in_block_close, pos)
                if ci == -1:
                    yield lineno, clean(line[pos:]), 'comment'
                    break
                yield lineno, clean(line[pos:ci]), 'comment'
                pos = ci + len(in_block_close)
                in_block_close = None
                continue
            literals = [] if strings else None
            ev = find_opener(line, pos, line_markers, block_openers, literals)
            for a, b in literals or ():
                content = line[a + 1:b - 1]
                key = KEY_BEFORE_RE.search(line, 0, a)
                if prose_literal(content) or (
                        key and is_text_attr(key.group(1)) and LETTER_RE.search(content)):
                    yield lineno, line[a:b], 'string'
            if ev is None:
                break
            idx, kind, marker = ev
            if kind == 'line':
                yield lineno, clean(line[idx + len(marker):]), 'comment'
                break
            in_block_close = close_for[marker]
            pos = idx + len(marker)


def json_text(text, manifest=False):
    """Return the (lineno, text, 'string') items of a JSON file: the string
    values (not the keys) that hold a letter, with their quotes. In a web app
    manifest, only the values of `name`, `short_name`, and the text keys
    (is_text_attr) count, since the others are colors, paths, and sizes."""
    items = []
    for lineno, line in enumerate(text.split('\n'), 1):
        literals = []
        find_opener(line, 0, (), (), literals)
        for a, b in literals:
            content = INTERPOLATION_RE.sub(' ', line[a + 1:b - 1])
            if line[b:].lstrip().startswith(':') or not LETTER_RE.search(content):
                continue
            if manifest:
                key = KEY_BEFORE_RE.search(line, 0, a)
                if not key or not (key.group(1) in ('name', 'short_name') or is_text_attr(key.group(1))):
                    continue
            items.append((lineno, line[a:b], 'string'))
    return items


def blank_spans(text, spans):
    """`text` with each (start, end) span blanked out except its line breaks."""
    parts, last = [], 0
    for a, b in spans:
        parts += [text[last:a], re.sub(r'[^\n]', ' ', text[a:b])]
        last = b
    return ''.join(parts) + text[last:]


def _blank(m):
    """The matched text with every character but the line breaks as a space,
    so that offsets and line numbers stay valid."""
    return re.sub(r'[^\n]', ' ', m.group())


def markup_text(src, first_line=1):
    """Return (lineno, text, 'string') items for the text of markup: the text
    between the tags, one item per line between `>` and `<` as markers, and
    the value of each attribute that users read (is_text_attr), with its
    quote characters. Comments,
    interpolations, Angular control flow, and the content of SKIP_ELEMENTS are
    left out, character references are decoded, and an item without a letter
    is dropped. `first_line` is the line number of the first line of `src`."""
    src = MARKUP_COMMENT_RE.sub(_blank, src)
    starts = [0] + [m.end() for m in re.finditer('\n', src)]

    def line_of(offset):
        return first_line + bisect.bisect_right(starts, offset) - 1

    pieces, attrs = {}, []

    def add_strings(expr, offset):
        for q in EXPR_STRING_RE.finditer(expr):
            if UI_STRING_RE.match(q.group()[1:]):
                attrs.append((line_of(offset + q.start()), q.group()))

    for m in INTERPOLATION_RE.finditer(src):
        if m.group().startswith('{{'):
            add_strings(m.group(), m.start())
    src = INTERPOLATION_RE.sub(_blank, src)
    src = CONTROL_FLOW_RE.sub(_blank, src)

    def add_text(a, b):
        offset = a
        for part in src[a:b].split('\n'):
            if part.strip():
                pieces.setdefault(line_of(offset), []).append(part)
            offset += len(part) + 1

    pos, n = 0, len(src)
    while pos < n:
        i = src.find('<', pos)
        if i == -1:
            add_text(pos, n)
            break
        add_text(pos, i)
        if src.startswith(('<!', '<?'), i):  # a declaration or processing instruction
            j = src.find('>', i)
            pos = n if j == -1 else j + 1
            continue
        m = TAG_RE.match(src, i)
        if not m:
            add_text(i, i + 1)
            pos = i + 1
            continue
        name = m.group(2).lower()
        for a in ATTR_RE.finditer(m.group(3)):
            attr = a.group(1).lower()
            bound = attr.startswith(('[', ':', 'v-bind:'))
            attr = re.sub(r'^(?:v-bind:|:|attr\.)', '', attr.strip('[]'))
            attr = attr[len('attr.'):] if attr.startswith('attr.') else attr
            if not is_text_attr(attr):
                continue
            quote = '"' if a.group(2) is not None else "'"
            raw = a.group(2) if quote == '"' else a.group(3)
            value_at = m.start(3) + a.start(2 if quote == '"' else 3)
            if bound:
                add_strings(raw, value_at)
                continue
            value = ' '.join(html.unescape(raw).split())
            if LETTER_RE.search(value):
                attrs.append((line_of(value_at), quote + value + quote))
        pos = m.end()
        if not m.group(1) and name in SKIP_ELEMENTS and not m.group(3).rstrip().endswith('/'):
            close = re.compile(r'</' + re.escape(name) + r'\s*>', re.IGNORECASE).search(src, pos)
            pos = close.start() if close else n
    texts = []
    for lineno, parts in pieces.items():
        text = ' '.join(html.unescape(' '.join(parts)).split())
        if LETTER_RE.search(text):
            texts.append((lineno, '>' + text + '<'))
    return [(ln, t, 'string') for ln, t in sorted(attrs + texts, key=lambda item: item[0])]


def _skip_js_token(text, i):
    """If a comment, a quoted string, or a template literal of JavaScript
    starts at offset i, return the offset after it, else None. A quoted string
    ends at a line break, and a template literal may hold `${...}` expressions
    with braces and nested template literals."""
    n = len(text)
    if text.startswith('//', i):
        j = text.find('\n', i)
        return n if j == -1 else j
    if text.startswith('/*', i):
        j = text.find('*/', i + 2)
        return n if j == -1 else j + 2
    c = text[i]
    if c in '"\'':
        j = i + 1
        while j < n and text[j] not in (c, '\n'):
            j += 2 if text[j] == '\\' else 1
        return min(j + 1, n)
    if c == '`':
        j, depth = i + 1, 0
        while j < n:
            if text[j] == '\\':
                j += 2
                continue
            if depth == 0 and text[j] == '`':
                return j + 1
            if text.startswith('${', j):
                depth += 1
                j += 2
                continue
            if depth and text[j] == '{':
                depth += 1
            elif depth and text[j] == '}':
                depth -= 1
            j += 1
        return n
    return None


def template_spans(text):
    """Return the (start, end) offsets of the template literals of JavaScript or
    TypeScript source that span lines, backticks included. Comments and quoted
    strings are skipped. Regular expression literals are not modeled."""
    spans, i, n = [], 0, len(text)
    while i < n:
        end = _skip_js_token(text, i)
        if end is None:
            i += 1
            continue
        if text[i] == '`' and '\n' in text[i:end]:
            spans.append((i, end))
        i = end
    return spans


def _jsx_lead(text, i):
    """True if the `<` at offset i can start a JSX element: a letter or `>`
    follows it, and an operator, an opening bracket, `return`, `yield`, or
    `default` precedes it."""
    if i + 1 >= len(text) or not (text[i + 1].isalpha() or text[i + 1] == '>'):
        return False
    j = i - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    return j < 0 or text[j] in JSX_LEAD_CHARS or bool(JSX_LEAD_WORD_RE.search(text, 0, j + 1))


def _jsx_expr_end(text, j, events, owner, depth):
    """Parse the JSX expression `{...}` at offset j. Appends ('string', owner,
    start, end) for each string or template literal in it, ('comment', start,
    end) for each comment, and the events of the JSX elements nested in it.
    `owner` is the name of the attribute that the expression is the value of,
    or None for a child. Returns the offset after the closing brace, or None."""
    k, d, n = j, 0, len(text)
    while k < n:
        end = _skip_js_token(text, k)
        if end is not None:
            kind = 'comment' if text[k] == '/' else 'string'
            events.append((kind, owner, k, end))
            k = end
            continue
        c = text[k]
        if c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                return k + 1
        elif c == '<' and _jsx_lead(text, k):
            end = _jsx_element(text, k, events, depth + 1)
            if end is not None:
                k = end
                continue
        k += 1
    return None


def _jsx_element(text, i, events, depth=0):
    """Parse the JSX element or fragment that starts with the `<` at offset i.
    On success, append its events and return the offset after it. Return None
    and append nothing when the text is not an element whose closing tag
    matches its opening tag. The events are ('text', element, start, end) for
    the text between tags, ('attr', name, start, end) for a quoted attribute
    value with its quotes, ('expr', owner, start, end) for an expression, and
    those of _jsx_expr_end."""
    n = len(text)
    if depth > JSX_DEPTH_LIMIT:
        return None
    local = []
    j = i + 1
    if j < n and text[j] == '>':
        name, j = '', j + 1
    else:
        m = JSX_NAME_RE.match(text, j)
        if not m:
            return None
        name, j = m.group(), m.end()
        while True:
            while j < n and text[j].isspace():
                j += 1
            if j >= n:
                return None
            if text.startswith('/>', j):
                events.extend(local)
                return j + 2
            if text[j] == '>':
                j += 1
                break
            if text[j] == '{':
                end = _jsx_expr_end(text, j, local, '', depth)
                if end is None:
                    return None
                j = end
                continue
            a = JSX_NAME_RE.match(text, j)
            if not a:
                return None
            attr, j = a.group(), a.end()
            while j < n and text[j].isspace():
                j += 1
            if j < n and text[j] == '=':
                j += 1
                while j < n and text[j].isspace():
                    j += 1
                if j < n and text[j] in '"\'':
                    q = text.find(text[j], j + 1)
                    if q == -1:
                        return None
                    local.append(('attr', attr, j, q + 1))
                    j = q + 1
                elif j < n and text[j] == '{':
                    end = _jsx_expr_end(text, j, local, attr, depth)
                    if end is None:
                        return None
                    local.append(('expr', attr, j, end))
                    j = end
                elif j < n and text[j] == '<':
                    end = _jsx_element(text, j, local, depth + 1)
                    if end is None:
                        return None
                    j = end
                else:
                    return None
    start = j
    while j < n:
        if text.startswith('</', j):
            m = JSX_CLOSE_RE.match(text, j)
            if not m or (m.group(1) or '') != name:
                return None
            local.append(('text', name, start, j))
            events.extend(local)
            return m.end()
        if text[j] == '<' and j + 1 < n and (text[j + 1].isalpha() or text[j + 1] == '>'):
            end = _jsx_element(text, j, local, depth + 1)
            if end is not None:
                local.append(('text', name, start, j))
                j = start = end
                continue
        elif text[j] == '{':
            end = _jsx_expr_end(text, j, local, None, depth)
            if end is None:
                return None
            local.append(('text', name, start, j))
            local.append(('expr', None, j, end))
            j = start = end
            continue
        j += 1
    return None


def jsx_spans(text):
    """Return (spans, events) for the JSX of a JavaScript or TSX source: the
    (start, end) offsets of each outermost element, and the events of
    _jsx_element for all of them."""
    spans, events, i, n = [], [], 0, len(text)
    while i < n:
        end = _skip_js_token(text, i)
        if end is not None:
            i = end
            continue
        if text[i] == '<' and _jsx_lead(text, i):
            local = []
            end = _jsx_element(text, i, local)
            if end is not None:
                spans.append((i, end))
                events += local
                i = end
                continue
        i += 1
    return spans, events


def is_text_attr(name):
    """True for an attribute that users read: `alt`, or a name that ends in
    one of TEXT_ATTR_SUFFIXES, such as `aria-label` or `matTooltip`."""
    name = name.lower()
    return name == 'alt' or name.endswith(TEXT_ATTR_SUFFIXES)


def jsx_text(text, events, strings=True):
    """Return the (lineno, text, source) items of the JSX events of one file:
    the text between tags, line by line between `>` and `<`, and the quoted
    values of text
    attributes (is_text_attr), when `strings` is true, and the comments in
    expressions in any case. A string in an expression is emitted with its
    quotes when it is the whole value of a child or of a text attribute, when
    it is in such a value and starts with a capital letter (UI_STRING_RE), or
    when it reads as prose (prose_literal)."""
    starts = [0] + [m.end() for m in re.finditer('\n', text)]

    def line_of(offset):
        return bisect.bisect_right(starts, offset)

    items = []
    sole = {}
    for kind, owner, a, b in events:
        if kind == 'expr':
            sole[(owner, text[a + 1:b - 1].strip())] = True
    for kind, owner, a, b in events:
        if kind == 'comment':
            items += [(ln + line_of(a) - 1, t, src)
                      for ln, t, src in extract_comments(text[a:b], SLASH) if t]
        if not strings:
            continue
        if kind == 'text' and owner.lower() not in SKIP_ELEMENTS:
            offset = a
            for part in text[a:b].split('\n'):
                line = ' '.join(html.unescape(part).split())
                if LETTER_RE.search(line):
                    items.append((line_of(offset), '>' + line + '<', 'string'))
                offset += len(part) + 1
        elif kind == 'attr' and is_text_attr(owner):
            value = ' '.join(html.unescape(text[a + 1:b - 1]).split())
            if LETTER_RE.search(value):
                items.append((line_of(a), text[a] + value + text[a], 'string'))
        elif kind == 'string':
            literal = text[a:b]
            if literal.startswith('`') and '\n' in literal:
                items += template_text(text, a, b, True)
                continue
            content = INTERPOLATION_RE.sub(' ', literal[1:-1])
            ui = owner is None or (owner and is_text_attr(owner))
            if ((ui and sole.get((owner, literal)) and LETTER_RE.search(content))
                    or (ui and UI_STRING_RE.match(content)) or prose_literal(content)):
                items.append((line_of(a), literal, 'string'))
    return items


def template_text(text, start, end, strings=True):
    """Return the (lineno, text, source) items of one multi-line template
    literal (`text[start:end]`, backticks included). A literal that holds
    markup yields its `<!-- -->` comments and, with `strings`, its text
    (markup_text). Any other literal yields its `/* */` comments, and, with
    `strings`, unless it holds CSS, the lines that hold a letter, each in
    backticks, when the whole literal reads as prose (prose_literal)."""
    content = text[start + 1:end - 1]
    first_line = text.count('\n', 0, start + 1) + 1
    markup = bool(MARKUP_HINT_RE.search(content))
    items = [(ln + first_line - 1, t, src)
             for ln, t, src in extract_comments(content, HTML if markup else BLOCK_ONLY) if t]
    if not strings:
        return items
    if markup:
        return items + markup_text(content, first_line)
    body = INTERPOLATION_RE.sub(_blank, re.sub(r'/\*.*?\*/', _blank, content, flags=re.S))
    if CSS_HINT_RE.search(body) or not prose_literal(body):
        return items
    for k, line in enumerate(body.split('\n')):
        line = ' '.join(line.split())
        if LETTER_RE.search(line):
            items.append((first_line + k, '`' + line + '`', 'string'))
    return items


FENCE_RE = re.compile(r'^\s*(?P<fence>`{3,}|~{3,})\s*(?P<info>[^`]*)$')

# Fence info strings that mark the contents as prose, not code. A template
# quoted in such a fence is content and is reviewed.
PROSE_FENCE_INFOS = {'markdown', 'md', 'mdx', 'text', 'txt', 'plain'}


def extract_prose(text, is_markdown):
    """Yield (lineno, line) for the non-blank lines of a prose file. In
    Markdown, fenced code blocks are skipped, except that a fence with a prose
    format as its info string (see PROSE_FENCE_INFOS) has its contents
    reviewed as prose. Fences nest. A bare code fence inside a prose fence is
    skipped, and a fence closes only on a bare marker of its character with at
    least its length, per CommonMark. A leading YAML front-matter block and an
    indented code block (four spaces or a tab after a blank line, when the
    previous text is not a list item or list continuation) are skipped too."""
    lines = text.splitlines()
    start = 0
    if is_markdown and lines and lines[0].strip() == '---':
        for j in range(1, len(lines)):
            if lines[j].strip() in ('---', '...'):
                start = j + 1
                break
    stack = []  # (fence_marker, contents_are_prose) per open fence
    in_indented = False
    prev_blank = False
    prev_nonblank = ''
    for i in range(start, len(lines)):
        line = lines[i]
        lineno = i + 1
        if is_markdown:
            m = FENCE_RE.match(line)
            if m:
                fence, info = m.group('fence'), m.group('info').strip()
                if (stack and not info and fence[0] == stack[-1][0][0]
                        and len(fence) >= len(stack[-1][0])):
                    stack.pop()
                else:
                    lang = info.split()[0].lower() if info else ''
                    stack.append((fence, lang in PROSE_FENCE_INFOS))
                prev_blank, prev_nonblank, in_indented = False, line, False
                continue
            if any(not prose for _, prose in stack):
                continue
            if in_indented:
                if not line.strip() or INDENTED_RE.match(line):
                    continue
                in_indented = False
            elif (prev_blank and INDENTED_RE.match(line)
                    and not LIST_ITEM_RE.match(prev_nonblank)
                    and not prev_nonblank[:1].isspace()):
                in_indented = True
                continue
        if not line.strip():
            prev_blank = True
            continue
        prev_blank, prev_nonblank = False, line
        yield lineno, line


def read_text(abspath):
    """Read a file as UTF-8 text, or return None if it is too large, binary, or
    unreadable."""
    try:
        if os.path.getsize(abspath) > MAX_BYTES:
            return None
        with open(abspath, 'rb') as fh:
            data = fh.read()
    except OSError:
        return None
    if b'\x00' in data:
        return None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def commit_selector(spec):
    """Translate a --commits spec into the arguments that select commits for `git log`. A count
    (int or all-digit string) becomes `-n N`, `all` selects the full history (no
    limiter), and anything else is passed through to `git log` as a revision range
    (e.g. `main..HEAD`)."""
    if isinstance(spec, int):
        return ['-n', str(spec)]
    if spec == 'all':
        return []
    if spec.isdigit():
        return ['-n', spec]
    return [spec]


class CommitSpecError(Exception):
    """git rejected the --commits selector (an unresolvable range)."""


def list_commits(root, spec):
    """Return [(short_sha, message)] for the selected commits, newest first.
    Returns [] when commit scanning is off (spec is None), when root is not a git
    work tree or git is unavailable, or when there are no commits. Raises
    CommitSpecError when the repository has commits but git rejects the
    selector, so a mistyped range does not pass as a clean "0 commits" run.
    Merge commits are excluded."""
    if spec is None:
        return []
    try:
        head = subprocess.run(
            ['git', '-C', str(root), 'rev-parse', '--verify', '--quiet', 'HEAD'],
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        return []
    if head.returncode != 0:
        return []  # not a work tree, or no commits yet
    cmd = (['git', '-C', str(root), 'log', '--no-merges', '-z', '--format=%H%n%B']
           + commit_selector(spec))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        detail = res.stderr.strip().splitlines()
        raise CommitSpecError(detail[-1] if detail else f'git log exited {res.returncode}')
    out = []
    for record in res.stdout.split('\0'):
        record = record.strip('\n')
        if not record:
            continue
        sha, _, body = record.partition('\n')
        out.append((sha[:9], body))
    return out


def extract_commit_message(message):
    """Yield (lineno, line) for the non-blank, non-trailer lines of a commit
    message. Line 1 is the subject. Trailer lines (Co-authored-by, ...) are
    dropped because they are metadata, not prose."""
    for lineno, raw in enumerate(message.split('\n'), 1):
        line = raw.rstrip('\r').rstrip()
        if line.strip() and not TRAILER_RE.match(line):
            yield lineno, line


def extract_file(relpath, text, strings=True, kind=None, spec=None):
    """Return the (lineno, text, source) triples that a scan emits for one file,
    where source is 'prose', 'comment', or 'string'. `kind` and `spec` default
    to classify(relpath), and a caller that reads a file that classify skips
    passes kind='prose' to read it as plain text. Strings are extracted only
    when `strings` is true and the file is not a test (is_test_path): the
    string literals on one line where the comment syntax admits them
    (NO_STRING_SPECS), the text of a markup file (MARKUP_EXTS), and the
    multi-line template literals of JavaScript and TypeScript (TEMPLATE_EXTS),
    which are blanked out before the comments are read."""
    if kind is None:
        kind, spec = classify(relpath)
    if kind == 'skip':
        return []
    ext = relpath.rsplit('.', 1)[-1].lower() if '.' in relpath else ''
    if kind == 'prose':
        pairs = extract_prose(text, ext in ('md', 'markdown', 'mdx'))
        return [(ln, t, 'prose') for ln, t in pairs if t]
    want = strings and not is_test_path(relpath)
    items = []
    if spec == JSON:
        return json_text(text, ext == 'webmanifest') if want else []
    if ext in MARKUP_EXTS and spec == HTML:
        if want:
            items = markup_text(text)
        want = False
    elif ext in TEMPLATE_EXTS:
        if ext in JSX_EXTS:
            spans, events = jsx_spans(text)
            items += jsx_text(text, events, want)
            text = blank_spans(text, spans)
        spans = template_spans(text)
        for a, b in spans:
            items += template_text(text, a, b, want)
        text = blank_spans(text, spans)
    want = want and spec not in NO_STRING_SPECS
    items += [item for item in extract_comments(text, spec, want) if item[1]]
    return sorted(items, key=lambda item: item[0])


def scan(root, commit_spec=DEFAULT_COMMIT_LIMIT, strings=True, excludes=()):
    """Scan the repo and return (lines, n_files, n_prose, n_comment, n_strings,
    n_commits, generated). Each line is a formatted `relpath:lineno:text`
    string. Commit messages use a `commit <short-sha>` pseudo-path and follow
    the files, newest first. `n_strings` counts the extracted string literals,
    and `generated` lists the relpaths skipped as generated files. A file whose
    relpath matches a pattern in `excludes` is skipped."""
    lines = []
    generated = []
    n_files = n_prose = n_comment = n_strings = 0
    for relpath, abspath in sorted(list_files(root)):
        if any(fnmatch.fnmatch(relpath, pat) for pat in excludes):
            continue
        kind, spec = classify(relpath)
        if kind == 'skip':
            continue
        text = read_text(abspath)
        if text is None:
            continue
        if looks_generated(text, spec):
            generated.append(relpath)
            continue
        emitted = extract_file(relpath, text, strings, kind, spec)
        if not emitted:
            continue
        n_files += 1
        n_prose += kind == 'prose'
        n_comment += kind == 'comment'
        n_strings += sum(1 for item in emitted if item[2] == 'string')
        for ln, t, _ in emitted:
            lines.append(f'{relpath}:{ln}:{t}')
    n_commits = 0
    for sha, message in list_commits(root, commit_spec):
        emitted = [(ln, t) for ln, t in extract_commit_message(message) if t]
        if not emitted:
            continue
        n_commits += 1
        for ln, t in emitted:
            lines.append(f'commit {sha}:{ln}:{t}')
    return lines, n_files, n_prose, n_comment, n_strings, n_commits, generated


def parse_args(argv):
    """Parse argv into (root, commit_spec, strings, excludes). The first bare
    argument is the repo root, --commits=<spec> and --no-commits control commit
    scanning, --no-strings turns off string literals, and each --exclude=<glob>
    adds a pattern of paths to skip. A bad --commits or --exclude value or an
    extra positional argument returns None to signal an error. Other --flags
    are left to the skill layer and ignored here."""
    root, commit_spec, strings, excludes = None, DEFAULT_COMMIT_LIMIT, True, []
    for arg in argv[1:]:
        if arg == '--no-commits':
            commit_spec = None
        elif arg == '--no-strings':
            strings = False
        elif arg.startswith('--exclude='):
            pattern = arg.split('=', 1)[1]
            if not pattern:
                return None
            excludes.append(pattern)
        elif arg.startswith('--commits='):
            val = arg.split('=', 1)[1]
            if val == '' or val.startswith('-'):
                return None  # empty, or a value git would read as an option
            commit_spec = int(val) if val.isdigit() else val
        elif arg.startswith('--'):
            continue  # a skill-layer flag (e.g. --scientific), not ours
        elif root is None:
            root = Path(arg)
        else:
            return None
    return (root or Path('.'), commit_spec, strings, excludes)


def main(argv):
    parsed = parse_args(argv)
    if parsed is None:
        print("scan_repo: usage: scan_repo.py [REPO_ROOT] "
              "[--commits=<N|all|RANGE>] [--no-commits] [--no-strings] "
              "[--exclude=GLOB ...]", file=sys.stderr)
        return 2
    root, commit_spec, strings, excludes = parsed
    if not root.is_dir():
        print(f"scan_repo: not a directory: {root}", file=sys.stderr)
        return 2
    try:
        (lines, n_files, n_prose, n_comment, n_strings, n_commits,
         generated) = scan(root, commit_spec, strings, excludes)
    except CommitSpecError as e:
        print(f"scan_repo: --commits={commit_spec}: {e}", file=sys.stderr)
        return 2
    sys.stdout.write('\n'.join(lines))
    if lines:
        sys.stdout.write('\n')
    print(
        f"scanned {n_files} file(s) with text "
        f"({n_prose} prose, {n_comment} with comments or strings), "
        f"{n_strings} string literal(s), "
        f"and {n_commits} commit message(s); {len(lines)} line(s).",
        file=sys.stderr,
    )
    if generated:
        shown = ', '.join(generated[:20]) + (', ...' if len(generated) > 20 else '')
        print(f"skipped {len(generated)} generated file(s): {shown}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
