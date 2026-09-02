#!/bin/bash
# Functions run-operator.sh uses around the agent run: config, lock, snapshot,
# backup, timeout. Deterministic shell, no model involvement, so the recovery
# and backup contract does not depend on what the agent chose to do. Sourced by
# run-operator.sh and exercised by .claude/scripts/tests/test-operator-lib.sh
# against a real temporary git repository.

SNAPSHOT_KEEP=10

config_path() {  # root -> path of the config to read
  if [ -f "$1/.claude/operator/operator.config.json" ]; then
    echo "$1/.claude/operator/operator.config.json"
  else
    echo "$1/.claude/operator/operator.config.example.json"
  fi
}

config_get() {  # file dotted.key default -> value (lists and objects are not supported)
  python3 -c '
import json, sys
path, key, default = sys.argv[1:4]
try:
    node = json.load(open(path))
    for part in key.split("."):
        node = node[part]
    print(str(node).lower() if isinstance(node, bool) else node)
except Exception:
    print(default)
' "$1" "$2" "$3"
}

require_head() {  # refuse to operate on a repository with no commits
  git rev-parse --verify HEAD >/dev/null 2>&1 && return 0
  echo "run-operator: this repository has no commits yet. Make the initial commit first; a snapshot needs a parent and a backup needs a branch." >&2
  return 1
}

acquire_lock() {  # root -> 0 if acquired, 1 if another run holds it
  local lock="$1/.claude/.operator-runs/lock"
  mkdir -p "$1/.claude/.operator-runs"
  if mkdir "$lock" 2>/dev/null; then
    echo $$ > "$lock/pid"
    return 0
  fi
  echo "run-operator: another run holds $lock (pid $(cat "$lock/pid" 2>/dev/null)). If that run is dead, remove the lock directory." >&2
  return 1
}

release_lock() {  # root
  rm -rf "$1/.claude/.operator-runs/lock"
}

snapshot_create() {  # root stamp -> prints the snapshot ref
  # A durable snapshot of the whole working tree, untracked files included,
  # ignored files excluded, built through a temporary index so neither the real
  # index nor the working tree is touched. Stored under refs/operator-snapshots/
  # so git never garbage-collects it; the oldest are pruned past SNAPSHOT_KEEP.
  local root=$1 stamp=$2 idx tree commit ref
  idx=$(mktemp -u)
  ref="refs/operator-snapshots/$stamp"
  (
    cd "$root" || exit 1
    GIT_INDEX_FILE="$idx" git add -A . >/dev/null 2>&1 || exit 1
    tree=$(GIT_INDEX_FILE="$idx" git write-tree) || exit 1
    commit=$(git commit-tree "$tree" -p HEAD -m "operator pre-run snapshot $stamp") || exit 1
    git update-ref "$ref" "$commit" || exit 1
    # prune: keep the newest SNAPSHOT_KEEP
    git for-each-ref --sort=creatordate --format='%(refname)' refs/operator-snapshots \
      | awk -v keep="$SNAPSHOT_KEEP" '{ a[NR]=$0 } END { for (i = 1; i <= NR - keep; i++) print a[i] }' \
      | while IFS= read -r old; do [ -n "$old" ] && git update-ref -d "$old"; done
    echo "$ref"
  )
  local rc=$?
  rm -f "$idx"
  return $rc
}

backup_commit() {  # root before_status_file remote branch stamp
  # Commits exactly the files whose git status changed during the run (new, or
  # newly modified) and pushes them to an explicit branch. A file that was
  # already dirty before the run is the owner's in-progress work and is left
  # alone. Never `git add -A`, never a refspec that could delete anything.
  local root=$1 before=$2 remote=$3 branch=$4 stamp=$5 after
  [[ "$remote" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "backup: invalid remote name: $remote" >&2; return 1; }
  [[ "$branch" =~ ^[A-Za-z0-9._][A-Za-z0-9._/-]*$ ]] || { echo "backup: invalid branch name: $branch" >&2; return 1; }
  (
    cd "$root" || exit 1
    after=$(mktemp)
    git status --porcelain --untracked-files=all > "$after"
    files=()
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      p=${line:3}
      case "$p" in *" -> "*) p=${p##* -> } ;; esac
      p=${p%\"}; p=${p#\"}
      files+=("$p")
    done < <(comm -13 <(sort "$before") <(sort "$after"))
    rm -f "$after"
    if [ ${#files[@]} -eq 0 ]; then
      echo "backup: no files changed during the run, nothing to commit"
      exit 0
    fi
    git add -- "${files[@]}" || exit 1
    git commit -q -m "Operator run $stamp" -- "${files[@]}" || exit 1
    echo "backup: committed $(git rev-parse --short HEAD) (${#files[@]} file(s))"
    git push -q "$remote" "HEAD:refs/heads/$branch" || { echo "backup: push to $remote $branch failed; the commit is local" >&2; exit 1; }
    echo "backup: pushed to $remote $branch"
  )
}

run_with_timeout() {  # seconds command... -> the command's exit code, or 124 on timeout
  local secs=$1; shift
  local flag; flag=$(mktemp -u)
  "$@" &
  local pid=$!
  ( sleep "$secs"; touch "$flag"; kill -TERM "$pid" 2>/dev/null; sleep 5; kill -KILL "$pid" 2>/dev/null ) &
  local watchdog=$!
  wait "$pid" 2>/dev/null
  local rc=$?
  kill "$watchdog" 2>/dev/null
  wait "$watchdog" 2>/dev/null
  if [ -e "$flag" ]; then
    rm -f "$flag"
    return 124
  fi
  return $rc
}
