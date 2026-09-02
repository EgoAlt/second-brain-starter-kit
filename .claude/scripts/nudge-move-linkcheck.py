#!/usr/bin/env python3
"""PostToolUse hook (Bash): NON-BLOCKING nudge for rule 10 of the root CLAUDE.md.

When a Bash command moves, renames, or removes a markdown page, inbound
[[wikilinks]] in OTHER files (a historical daily, an archive record, an
unrelated page) silently dangle. Link checks run on the file being edited, not
on the files that link to it, so nothing re-checks the linkers at move time.
This nudge fires right after such a command and reminds the agent to run the
vault-wide link sweep and repair before calling the task done.

Advisory only: prints to stderr, exit 0, never blocks. The detection of a move
is mechanical; the repair (which target each dangling link should repoint to)
is judgment, so this hook does not try to fix anything.

Detection: a move/remove verb (`mv`, `rm`, which also covers `git mv` / `git rm`)
in the same statement segment as a `.md` path outside the excluded folders.
Broad on purpose; a false positive costs one ignorable reminder.
"""
import json
import re
import sys

MOVE_VERB_RE = re.compile(r"(?<![\w./-])(?:mv|rm)\b")
SEGMENT_RE = re.compile(r"&&|\|\||;|\n")
# Folders whose files are not linked-to pages, or are guarded elsewhere.
EXCLUDE_PARTS = ("/Daily/", "/raw/", "/Inbox/", "/node_modules/", "/.git/", "/tmp/")


def _excluded(tok):
    t = tok if tok.startswith("/") else "/" + tok
    return any(part in t for part in EXCLUDE_PARTS)


def moved_md_pages(command):
    hits = []
    for seg in SEGMENT_RE.split(command or ""):
        if not MOVE_VERB_RE.search(seg):
            continue
        for tok in re.split(r"[\s'\"|;&<>()]+", seg):
            tok = tok.strip().strip("'\"")
            if tok.lower().endswith(".md") and not _excluded(tok):
                hits.append(tok)
    return hits


def selfcheck():
    if not __debug__:
        sys.exit("selfcheck needs assertions enabled; run without -O / PYTHONOPTIMIZE")
    assert moved_md_pages("git mv Projects/x/old.md Intelligence/archive/old.md") == \
        ["Projects/x/old.md", "Intelligence/archive/old.md"]
    assert moved_md_pages("mv Projects/a/notes/a.md Projects/a/notes/b.md")
    assert moved_md_pages("rm Resources/library/topic/page.md")
    assert moved_md_pages("git status && rm Resources/x/foo.md") == ["Resources/x/foo.md"]
    assert moved_md_pages("cat Projects/x/old.md") == []
    assert moved_md_pages("rm /tmp/scratch.md") == []
    assert moved_md_pages("mv Daily/2026-01-15.md Daily/x.md") == [], "Daily is the daily guard's job"
    assert moved_md_pages("rm Inbox/dropped.md") == []
    assert moved_md_pages("rm Projects/x/raw/source.md") == []
    assert moved_md_pages("mv old.py new.py") == []
    assert moved_md_pages("git commit -m 'remove old.md page'") == []
    print("selfcheck OK")


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return
        pages = moved_md_pages((payload.get("tool_input") or {}).get("command", ""))
    except Exception as e:
        print(f"nudge-move-linkcheck: skipped (hook error: {e})", file=sys.stderr)
        return
    if pages:
        shown = ", ".join(pages[:4]) + (" ..." if len(pages) > 4 else "")
        print(
            f"nudge-move-linkcheck (rule 10): this command moved, renamed, or removed a page "
            f"({shown}). Inbound [[wikilinks]] in OTHER files may now dangle. Before calling the "
            f"task done, grep the vault for the old slug and repoint every hit, then run "
            f"`python3 .claude/scripts/vault-health.py` to confirm zero broken links.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
