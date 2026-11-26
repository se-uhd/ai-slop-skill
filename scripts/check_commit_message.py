#!/usr/bin/env python3
"""check_commit_message.py <message file> | --range <revision range>

Check commit messages against the format that the section on commit messages
in AGENTS.md describes:

    type(scope)!: description

    - A bullet of at most two lines, with the continuation line indented
      by two spaces.

    Co-Authored-By: Name <address>

The subject follows Conventional Commits 1.0.0 with a type from TYPES, has at
most 72 characters, and does not end with a period. The scope is optional and
is a skill name or one of SCOPES. A release commit has the subject
`chore(release): YYYY-MM_revN`. A blank line and 1 to 5 bullets follow, each
line of a bullet has at most 72 characters, and the trailers form the last
paragraph.

With a message file, the script checks the message as the commit-msg hook in
.githooks/ passes it. It ignores comment lines and the diff that
`git commit --verbose` adds below the scissors line, since git removes both.
With --range, it checks each commit of a revision range, such as
origin/main..HEAD, in the current repository. It skips merges, commits by
Dependabot, and the commits up to the tag LAST_RELEASE_BEFORE_FORMAT, which
were released before the format applied.

Exits 0 when every message follows the format, 1 with each violation on
stderr when a message breaks it, and 2 on a usage error or a failed git
command.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / 'plugins' / 'ai-slop' / 'skills'

TYPES = ('feat', 'fix', 'docs', 'refactor', 'test', 'build', 'ci', 'chore', 'perf', 'revert')
# The scopes besides the skill names: the five rule layers, the helpers under
# plugins/ai-slop/scripts/, the vendored Markdown linter, the plugin,
# marketplace, and pi manifests, and a release.
SCOPES = ('general', 'scientific', 'latex', 'economist', 'ste',
          'scripts', 'vendor', 'manifests', 'release')
MAX_SUBJECT = 72
MAX_LINE = 72
MAX_BULLETS = 5
MAX_BULLET_LINES = 2
LAST_RELEASE_BEFORE_FORMAT = '2026-11_rev9'

SUBJECT = re.compile(r'(?P<type>\w+)(?:\((?P<scope>[^()]*)\))?!?: (?P<description>\S.*)')
RELEASE = re.compile(r'\d{4}-\d{2}(?:_rev[1-9]\d*)?')
TRAILER = re.compile(r'[A-Za-z][A-Za-z0-9-]*: \S')
BULLET = re.compile(r'- \S')
CONTINUATION = re.compile(r'  \S')
SCISSORS = re.compile(r'# -+ >8 -+')
EXAMPLE = (
    'fix(scripts): name the cause of a failed catalog download',
    '',
    '- fetch_tropes.py printed "no catalog" after a DNS or TLS error.',
    '- It now names the cause, such as an HTTP status or a timeout.',
)


class GitError(Exception):
    pass


def allowed_scopes():
    """Return the skill names and SCOPES, sorted."""
    return sorted({path.parent.name for path in SKILLS.glob('*/SKILL.md')} | set(SCOPES))


def clean(text, strip_comments):
    """Return the lines of a message as git stores it, without trailing
    whitespace, repeated blank lines, or blank lines at the start and end.
    With strip_comments, also drop the comment lines and everything below the
    scissors line, which git removes from a message written in an editor."""
    lines = []
    for line in text.replace('\r\n', '\n').split('\n'):
        if strip_comments and SCISSORS.fullmatch(line):
            break
        if strip_comments and line.startswith('#'):
            continue
        line = line.rstrip()
        if line or (lines and lines[-1]):
            lines.append(line)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def check_subject(subject, scopes):
    errors = []
    match = SUBJECT.fullmatch(subject)
    if not match:
        errors.append(f"the subject '{subject}' does not have the form "
                      "'type(scope): description'")
    else:
        kind, scope, description = match.group('type', 'scope', 'description')
        if kind not in TYPES:
            errors.append(f"the type '{kind}' is not one of {', '.join(TYPES)}")
        if scope is not None and scope not in scopes:
            errors.append(f"the scope '{scope}' is not one of {', '.join(scopes)}")
        if scope == 'release' and (kind != 'chore' or not RELEASE.fullmatch(description)):
            errors.append("a release commit has the subject 'chore(release): YYYY-MM_revN'")
    if len(subject) > MAX_SUBJECT:
        errors.append(f'the subject has {len(subject)} characters, more than {MAX_SUBJECT}')
    if subject.endswith('.'):
        errors.append('the subject ends with a period')
    return errors


def check_message(text, scopes, strip_comments=False):
    """Return the violations of the format in one commit message."""
    lines = clean(text, strip_comments)
    if not lines:
        return ['the message is empty']
    errors = check_subject(lines[0], scopes)
    if len(lines) < 3 or lines[1]:
        return errors + ['a blank line and at least one bullet must follow the subject']

    # The trailers, such as Co-Authored-By, form the last paragraph.
    end = len(lines)
    if '' in lines[2:]:
        last_blank = len(lines) - 1 - lines[::-1].index('')
        if all(TRAILER.match(line) for line in lines[last_blank + 1:]):
            end = last_blank

    bullets = 0
    lines_of_bullet = 0
    for number, line in enumerate(lines[2:end], start=3):
        if BULLET.match(line):
            bullets += 1
            lines_of_bullet = 1
        elif CONTINUATION.match(line) and bullets:
            lines_of_bullet += 1
            if lines_of_bullet == MAX_BULLET_LINES + 1:
                errors.append(f'bullet {bullets} has more than {MAX_BULLET_LINES} lines')
        else:
            errors.append(f"line {number} is neither a bullet ('- ') nor the continuation "
                          f"of one (two spaces): '{line}'")
        if len(line) > MAX_LINE:
            errors.append(f'line {number} has {len(line)} characters, more than {MAX_LINE}')
    if not bullets:
        errors.append('the body has no bullet')
    elif bullets > MAX_BULLETS:
        errors.append(f'the body has {bullets} bullets, more than {MAX_BULLETS}')
    return errors


def git(*args):
    result = subprocess.run(['git', *args], capture_output=True)
    if result.returncode:
        raise GitError(result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout.decode('utf-8', 'replace')


def commits(revision_range):
    """Yield the abbreviated hash and the message of each commit in the range
    that the format applies to."""
    tag = f'refs/tags/{LAST_RELEASE_BEFORE_FORMAT}'
    try:
        git('rev-parse', '-q', '--verify', tag)
    except GitError:
        raise GitError(f'the tag {LAST_RELEASE_BEFORE_FORMAT} is missing, so the commits '
                       'before the format cannot be skipped. Fetch it with git fetch --tags.') from None
    log = git('log', '-z', '--no-merges', '--format=%h%x1f%ae%x1f%B',
              revision_range, f'^{tag}', '--')
    for record in filter(None, log.split('\0')):
        sha, email, message = record.split('\x1f', 2)
        if 'dependabot' not in email:
            yield sha, message


def main(argv):
    scopes = allowed_scopes()
    if len(argv) == 3 and argv[1] == '--range' and not argv[2].startswith('-'):
        try:
            results = [(f'commit {sha}', check_message(message, scopes))
                       for sha, message in commits(argv[2])]
        except GitError as error:
            print(f'check_commit_message.py: {error}', file=sys.stderr)
            return 2
    elif len(argv) == 2 and not argv[1].startswith('-'):
        try:
            text = Path(argv[1]).read_text(encoding='utf-8', errors='replace')
        except OSError as error:
            print(f'check_commit_message.py: {error}', file=sys.stderr)
            return 2
        results = [('commit message', check_message(text, scopes, strip_comments=True))]
    else:
        print('usage: check_commit_message.py <message file> | --range <revision range>',
              file=sys.stderr)
        return 2

    failed = False
    for label, errors in results:
        for error in errors:
            print(f'{label}: {error}', file=sys.stderr)
            failed = True
    if failed:
        print('Write the message as the section on commit messages in AGENTS.md '
              'describes, for example:', file=sys.stderr)
        for line in EXAMPLE:
            print(f'  {line}'.rstrip(), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
