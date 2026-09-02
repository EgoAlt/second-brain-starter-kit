#!/usr/bin/env python3
"""PreToolUse hook (Write + Edit + Bash): BLOCKING guard for rule 8 of the root CLAUDE.md.

A daily note is uncommitted for the length of a session (edits sit in the working
tree until the next backup commit), so anything that clobbers or discards it loses
the content with no git copy to recover from. Three routes are closed here:

Write gate: a Write whose target is an existing, non-empty daily-family file is
blocked; use Edit. Creating the file (it does not exist yet, or is an empty stub)
passes. An identical-content Write is a provable no-op and passes.

Edit gate: an Edit whose `old_string` is the whole current file is a wholesale
replacement wearing Edit's clothes, and is blocked. Any smaller Edit passes: an
in-place edit to one section is exactly what a daily wants.

Bash gate: a command is blocked when it would discard, remove, or clobber a daily:
  (A) it names a daily path (or a bare daily-shaped basename, for the `cd Daily`
      case) together with a destructive verb: a git restore/checkout/reset/clean/rm,
      any git command carrying `--output` (log/diff/show write the file named),
      rm, mv, cp, tee, truncate, an in-place sed or perl, a find -delete, or a
      truncating `>` redirect into that path or bare basename; or
  (B) it is a whole-working-tree discard (hard reset, restore or checkout of `.`,
      a forced checkout, clean with -f or --force) AND the tool cwd is inside the
      vault. Scoped to the vault cwd so the same command in a sibling code repo is
      not caught.
Reads, appends, `git add`, `git commit`, `git diff`, `git log`, and `git stash`
(recoverable) always pass. Commands are judged one statement-segment at a time
(split on `&&`, `||`, `;`, newline) so an unrelated discard chained before a daily
read is not caught.

Scope: `<DAILY_DIR>/YYYY-MM-DD.md` and `<DAILY_DIR>/log/YYYY-MM-DD-log.md` only,
never the folder's CLAUDE.md or README.md.

Known limits, stated so nobody trusts the guard for more than it does:
  - It is a pattern match on the command text. A command that reaches a daily
    through a variable, a script file, or an interpreter one-liner is not seen.
    The permission allowlist in `.claude/settings.json` is the layer that keeps
    such commands from being pre-approved.
  - Two sessions that both see "today's daily does not exist" are both allowed
    to create it, and the second Write wins. There is no lock. Commit early and
    keep sessions that write the same daily sequential.

Override: create `.claude/daily-overwrite-approved` (any content). Honored only on
the day it was last touched, so a forgotten marker cannot disable the gate forever.
The real use is recovering a corrupted daily that needs a wholesale rewrite.

Blocking convention: exit 2 with the reason on stderr. Fails open on any error.
"""
import json
import os
import re
import sys
import time

DAILY_DIR = "Daily"  # the daily-journal folder name, relative to the vault root

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APPROVAL_MARKER = os.path.join(VAULT_ROOT, ".claude", "daily-overwrite-approved")

_D = re.escape(DAILY_DIR)
DAILY_RE = re.compile(rf"^{_D}/(?:log/\d{{4}}-\d{{2}}-\d{{2}}-log|\d{{4}}-\d{{2}}-\d{{2}})\.md$")
DAILY_PATH_RE = re.compile(rf"\b{_D}(?:/|(?=\s|$))")
DAILY_BASENAME = r"(?<![\w-])\d{4}-\d{2}-\d{2}(?:-log)?\.md\b"
DAILY_BASENAME_RE = re.compile(DAILY_BASENAME)
GIT_FLAGS = r"(?:\s+(?:-[cC]\s+\S+|--[\w-]+(?:=\S+)?|-[A-Za-z]\S*))*"
GIT_DISCARD_RE = re.compile(r"\bgit\b" + GIT_FLAGS + r"\s+(?:restore|checkout|reset|clean|rm)\b")
# A truncating redirect (`>` or `>|`, never `>>`) into a daily path or a bare daily basename.
REDIRECT_TO_DAILY_RE = re.compile(
    rf"(?<!>)>\|?\s*[^\s|;&>]*(?:{_D}/(?:log/\d{{4}}-\d{{2}}-\d{{2}}-log|\d{{4}}-\d{{2}}-\d{{2}})\.md|{DAILY_BASENAME})"
)
SEGMENT_RE = re.compile(r"&&|\|\||;|\n")


def approval_active():
    try:
        mtime = os.path.getmtime(APPROVAL_MARKER)
    except OSError:
        return False
    return time.strftime("%Y-%m-%d", time.localtime(mtime)) == time.strftime("%Y-%m-%d")


def deny(reason):
    print(f"guard-daily-overwrite: BLOCKED. {reason}", file=sys.stderr)
    sys.exit(2)


def _in_vault(path):
    if not path:
        return False
    try:
        return os.path.commonpath([os.path.abspath(path), VAULT_ROOT]) == VAULT_ROOT
    except ValueError:
        return False


def _marker_hint():
    return os.path.relpath(APPROVAL_MARKER, VAULT_ROOT)


def _daily_relpath(file_path):
    """Vault-relative path if `file_path` is a daily-family file, else None."""
    if not file_path:
        return None
    abs_path = os.path.abspath(file_path)
    if not _in_vault(abs_path):
        return None
    rel = os.path.relpath(abs_path, VAULT_ROOT).replace(os.sep, "/")
    return rel if DAILY_RE.match(rel) else None


def _read(file_path):
    try:
        return open(os.path.abspath(file_path), encoding="utf-8", errors="ignore").read()
    except OSError:
        return None


def analyze_write(tool_input):
    relpath = _daily_relpath(tool_input.get("file_path", ""))
    if not relpath:
        return None
    existing = _read(tool_input["file_path"])
    if existing is None or existing.strip() == "" or tool_input.get("content", "") == existing:
        return None
    return (
        f'this Write would replace the ENTIRE content of {relpath}, which already exists with '
        f'content. A wholesale overwrite of a live daily clobbers whatever a concurrent session '
        f'wrote into it, and the daily is uncommitted, so git has no copy. Update it in place '
        f'with Edit on the section you mean (rule 8). If the daily is genuinely corrupted and '
        f'must be rewritten, that is the owner\'s call: the override is `touch {_marker_hint()}`.'
    )


def analyze_edit(tool_input):
    relpath = _daily_relpath(tool_input.get("file_path", ""))
    if not relpath:
        return None
    existing = _read(tool_input["file_path"])
    old = tool_input.get("old_string", "")
    if existing is None or not old.strip() or old.strip() != existing.strip():
        return None
    if tool_input.get("new_string", "") == old:
        return None
    return (
        f'this Edit replaces the ENTIRE content of {relpath} (old_string is the whole file), '
        f'which is a wholesale overwrite by another name. Edit one section at a time and leave '
        f'the rest intact (rule 8). A corrupted daily that must be rewritten is the owner\'s call: '
        f'`touch {_marker_hint()}`.'
    )


def _segment_discards_path(seg):
    if GIT_DISCARD_RE.search(seg):
        return True
    if re.search(r"\bgit\b[^;|&]*\s--output(?:=|\s)", seg):
        return True  # git log/diff/show --output=<file> writes that file
    if re.search(r"(?<![\w./-])(?:rm|mv|cp|dd|install|shred|truncate)\b", seg):
        return True
    if re.search(r"(?<![\w./-])tee\b", seg) and not re.search(r"(?<![\w./-])tee\b[^|;&]*\s-a\b", seg):
        return True
    if re.search(r"(?<![\w./-])sed\s+(?:-i\b|--in-place)", seg):
        return True
    if re.search(r"(?<![\w./-])perl\b[^|;&]*\s-\w*i", seg):
        return True
    if re.search(r"(?<![\w./-])find\b[^|;&]*(?:-delete\b|-exec\s+rm\b)", seg):
        return True
    return False


def _segment_whole_tree_discard(seg):
    if re.search(r"\bgit\b" + GIT_FLAGS + r"\s+reset\s+--hard", seg):
        return True
    if re.search(r"\bgit\b" + GIT_FLAGS + r"\s+clean\b[^;|&]*\s(?:-\w*f\w*|--force)\b", seg):
        return True
    if re.search(r"\bgit\b" + GIT_FLAGS + r"\s+(?:restore|checkout)\b", seg):
        if re.search(r"(?:^|\s)(?:--\s+)?(?:\.|:/)(?:\s|$)", seg):
            return True  # restore/checkout of the whole tree
        if re.search(r"\bcheckout\b[^;|&]*\s(?:-\w*f\w*|--force)\b", seg):
            return True  # forced checkout throws away local changes
    return False


def analyze_bash(command, cwd):
    if not command:
        return None
    in_vault = _in_vault(cwd)
    for seg in SEGMENT_RE.split(command):
        if ((DAILY_PATH_RE.search(seg) or DAILY_BASENAME_RE.search(seg)) and _segment_discards_path(seg)) \
                or REDIRECT_TO_DAILY_RE.search(seg):
            return (
                f'this Bash command would discard, remove, or clobber a {DAILY_DIR}/ file, and the '
                f'daily is uncommitted during a session, so git has no copy to recover from. Never '
                f'mutate a daily from Bash: undo your own edits with Edit and read it with Read '
                f'(rule 8). If a daily is genuinely corrupted and must be reset, that is the owner\'s '
                f'call: `touch {_marker_hint()}`.'
            )
        if in_vault and _segment_whole_tree_discard(seg):
            return (
                f'this is a whole-working-tree discard run inside the vault; it would wipe the '
                f'current daily\'s uncommitted state and any other unsaved session work, with no '
                f'git copy to recover from. Undo specific edits with Edit instead (rule 8). If you '
                f'truly mean to discard everything, that is the owner\'s call: `touch {_marker_hint()}`.'
            )
    return None


def analyze(tool_name, tool_input):
    if tool_name == "Write":
        return analyze_write(tool_input)
    if tool_name == "Edit":
        return analyze_edit(tool_input)
    if tool_name == "Bash":
        return analyze_bash(tool_input.get("command", ""), tool_input.get("cwd", ""))
    return None


def selfcheck():
    if not __debug__:
        sys.exit("selfcheck needs assertions enabled; run without -O / PYTHONOPTIMIZE")
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp()
    orig_root, orig_marker = globals()["VAULT_ROOT"], globals()["APPROVAL_MARKER"]
    try:
        globals()["VAULT_ROOT"] = tmp
        globals()["APPROVAL_MARKER"] = os.path.join(tmp, ".claude", "daily-overwrite-approved")
        daily_dir = os.path.join(tmp, DAILY_DIR)
        os.makedirs(os.path.join(daily_dir, "log"))
        existing = os.path.join(daily_dir, "2026-01-15.md")
        body = "---\ntype: daily-note\n---\n\n## Focus\n\nReal work.\n"
        open(existing, "w", encoding="utf-8").write(body)

        # Write gate
        assert analyze("Write", {"file_path": existing, "content": "different\n"}), "overwrite of existing daily must block"
        logf = os.path.join(daily_dir, "log", "2026-01-15-log.md")
        open(logf, "w", encoding="utf-8").write("narrative\n")
        assert analyze("Write", {"file_path": logf, "content": "clobber\n"}), "daily-log overwrite must block"
        assert analyze("Write", {"file_path": os.path.join(daily_dir, "2026-01-16.md"), "content": "new\n"}) is None, "new daily must pass"
        stub = os.path.join(daily_dir, "2026-01-17.md")
        open(stub, "w", encoding="utf-8").write("   \n")
        assert analyze("Write", {"file_path": stub, "content": "first\n"}) is None, "empty stub must pass"
        assert analyze("Write", {"file_path": existing, "content": body}) is None, "no-op must pass"
        conv = os.path.join(daily_dir, "CLAUDE.md")
        open(conv, "w", encoding="utf-8").write("conventions\n")
        assert analyze("Write", {"file_path": conv, "content": "changed\n"}) is None, "folder CLAUDE.md is out of scope"

        # Edit gate
        assert analyze("Edit", {"file_path": existing, "old_string": "Real", "new_string": "New"}) is None, "section Edit must pass"
        assert analyze("Edit", {"file_path": existing, "old_string": body, "new_string": "gone\n"}), "whole-file Edit must block"
        assert analyze("Edit", {"file_path": existing, "old_string": body.strip(), "new_string": "gone"}), "whole-file Edit (stripped) must block"
        assert analyze("Edit", {"file_path": existing, "old_string": body, "new_string": body}) is None, "identical whole-file Edit is a no-op"
        assert analyze("Edit", {"file_path": conv, "old_string": "conventions\n", "new_string": "x"}) is None, "CLAUDE.md out of scope"

        # Bash gate (A)
        blocked = [
            f"git restore {DAILY_DIR}/2026-01-15.md",
            f"git checkout HEAD -- {DAILY_DIR}/2026-01-15.md",
            f"git -C /some/path restore {DAILY_DIR}/2026-01-15.md",
            f"git rm {DAILY_DIR}/2026-01-15.md",
            f"rm {DAILY_DIR}/2026-01-15.md",
            f"rm -f {DAILY_DIR}/log/2026-01-15-log.md",
            f"rm {DAILY_DIR}/*.md",
            f"rm -rf {DAILY_DIR}",
            f"mv {DAILY_DIR}/2026-01-15.md /tmp/x",
            f"echo x > {DAILY_DIR}/2026-01-15.md",
            f"echo x >| {DAILY_DIR}/2026-01-15.md",
            f"sed -i '' 's/a/b/' {DAILY_DIR}/2026-01-15.md",
            f"tee {DAILY_DIR}/2026-01-15.md < foo",
            f"find {DAILY_DIR} -name '*.md' -delete",
            f"cd {DAILY_DIR} && rm 2026-01-15.md",
            f"cd {DAILY_DIR} && printf hacked > 2026-01-15.md",
            f"cd {DAILY_DIR}/log && echo x >| 2026-01-15-log.md",
            "rm 2026-01-15-log.md",
            f"git log --output={DAILY_DIR}/2026-01-15.md -1",
            f"git log -1 --output {DAILY_DIR}/2026-01-15.md",
            f"git diff --output={DAILY_DIR}/2026-01-15.md HEAD",
            f"git show HEAD --output={DAILY_DIR}/log/2026-01-15-log.md",
            f"cd {DAILY_DIR} && git log --output=2026-01-15.md",
        ]
        for cmd in blocked:
            assert analyze("Bash", {"command": cmd}), f"must block: {cmd}"
        passed = [
            f"cat {DAILY_DIR}/2026-01-15.md",
            f"grep Focus {DAILY_DIR}/2026-01-15.md",
            f"git add {DAILY_DIR}/2026-01-15.md",
            f"git diff HEAD -- {DAILY_DIR}/2026-01-15.md",
            f"git log --oneline {DAILY_DIR}/2026-01-15.md",
            f"git log --since=yesterday --name-only -- {DAILY_DIR}",
            f"git commit -m '{DAILY_DIR} backup'",
            f"echo done >> {DAILY_DIR}/2026-01-15.md",
            f"tee -a {DAILY_DIR}/2026-01-15.md < foo",
            f"rm {DAILY_DIR}-standup.md",
            "mv notes/2026-01-14-meeting-notes.md /tmp/x",
            "echo x > notes/2026-01-14-meeting-notes.md",
            f"git checkout main && cat {DAILY_DIR}/2026-01-15.md",
        ]
        for cmd in passed:
            assert analyze("Bash", {"command": cmd}) is None, f"must pass: {cmd}"

        # Bash gate (B)
        for cmd in ["git reset --hard", "git -C . reset --hard HEAD~1", "git restore .",
                    "git checkout -- .", "git checkout HEAD -- .", "git clean -fd", "git clean --force",
                    "git checkout -f other-branch", "git checkout --force main", "git checkout -fq main"]:
            assert analyze("Bash", {"command": cmd, "cwd": tmp}), f"vault whole-tree discard must block: {cmd}"
            assert analyze("Bash", {"command": cmd, "cwd": "/some/other/repo"}) is None, f"sibling repo must pass: {cmd}"
            assert analyze("Bash", {"command": cmd}) is None, f"no cwd must pass: {cmd}"
        for cmd in ["git checkout main", "git checkout -b feature", "git switch main", "git stash",
                    "git clean -n", "ls -la", "git status"]:
            assert analyze("Bash", {"command": cmd, "cwd": tmp}) is None, f"benign command must pass: {cmd}"
        print("selfcheck OK")
    finally:
        globals()["VAULT_ROOT"], globals()["APPROVAL_MARKER"] = orig_root, orig_marker
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return
    try:
        payload = json.load(sys.stdin)
        tool_name = payload.get("tool_name")
        tool_input = payload.get("tool_input") or {}
        if tool_name == "Bash" and "cwd" not in tool_input and payload.get("cwd"):
            tool_input["cwd"] = payload.get("cwd")
        if approval_active():
            print(f"guard-daily-overwrite: override armed for today ({_marker_hint()}), gate not enforced.",
                  file=sys.stderr)
            return
        reason = analyze(tool_name, tool_input)
    except Exception as e:
        print(f"guard-daily-overwrite: skipped (hook error: {e})", file=sys.stderr)
        return
    if reason:
        deny(reason)


if __name__ == "__main__":
    main()
