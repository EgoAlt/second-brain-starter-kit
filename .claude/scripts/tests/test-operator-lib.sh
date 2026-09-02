#!/bin/bash
# Exercises operator-lib.sh against a real temporary git repository: the
# snapshot must capture untracked files without touching the tree, the backup
# must commit only what the run changed and push to an explicit branch, the lock
# must be exclusive, and a repository with no commits must be refused.

set -u
HERE=$(cd "$(dirname "$0")" && pwd)
. "$HERE/../../operator/operator-lib.sh"

fail() { echo "FAIL: $*" >&2; exit 1; }

T=$(mktemp -d)
BARE=$(mktemp -d)
trap 'rm -rf "$T" "$BARE"' EXIT

cd "$T" || exit 1
git init -q
git config user.email test@example.invalid
git config user.name test
mkdir -p Daily .claude/.operator-runs
echo tracked > tracked.md
echo seed > run-edited.md
echo secret > .env
printf '.env\n.claude/.operator-runs/\n' > .gitignore
git add tracked.md run-edited.md .gitignore
git commit -qm init

# Owner's in-progress work (dirty before the run) and a new untracked daily.
echo "owner edit" >> tracked.md
echo new > Daily/2026-01-15.md

# --- snapshot ---
ref=$(snapshot_create "$T" test-1) || fail "snapshot_create returned non-zero"
[ "$ref" = "refs/operator-snapshots/test-1" ] || fail "unexpected ref: $ref"
git rev-parse --verify "$ref" >/dev/null 2>&1 || fail "snapshot ref is not durable"
git ls-tree -r --name-only "$ref" | grep -qx 'Daily/2026-01-15.md' || fail "snapshot omits the untracked daily"
git ls-tree -r --name-only "$ref" | grep -qx '.env' && fail "snapshot captured an ignored secret"
git show "$ref:tracked.md" | grep -q 'owner edit' || fail "snapshot omits the pre-run modification"
[ "$(cat Daily/2026-01-15.md)" = new ] || fail "working tree changed by snapshot"
git diff --cached --quiet || fail "real index changed by snapshot"
git status --porcelain --untracked-files=all | grep -q '^?? Daily/2026-01-15.md' || fail "daily no longer untracked after snapshot"

# prune keeps the newest SNAPSHOT_KEEP
for i in $(seq 2 $((SNAPSHOT_KEEP + 3))); do snapshot_create "$T" "test-$i" >/dev/null || fail "snapshot $i"; done
n=$(git for-each-ref refs/operator-snapshots | wc -l | tr -d ' ')
[ "$n" -eq "$SNAPSHOT_KEEP" ] || fail "expected $SNAPSHOT_KEEP snapshots kept, found $n"
git rev-parse --verify refs/operator-snapshots/test-1 >/dev/null 2>&1 && fail "oldest snapshot not pruned"

# --- backup: only the run's changes, pushed to an explicit branch ---
BEFORE=$(mktemp)
git status --porcelain --untracked-files=all > "$BEFORE"
echo "run edit" >> run-edited.md          # modified by the run
echo run > Daily/2026-01-16.md            # created by the run
echo "more owner" >> tracked.md            # was already dirty: stays the owner's
git init -q --bare "$BARE"
git remote add origin "$BARE"
out=$(backup_commit "$T" "$BEFORE" origin main test-1) || fail "backup_commit failed: $out"
committed=$(git show --name-only --format= HEAD)
echo "$committed" | grep -qx 'run-edited.md' || fail "run-modified file not committed"
echo "$committed" | grep -qx 'Daily/2026-01-16.md' || fail "run-created daily not committed"
echo "$committed" | grep -qx 'tracked.md' && fail "pre-dirty owner file was committed"
git status --porcelain | grep -q '^ M tracked.md' || fail "owner's dirty file lost"
[ "$(git -C "$BARE" rev-parse refs/heads/main)" = "$(git rev-parse HEAD)" ] || fail "push to main did not land"
backup_commit "$T" "$BEFORE" 'origin;rm' main x >/dev/null 2>&1 && fail "invalid remote accepted"
backup_commit "$T" "$BEFORE" origin ':main' x >/dev/null 2>&1 && fail "deletion refspec accepted as branch"
out=$(git status --porcelain --untracked-files=all > "$BEFORE"; backup_commit "$T" "$BEFORE" origin main y) || fail "no-op backup failed"
echo "$out" | grep -q 'nothing to commit' || fail "no-op backup did not report nothing to commit"
rm -f "$BEFORE"

# --- lock ---
acquire_lock "$T" || fail "first lock not acquired"
acquire_lock "$T" 2>/dev/null && fail "second lock acquired while held"
release_lock "$T"
acquire_lock "$T" || fail "lock not reacquirable after release"
release_lock "$T"

# --- no commits: refused ---
E=$(mktemp -d)
git -C "$E" init -q
( cd "$E" && require_head 2>/dev/null ) && fail "repository with no commits was accepted"
rm -rf "$E"

# --- config ---
printf '{"backup":{"enabled":true,"remote":"origin"},"caps":{"run_minutes":7}}\n' > cfg.json
[ "$(config_get cfg.json backup.enabled false)" = "true" ] || fail "config_get bool"
[ "$(config_get cfg.json caps.run_minutes 20)" = "7" ] || fail "config_get int"
[ "$(config_get cfg.json backup.branch main)" = "main" ] || fail "config_get default"
[ "$(config_get missing.json a.b dflt)" = "dflt" ] || fail "config_get missing file"

# --- timeout ---
run_with_timeout 1 sleep 5; rc=$?
[ "$rc" -eq 124 ] || fail "timeout did not report 124 (got $rc)"
run_with_timeout 5 true || fail "fast command did not pass through"

echo "test-operator-lib OK"
