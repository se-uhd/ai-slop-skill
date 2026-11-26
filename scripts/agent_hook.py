#!/usr/bin/env python3
"""Hook that checks the result of a tool call of an agent in this repository.

Claude Code (.claude/settings.json) and Codex (.codex/hooks.json) run the
script after a tool call (PostToolUse) and pass the event as JSON on stdin.
The pi extension .pi/extensions/ai-slop-checks.ts passes an event of the same
form. The script reads these fields:

    cwd                   the working directory of the session
    tool_name             Bash (Claude Code, Codex) or bash (pi); Edit,
                          Write, or MultiEdit (Claude Code); apply_patch
                          (Codex); edit or write (pi)
    tool_input.command    the shell command, or the patch of apply_patch
    tool_input.file_path  the edited file (Claude Code)
    tool_input.path       the edited file (pi)

When a shell command runs `git commit` in this repository or in one of its
worktrees, the script checks the commit at HEAD with check_commit_message.py.
It finds the directory of the commit from the `cd <path>` and `git -C <path>`
in the command, and otherwise uses the working directory of the event. When
the tool edits a Markdown file of this repository, the script runs
lint_markdown.py and check_markdown_limits.py on the file. It skips a file in
another repository, a file that git ignores, and the upstream-owned paths
that AGENTS.md lists. The checks run with the scripts of the worktree that
holds the commit or the file.

Exit code 2 returns the violations on stderr to the agent: Claude Code shows
them to the model, Codex replaces the tool result with them, and the pi
extension appends them to the tool result. The glyphs that scan_glyphs.py
finds in the text that an edit inserted do not block. Without a violation, the
script prints them on stdout as `additionalContext` in the JSON that Claude
Code and Codex read, and exits 0. So does a note after a commit in a clone
that has not enabled the Git hook in .githooks/. Exit code 1 reports a failure
of a check itself.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
CHECKER = 'scripts/check_commit_message.py'
LIMITS = 'scripts/check_markdown_limits.py'
LINTER = 'plugins/ai-slop/scripts/lint_markdown.py'
GLYPHS = 'plugins/ai-slop/scripts/scan_glyphs.py'
# The upstream-owned paths of AGENTS.md, which the pymarkdown-skill repository
# syncs into plugins/ai-slop/scripts/.
UPSTREAM_OWNED = ('plugins/ai-slop/scripts/_vendor/', 'plugins/ai-slop/scripts/bundled_licenses/',
                  'plugins/ai-slop/scripts/lint_markdown.py', 'plugins/ai-slop/scripts/check_baseline.py',
                  'plugins/ai-slop/scripts/refresh_vendor.py')
MAX_GLYPH_ROWS = 10

ARGUMENT = r'''(?:"[^"]*"|'[^']*'|[^\s;&|()]+)'''
GIT_COMMIT = re.compile(
    rf'(?<![\w.-])git((?:\s+(?:-[Cc]\s+{ARGUMENT}|-[-\w]+(?:={ARGUMENT})?))*)\s+commit(?![\w-])')
DIRECTORY_OPTION = re.compile(rf'-C\s+({ARGUMENT})')
CD = re.compile(rf'(?:^|[;&|(\n])\s*cd\s+({ARGUMENT})')
PATCH_FILE = re.compile(r'^\*\*\* (Add File|Update File|Delete File|Move to): (.+?)\s*$')


def unquote(argument):
    if len(argument) > 1 and argument[0] in '"\'' and argument[-1] == argument[0]:
        return argument[1:-1]
    return argument


def directory_of(command, match, cwd):
    """Return the directory in which the matched `git commit` runs."""
    directory = cwd
    for cd in CD.finditer(command, 0, match.start()):
        directory = directory / os.path.expanduser(unquote(cd.group(1)))
    for option in DIRECTORY_OPTION.finditer(match.group(1)):
        directory = directory / os.path.expanduser(unquote(option.group(1)))
    return directory if directory.is_dir() else cwd


def git(directory, *args):
    result = subprocess.run(['git', '-C', str(directory), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def common_dir(directory):
    path = git(directory, 'rev-parse', '--path-format=absolute', '--git-common-dir')
    return Path(path).resolve() if path else None


def in_project(directory):
    """Return the root of the worktree of this repository that holds the
    directory, or None for another repository."""
    repository = common_dir(directory)
    if repository is None or repository != common_dir(PROJECT):
        return None
    return Path(git(directory, 'rev-parse', '--show-toplevel')).resolve()


def script(root, relative):
    """Return a script of the worktree, or of this checkout when the
    worktree does not have it."""
    path = root / relative
    return path if path.is_file() else PROJECT / relative


def run(root, relative, *args, cwd=None):
    return subprocess.run([sys.executable, str(script(root, relative)), *args],
                          cwd=cwd or root, capture_output=True, text=True)


def check_commit(command, cwd):
    """Return (violations, failures, notes) for a `git commit` in the
    command. A note names the Git hook while the clone has not enabled it."""
    match = GIT_COMMIT.search(command)
    if not match:
        return [], [], []
    directory = directory_of(command, match, cwd)
    root = in_project(directory)
    if root is None:
        return [], [], []
    notes = [] if git(directory, 'config', 'core.hooksPath') == '.githooks' else [
        'The Git hook of this repository is off in this clone. Enable it with '
        '`git config core.hooksPath .githooks`, so that git checks each message before the commit.']
    result = run(root, CHECKER, '--range', 'HEAD^!', cwd=directory)
    if result.returncode == 1:
        return [result.stderr.rstrip() + '\nRewrite the message with git commit --amend '
                'before the commit is pushed.'], [], notes
    return [], [result.stderr.rstrip()] if result.returncode else [], notes


def patch_edits(patch, cwd):
    """Return {path: inserted text} for the files that an apply_patch patch
    adds, updates, or moves to."""
    edits, current = {}, None
    for line in patch.split('\n'):
        match = PATCH_FILE.match(line)
        if match:
            kind, name = match.groups()
            path = (cwd / os.path.expanduser(name)).resolve()
            if kind == 'Delete File':
                edits.pop(path, None)
                current = None
                continue
            if kind == 'Move to' and current is not None:
                edits[path] = edits.pop(current, '')
            current = path
            edits.setdefault(current, '')
        elif current is not None and line.startswith('+'):
            edits[current] += line[1:] + '\n'
    return edits


def edited_files(event, cwd):
    """Return {path: inserted text} for the files that the tool call edited."""
    tool = (event.get('tool_name') or '').lower()
    tool_input = event.get('tool_input') or {}
    if tool == 'apply_patch':
        return patch_edits(tool_input.get('command') or '', cwd)
    name = tool_input.get('file_path') or tool_input.get('path')
    if tool not in ('edit', 'write', 'multiedit') or not isinstance(name, str):
        return {}
    name = name[1:] if name.startswith('@') else name
    edits = tool_input.get('edits') or []
    inserted = [tool_input.get('content'), tool_input.get('new_string')]
    inserted += [edit.get('new_string') or edit.get('newText') for edit in edits if isinstance(edit, dict)]
    path = (cwd / os.path.expanduser(name)).resolve()
    return {path: '\n'.join(text for text in inserted if isinstance(text, str))}


def glyph_notes(root, relative, inserted):
    """Return the glyphs that scan_glyphs.py finds in the inserted text."""
    if not inserted.strip():
        return []
    with tempfile.TemporaryDirectory() as directory:
        sample = Path(directory) / ('inserted' + Path(relative).suffix)
        sample.write_text(inserted, encoding='utf-8')
        result = run(root, GLYPHS, str(sample), cwd=directory)
    rows = [row.split('\t', 2) for row in result.stdout.splitlines() if row.count('\t') >= 2]
    notes = [f'{relative}: inserted {kind}: {context}' for _, kind, context in rows]
    if len(notes) > MAX_GLYPH_ROWS:
        notes = notes[:MAX_GLYPH_ROWS] + [f'{relative}: {len(rows) - MAX_GLYPH_ROWS} more']
    return notes


def check_markdown(path, inserted):
    """Return (violations, failures, notes) for an edited Markdown file."""
    if path.suffix.lower() != '.md' or not path.is_file():
        return [], [], []
    root = in_project(path.parent)
    if root is None or not path.is_relative_to(root):
        return [], [], []
    relative = path.relative_to(root).as_posix()
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', relative]).returncode == 0
    if relative.startswith(UPSTREAM_OWNED) or ignored:
        return [], [], []
    violations, failures = [], []
    lint = run(root, LINTER, relative)
    if lint.returncode == 1:
        violations.append(lint.stdout.rstrip())
    elif lint.returncode:
        failures.append(f'lint_markdown.py could not check {relative}: {lint.stderr.strip()}')
    limits = run(root, LIMITS, '--root', str(root), relative)
    if limits.returncode == 1:
        violations.append(limits.stderr.rstrip())
    elif limits.returncode:
        failures.append(limits.stderr.rstrip())
    return violations, failures, glyph_notes(root, relative, inserted)


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    tool_input = event.get('tool_input') if isinstance(event, dict) else None
    if not isinstance(tool_input, dict):
        return 0
    cwd = Path(event.get('cwd') or os.getcwd())
    command = tool_input.get('command')
    violations, failures, notes, glyphs = [], [], [], []
    if (event.get('tool_name') or '').lower() == 'bash' and isinstance(command, str):
        violations, failures, notes = check_commit(command, cwd)
    else:
        for path, inserted in edited_files(event, cwd).items():
            found = check_markdown(path, inserted)
            violations += found[0]
            failures += found[1]
            glyphs += found[2]
    if glyphs:
        notes += ['scan_glyphs.py found these glyphs in the inserted text. They do not block. '
                  'Keep a glyph in a quotation or an example, and replace it in prose.'] + glyphs

    advice = '\n'.join(notes)
    if violations:
        sys.stderr.write('\n'.join(violations + failures + ([advice] if advice else [])) + '\n')
        return 2
    if failures:
        sys.stderr.write('\n'.join(failures) + '\n')
        return 1
    if advice:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                                                 'additionalContext': advice}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
