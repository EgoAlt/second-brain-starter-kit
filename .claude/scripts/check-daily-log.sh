#!/bin/bash
# Stop hook: blocks ending the session if vault content changed without a same-day
# daily note change. Backs rule 2 of the root CLAUDE.md (meaningful work gets a
# session log entry).
#
# "Content changed" means an uncommitted change under the content folders listed in
# CONTENT_DIRS, excluding the operator's own state folder (which changes on every
# autonomous run and has its own reporting). Tooling-only changes (.claude/) never
# trigger this.
#
# "Daily changed" means touched today: an uncommitted edit counts, and so does a
# same-day commit that already logged it. Checking only the uncommitted diff would
# re-block every turn after the daily was committed mid-session.
#
# Day-level, not session-level: it cannot attribute the daily change to THIS
# session, so an earlier same-day session's log satisfies it. That is the honest
# limit of a Stop hook, and the scripts README says so.

DAILY_DIR="Daily"
CONTENT_DIRS=(Projects Context Intelligence Resources)
EXCLUDE_PATHSPECS=(':(exclude)Resources/operator/**')

ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$ROOT" ]; then echo '{}'; exit 0; fi
cd "$ROOT" || { echo '{}'; exit 0; }

TODAY=$(date +%Y-%m-%d)
DAILY="$DAILY_DIR/$TODAY.md"

CONTENT_CHANGED=$(git status --porcelain -- "${CONTENT_DIRS[@]}" "${EXCLUDE_PATHSPECS[@]}" 2>/dev/null)

DAILY_CHANGED=$(git status --porcelain -- "$DAILY" 2>/dev/null)
if [ -z "$DAILY_CHANGED" ]; then
  DAILY_COMMITTED_TODAY=$(git log --since="${TODAY} 00:00:00" --format=%H -- "$DAILY" 2>/dev/null)
  [ -n "$DAILY_COMMITTED_TODAY" ] && DAILY_CHANGED="committed-today"
fi

if [ -n "$CONTENT_CHANGED" ] && [ -z "$DAILY_CHANGED" ]; then
  FILES=$(printf '%s\n' "$CONTENT_CHANGED" | head -20)
  python3 - "$DAILY" "$FILES" <<'PY'
import json, sys
daily, files = sys.argv[1], sys.argv[2]
reason = (
    f"Vault content changed but {daily} was not updated. Rule 2 requires a session log "
    f"for meaningful work: add a one-or-two-line Completed entry (what is true now, plus a "
    f"wikilink to the detail) and refresh Focus, then finish.\nChanged files (uncommitted):\n{files}"
)
print(json.dumps({"decision": "block", "reason": reason}))
PY
else
  echo '{}'
fi
