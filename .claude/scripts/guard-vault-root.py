#!/usr/bin/env python3
"""PreToolUse hook (Write): BLOCKING guard for rule 9 of the root CLAUDE.md.

"Never create files or folders in the vault root. Every file lives in an
existing top-level folder." This is the mechanical backstop.

Blocked (a Write whose resolved target is inside the vault):
  (A) a NEW file directly in the vault root. Updating a file that already lives
      there (the root CLAUDE.md, README.md) is an edit, not a creation, and passes.
  (B) a file whose first path component under the root is not an existing
      directory, which would bring a new top-level folder into being. Writing at
      any depth under an existing top-level folder passes.

Only Write is gated: Edit never creates a file, and a Write outside the vault
is not this vault's concern. A Bash `mkdir` or redirect creating a root entry is
a known gap; the Write tool is the real vector for new notes.

Blocking convention: exit 2 with the reason on stderr. Fails open on any error,
because a hook-plumbing bug must never block a legitimate call.
"""
import json
import os
import sys

# .claude/scripts/<this file> -> three levels up is the vault root
VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def deny(reason):
    print(f"guard-vault-root: BLOCKED. {reason}", file=sys.stderr)
    sys.exit(2)


def _in_vault(abs_path):
    try:
        return os.path.commonpath([abs_path, VAULT_ROOT]) == VAULT_ROOT
    except ValueError:
        return False


def analyze_write(file_path):
    """A block reason if this Write would create a new root file or a new
    top-level folder, else None."""
    if not file_path:
        return None
    abs_path = os.path.abspath(file_path)
    if not _in_vault(abs_path) or abs_path == VAULT_ROOT:
        return None
    rel = os.path.relpath(abs_path, VAULT_ROOT).replace(os.sep, "/")
    parts = rel.split("/")

    if len(parts) == 1:
        if os.path.exists(abs_path):
            return None
        return (
            f'this Write would create "{rel}" directly in the vault ROOT. Rule 9: every file '
            f'lives in an existing top-level folder. Route it per the Knowledge Routing table '
            f'in CLAUDE.md (Context/, Projects/{{name}}/, Resources/, Intelligence/, Daily/).'
        )
    top = parts[0]
    if not os.path.isdir(os.path.join(VAULT_ROOT, top)):
        return (
            f'this Write would create a NEW top-level folder "{top}/" (target "{rel}"). Rule 9: '
            f'no new folders in the vault root. Put this under an existing top-level folder, or '
            f'if a new area is warranted, that is the owner\'s structural call: raise it first.'
        )
    return None


def analyze(tool_name, tool_input):
    if tool_name != "Write":
        return None
    return analyze_write(tool_input.get("file_path", ""))


def selfcheck():
    if not __debug__:
        sys.exit("selfcheck needs assertions enabled; run without -O / PYTHONOPTIMIZE")
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp()
    orig = globals()["VAULT_ROOT"]
    try:
        globals()["VAULT_ROOT"] = tmp
        for d in ("Context", "Projects", "Daily", ".claude"):
            os.makedirs(os.path.join(tmp, d), exist_ok=True)
        open(os.path.join(tmp, "CLAUDE.md"), "w").write("root conventions\n")

        assert analyze("Write", {"file_path": os.path.join(tmp, "scratch.md")}), "new root file must block"
        assert analyze("Write", {"file_path": os.path.join(tmp, "NewArea", "note.md")}), "new top-level folder must block"
        assert analyze("Write", {"file_path": os.path.join(tmp, "CLAUDE.md")}) is None, "root CLAUDE.md update must pass"
        assert analyze("Write", {"file_path": os.path.join(tmp, "Context", "me.md")}) is None, "existing top-level dir must pass"
        assert analyze("Write", {"file_path": os.path.join(tmp, "Projects", "x", "deep", "n.md")}) is None, "nesting under existing dir must pass"
        assert analyze("Write", {"file_path": os.path.join(tmp, ".claude", "scripts", "x.py")}) is None, "existing hidden dir must pass"
        assert analyze("Edit", {"file_path": os.path.join(tmp, "whatever.md")}) is None, "Edit must pass"
        assert analyze("Write", {"file_path": "/tmp/some-other-repo/root.md"}) is None, "outside-vault write must pass"
        print("selfcheck OK")
    finally:
        globals()["VAULT_ROOT"] = orig
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return
    try:
        payload = json.load(sys.stdin)
        reason = analyze(payload.get("tool_name"), payload.get("tool_input") or {})
    except Exception as e:
        print(f"guard-vault-root: skipped (hook error: {e})", file=sys.stderr)
        return
    if reason:
        deny(reason)


if __name__ == "__main__":
    main()
