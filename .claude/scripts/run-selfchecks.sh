#!/bin/bash
# Runs every script's --selfcheck, then the vault health check against this vault.
# Green means the hooks behave as documented on this machine.
#
#   bash .claude/scripts/run-selfchecks.sh
#
# The selfchecks are assert-based, so they refuse to run under python -O or
# PYTHONOPTIMIZE (which would strip the assertions and print a false PASS).

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
fail=0

if [ -n "$PYTHONOPTIMIZE" ]; then
  echo "FAIL  PYTHONOPTIMIZE is set; assertions would be stripped. Unset it and rerun."
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "FAIL  python3 not found. The hooks fail open without it, so nothing is guarded."
  exit 1
fi

for s in nudge-wikilinks guard-vault-root guard-daily-overwrite nudge-move-linkcheck check-note-standard vault-health; do
  if out=$(python3 "$HERE/$s.py" --selfcheck 2>&1) && [ "$out" = "selfcheck OK" ]; then
    echo "PASS  $s.py"
  else
    echo "FAIL  $s.py"; echo "$out" | sed 's/^/      /'; fail=1
  fi
done

for sh in check-daily-log.sh operator-git.sh "../operator/run-operator.sh" "../operator/operator-lib.sh"; do
  if bash -n "$HERE/$sh"; then
    echo "PASS  $(basename "$sh") (syntax)"
  else
    echo "FAIL  $(basename "$sh") (syntax)"; fail=1
  fi
done

# Independent tests: the permission contract, and the wrapper's snapshot/backup/lock
# against a real temporary git repository.
if out=$(python3 "$HERE/tests/test-settings-policy.py" 2>&1); then
  echo "PASS  tests/test-settings-policy.py"
else
  echo "FAIL  tests/test-settings-policy.py"; echo "$out" | sed 's/^/      /'; fail=1
fi
if out=$(bash "$HERE/tests/test-operator-lib.sh" 2>&1) && [ "${out##*$'\n'}" = "test-operator-lib OK" ]; then
  echo "PASS  tests/test-operator-lib.sh"
else
  echo "FAIL  tests/test-operator-lib.sh"; echo "$out" | sed 's/^/      /'; fail=1
fi

if python3 -c "import json; json.load(open('$ROOT/.claude/settings.json'))" 2>/dev/null; then
  echo "PASS  settings.json (valid JSON)"
else
  echo "FAIL  settings.json (invalid JSON)"; fail=1
fi

echo
echo "vault-health on $ROOT:"
python3 "$HERE/vault-health.py" "$ROOT" | sed 's/^/  /' || fail=1

exit $fail
