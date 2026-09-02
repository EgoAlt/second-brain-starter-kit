#!/usr/bin/env python3
"""PreToolUse hook (Write|Edit): non-blocking wikilink nudge.

Backstops rule 5 of the root CLAUDE.md (link every entity that has a page).
Scans the content about to be written for an EXISTING page title appearing as
plain prose outside a [[wikilink]], and surfaces it as additionalContext. It
never blocks the write.

Precision over recall by design: only an exact match against a real page title
counts. No fuzzy Title-Case guessing, which is what keeps this from firing on
every proper noun that is not meant to be a page.

A second, independent check flags any [[wikilink]] into a dot-prefixed folder
(`[[.claude/...]]`): Obsidian never indexes dot-folders, so such a link is a
guaranteed broken link. Tooling files are referenced as backtick paths instead.

Payload shape (Claude Code): Write gives tool_input.content, Edit gives
tool_input.new_string.
"""
import json
import os
import re
import subprocess
import sys

MIN_TITLE_LEN = 4
MAX_SUGGESTIONS = 5
SKIP_DIRS = {".git", ".claude", ".obsidian", "node_modules", ".venv", "Inbox"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOTFOLDER_LINK_RE = re.compile(r"\[\[\s*~?/?\.[A-Za-z][\w-]*/[^\]]*\]\]")


def vault_root():
    """The git toplevel of the current working directory, or None."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def title_index(root):
    """Map each multi-word page's kebab-case filename, and a naive Title Case
    rendering of it (hyphens to spaces, each word capitalised), to its path.
    Prose mentions a page as "Bridle Tuning", not "bridle-tuning"; the Title
    Case guess is what catches that. Single-word and pure-date titles are
    excluded: matching a common word against arbitrary prose is pure noise."""
    index = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            raw = name[:-3]
            if "-" not in raw or DATE_RE.match(raw) or len(raw) < MIN_TITLE_LEN:
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            index.setdefault(raw, rel)
            display = " ".join(w.capitalize() for w in raw.split("-"))
            if display != raw:
                index.setdefault(display, rel)
    return index


def strip_noise(text):
    """Remove spans that are never a wikilink candidate: existing [[wikilinks]]
    and backtick code spans (a backticked path is a deliberate non-link)."""
    text = re.sub(r"\[\[[^\]]*\]\]", " ", text)
    text = re.sub(r"`[^`]*`", " ", text)
    return text


def find_hits(text, index, self_title=None):
    stripped = strip_noise(text)
    hits = []
    for title in sorted(index, key=len, reverse=True):
        if title == self_title:
            continue
        if re.search(r"(?<!\w)" + re.escape(title) + r"(?!\w)", stripped):
            hits.append((title, index[title]))
        if len(hits) >= MAX_SUGGESTIONS:
            break
    return hits


def dotfolder_links(text):
    """Dot-folder wikilinks outside backtick spans (a backticked example of the
    pattern, as in this file's own README, is not a live link)."""
    return sorted(set(DOTFOLDER_LINK_RE.findall(re.sub(r"`[^`]*`", " ", text))))


def selfcheck():
    if not __debug__:
        sys.exit("selfcheck needs assertions enabled; run without -O / PYTHONOPTIMIZE")
    index = {"bridle-tuning": "Resources/x/bridle-tuning.md",
             "Bridle Tuning": "Resources/x/bridle-tuning.md"}
    assert find_hits("Read Bridle Tuning first.", index) == [("Bridle Tuning", "Resources/x/bridle-tuning.md")]
    assert find_hits("Read [[bridle-tuning|Bridle Tuning]] first.", index) == [], "linked mention is not a hit"
    assert find_hits("See `bridle-tuning.md`.", index) == [], "backticked path is not a hit"
    assert find_hits("Bridle Tuning", index, self_title="Bridle Tuning") == [], "a page never nudges itself"
    assert dotfolder_links("see [[.claude/scripts/x]]") == ["[[.claude/scripts/x]]"]
    assert dotfolder_links("see `[[.claude/scripts/x]]` as an example") == [], "backticked example ignored"
    assert dotfolder_links("see [[Resources/library/x]]") == []
    print("selfcheck OK")


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print("{}")
        return

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if not file_path.endswith(".md") or any(p in SKIP_DIRS for p in file_path.split(os.sep)):
        print("{}")
        return

    text = tool_input.get("content", "") if tool_name == "Write" else tool_input.get("new_string", "")
    if len(text) < 10:
        print("{}")
        return

    bad_links = dotfolder_links(text)
    root = vault_root()
    hits = []
    if root:
        hits = find_hits(text, title_index(root), self_title=os.path.basename(file_path)[:-3])

    if not hits and not bad_links:
        print("{}")
        return

    parts = []
    if bad_links:
        parts.append(
            "This write contains [[wikilink]]s into a dot-folder: " + ", ".join(bad_links[:5])
            + ". Obsidian never indexes dot-folders, so these are guaranteed broken links. "
            "Reference tooling as a backtick path instead."
        )
    if hits:
        lines = "; ".join(f'"{t}" -> {p}' for t, p in hits)
        parts.append(
            "This write mentions existing page(s) as plain text, not a [[wikilink]] "
            f"(rule 5): {lines}. Consider linking if it is the same entity."
        )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "additionalContext": " ".join(parts)}}))


if __name__ == "__main__":
    main()
