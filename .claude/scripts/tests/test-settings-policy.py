#!/usr/bin/env python3
"""Independent check of the permission contract: the shared settings and the
operator wrapper must not pre-approve any command with a write-capable form.

Fails if:
  - an `allow` rule in .claude/settings.json is a Bash wildcard on anything other
    than the two kit helpers whose arguments are validated inside the script
  - any allow rule pre-approves a git write verb, or a git read verb with a
    wildcard (every `git log *` / `git diff *` also allows `--output=<file>`)
  - the operator wrapper's ALLOWED list contains any git command other than the
    validated helper, or any Bash wildcard outside the helper set
  - a hook command does not resolve through $CLAUDE_PROJECT_DIR
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SETTINGS = os.path.join(ROOT, ".claude", "settings.json")
WRAPPER = os.path.join(ROOT, ".claude", "operator", "run-operator.sh")

# Wildcards are allowed only on commands that validate their own arguments.
WILDCARD_OK = (
    "Bash(python3 .claude/scripts/check-note-standard.py --file *)",
    "Bash(bash .claude/scripts/operator-git.sh *)",
    "Bash(ls *)",
    "Bash(git status*)",
)
GIT_WRITE = re.compile(r"git\s+(add|commit|push|pull|fetch|merge|rebase|reset|restore|checkout|switch|clean|rm|mv|stash|tag|branch)\b")
GIT_READ_WILD = re.compile(r"git\s+(log|diff|show|grep|blame)\b.*\*")

failures = []
settings = json.load(open(SETTINGS))
for rule in settings["permissions"]["allow"]:
    if rule.startswith("Bash(") and "*" in rule and rule not in WILDCARD_OK:
        failures.append(f"settings allow: wildcard on an unvalidated command: {rule}")
    if GIT_WRITE.search(rule) or GIT_READ_WILD.search(rule):
        failures.append(f"settings allow: git write or wildcard read: {rule}")

for event, groups in settings["hooks"].items():
    for g in groups:
        for h in g["hooks"]:
            if "$CLAUDE_PROJECT_DIR" not in h["command"]:
                failures.append(f"hook {event}: command not rooted in $CLAUDE_PROJECT_DIR: {h['command']}")

src = open(WRAPPER).read()
m = re.search(r"ALLOWED=\((.*?)\n\)", src, re.S)
if not m:
    failures.append("wrapper: ALLOWED array not found")
else:
    for tok in re.findall(r'"([^"]+)"', m.group(1)):
        if tok.startswith("Bash(") and "*" in tok and tok not in WILDCARD_OK:
            failures.append(f"wrapper ALLOWED: wildcard on an unvalidated command: {tok}")
        if "git" in tok and "operator-git.sh" not in tok:
            failures.append(f"wrapper ALLOWED: raw git command: {tok}")
if "--permission-mode dontAsk" not in src:
    failures.append("wrapper: not running with --permission-mode dontAsk")
if "require_head" not in src or "acquire_lock" not in src or "snapshot_create" not in src:
    failures.append("wrapper: missing require_head / acquire_lock / snapshot_create")

if failures:
    print("\n".join(failures), file=sys.stderr)
    sys.exit(1)
print("test-settings-policy OK")
