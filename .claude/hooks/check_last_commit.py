#!/usr/bin/env python3
"""Claude Code hook that checks the message of a new commit.

.claude/settings.json runs the hook after each Bash command (PostToolUse),
and Claude Code passes the event as JSON on stdin. When the command runs
`git commit` in this repository or in one of its worktrees, the hook checks
the commit at HEAD with scripts/check_commit_message.py. Exit code 2 returns
the violations to Claude Code. The hook finds the directory of the commit
from the `cd <path>` and `git -C <path>` in the command, and otherwise uses
the working directory of the event. A commit in another repository is not
checked.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
CHECKER = PROJECT / 'scripts' / 'check_commit_message.py'
ARGUMENT = r'''(?:"[^"]*"|'[^']*'|[^\s;&|()]+)'''
GIT_COMMIT = re.compile(
    rf'(?<![\w.-])git((?:\s+(?:-[Cc]\s+{ARGUMENT}|-[-\w]+(?:={ARGUMENT})?))*)\s+commit(?![\w-])')
DIRECTORY_OPTION = re.compile(rf'-C\s+({ARGUMENT})')
CD = re.compile(rf'(?:^|[;&|(\n])\s*cd\s+({ARGUMENT})')


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


def common_dir(directory):
    result = subprocess.run(
        ['git', '-C', str(directory), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
        capture_output=True, text=True)
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (event.get('tool_input') or {}).get('command') or ''
    match = GIT_COMMIT.search(command)
    if not match:
        return 0
    directory = directory_of(command, match, Path(event.get('cwd') or os.getcwd()))
    repository = common_dir(directory)
    if repository is None or repository != common_dir(PROJECT):
        return 0
    result = subprocess.run([sys.executable, str(CHECKER), '--range', 'HEAD^!'],
                            cwd=directory, capture_output=True, text=True)
    if result.returncode == 1:
        sys.stderr.write(result.stderr)
        print('Rewrite the message with git commit --amend before the commit is pushed.',
              file=sys.stderr)
        return 2
    if result.returncode:
        sys.stderr.write(result.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
