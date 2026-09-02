#!/bin/bash
# Runs one unattended operator pass. The command a scheduler (cron, launchd, a
# Claude Code scheduled task) should call.
#
#   bash .claude/operator/run-operator.sh            # one real run
#   bash .claude/operator/run-operator.sh --dry-run  # print the agent command, run nothing
#
# What the wrapper does around the agent, deterministically and without the
# model's involvement:
#   1. refuses to run on a repository with no commits, or while another run holds the lock
#   2. records a durable pre-run snapshot (untracked files included) under refs/operator-snapshots/
#   3. runs the agent with a deny-by-default permission mode, an exact tool allowlist
#      (no git write commands, no git wildcards), a spend cap, and a wall-clock timeout
#   4. if backup.enabled in the config: commits exactly the files the run changed and
#      pushes them to the configured remote and branch, after every agent write is done
#
# Verify one run by hand (read the log, read the git diff) before scheduling it,
# and again after any change to the prompt or the allowlist.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
. "$HERE/operator-lib.sh"

CONFIG=$(config_path "$ROOT")
TIMEOUT_MIN=$(config_get "$CONFIG" caps.run_minutes 20)
BACKUP_ENABLED=$(config_get "$CONFIG" backup.enabled false)
REMOTE=$(config_get "$CONFIG" backup.remote origin)
BRANCH=$(config_get "$CONFIG" backup.branch main)
BUDGET_USD="${OPERATOR_BUDGET_USD:-2}"

PROMPT="Read and execute .claude/operator/operator-prompt.md exactly as written. One run, one report. Stop when done."

# The exact tool surface the prompt needs. Write is allowed only because creating
# today's daily requires it; the daily guard blocks a Write over an existing daily.
# Git is reachable only through the validated helper (no --output, no writes).
ALLOWED=(
  "Read" "Glob" "Grep" "Edit" "Write"
  "Bash(python3 .claude/scripts/vault-health.py --json)"
  "Bash(bash .claude/scripts/operator-git.sh *)"
  "Bash(ls *)"
)

CMD=(claude -p "$PROMPT" --permission-mode dontAsk --max-budget-usd "$BUDGET_USD"
     --allowedTools "${ALLOWED[@]}")

if [ "${1:-}" = "--dry-run" ]; then
  printf 'cd %q && ' "$ROOT"; printf '%q ' "${CMD[@]}"; echo
  echo "config=$CONFIG timeout=${TIMEOUT_MIN}m backup=$BACKUP_ENABLED remote=$REMOTE branch=$BRANCH"
  exit 0
fi

command -v claude >/dev/null 2>&1 || { echo "run-operator: claude CLI not found on PATH" >&2; exit 127; }
command -v python3 >/dev/null 2>&1 || { echo "run-operator: python3 not found on PATH" >&2; exit 127; }

cd "$ROOT" || exit 1
require_head || exit 1
acquire_lock "$ROOT" || exit 1
trap 'release_lock "$ROOT"' EXIT

STAMP=$(date +%Y-%m-%dT%H-%M-%S)-$$
LOG="$ROOT/.claude/.operator-runs/$STAMP.log"
BEFORE=$(mktemp)
git status --porcelain --untracked-files=all > "$BEFORE"

SNAP=$(snapshot_create "$ROOT" "$STAMP") || { echo "run-operator: snapshot failed, refusing to run" >&2; exit 1; }
echo "pre-run snapshot: $SNAP (restore one file: git checkout $SNAP -- <path>; list: git ls-tree -r --name-only $SNAP)" | tee "$LOG"

run_with_timeout $((TIMEOUT_MIN * 60)) "${CMD[@]}" >>"$LOG" 2>&1
rc=$?
[ "$rc" -eq 124 ] && echo "run-operator: agent run hit the ${TIMEOUT_MIN}-minute timeout and was stopped" | tee -a "$LOG"

if [ "$BACKUP_ENABLED" = "true" ]; then
  backup_commit "$ROOT" "$BEFORE" "$REMOTE" "$BRANCH" "$STAMP" 2>&1 | tee -a "$LOG"
else
  echo "backup: disabled in config; the run's changes are uncommitted in the working tree" | tee -a "$LOG"
fi
rm -f "$BEFORE"

echo "exit=$rc log=$LOG"
exit $rc
