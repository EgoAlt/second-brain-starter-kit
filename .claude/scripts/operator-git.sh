#!/bin/bash
# Exact read-only git queries for the operator prompt. The operator's allowlist
# permits this script and nothing else git-shaped, because every `git log *` or
# `git diff *` wildcard also permits `--output=<file>`, which overwrites a file.
# Arguments are validated here; flags are never passed through.
#
#   bash .claude/scripts/operator-git.sh recent                 # what changed since yesterday
#   bash .claude/scripts/operator-git.sh renames <basename>     # git rename history for <basename>.md
#   bash .claude/scripts/operator-git.sh folder-date <folder>   # date of the folder's last commit

set -u
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT" || exit 1

usage() {
  echo "usage: operator-git.sh recent | renames <basename> | folder-date <folder>" >&2
  exit 2
}

case "${1:-}" in
  recent)
    [ $# -eq 1 ] || usage
    git log --since=yesterday --name-only --format=%s
    ;;
  renames)
    [ $# -eq 2 ] || usage
    b=$2
    [[ "$b" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "renames: basename must match [A-Za-z0-9._-]+" >&2; exit 2; }
    git log --diff-filter=R --name-status --format= -- "*$b.md"
    ;;
  folder-date)
    [ $# -eq 2 ] || usage
    f=$2
    [[ "$f" =~ ^[A-Za-z0-9._][A-Za-z0-9._/-]*$ ]] || { echo "folder-date: folder must be a plain relative path" >&2; exit 2; }
    [ -d "$f" ] || { echo "folder-date: no such folder: $f" >&2; exit 2; }
    git log -1 --format=%cs -- "$f"
    ;;
  *)
    usage
    ;;
esac
