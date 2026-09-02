#!/usr/bin/env python3
"""PostToolUse hook (Write|Edit): post-action detector for rule 4 of the root
CLAUDE.md (frontmatter and a Summary line on every note).

Reads the file that was just written and reports, on stderr with exit 2 so the
message reaches the agent:
  - missing frontmatter, a malformed frontmatter line, missing `type:` or
    `status:`, a `status:` that is not a single token, or fewer than two `tags:`
  - a missing `**Summary**:` line as the first body line (daily notes exempt)
  - a redundant `# Title` H1 that duplicates the filename
  - any banned substring from BANNED_SUBSTRINGS (empty by default; a common use
    is a house style that bans a particular punctuation mark)

It cannot prevent or roll back the write; it makes the drift visible in the
same turn so the agent fixes it before moving on.

Exempt: any `CLAUDE.md`; a `README.md` or `CONTRIBUTING.md` at the vault root or
directly inside a top-level folder (a deeper README, such as a project's, is a
page and is checked); and files under folders that are not vault pages.

Frontmatter is validated by shape without a YAML library (standard library
only). See `vault-health.py` for the same rules applied vault-wide.

Also usable directly: `python3 check-note-standard.py --file path/to/note.md`.
"""
import json
import os
import re
import sys

VAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXEMPT_DIRS = {".git", ".claude", ".obsidian", "node_modules", ".venv", "raw", "Inbox"}
SUMMARY_EXEMPT_TYPES = {"daily-note", "daily-log"}
# Substrings a note must not contain, checked line by line outside code spans.
# Example for a house style that bans the em dash: BANNED_SUBSTRINGS = {"—": "em dash"}
BANNED_SUBSTRINGS = {}

FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
FM_LINE_RE = re.compile(r"^(?:[A-Za-z_][\w-]*:(?:\s.*)?|\s+-\s+.*|\s*)$")


def parse_frontmatter(text):
    m = FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def frontmatter_tags(fm):
    m = re.search(r"^tags:\s*\[(.*?)\]\s*$", fm, re.M)
    if m:
        return [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]
    m = re.search(r"^tags:\s*\n((?:\s+-\s+.*\n?)+)", fm, re.M)
    if m:
        return [ln.strip()[1:].strip().strip("'\"") for ln in m.group(1).splitlines() if ln.strip().startswith("-")]
    return []


def frontmatter_issues(fm):
    issues = []
    seen = set()
    for n, ln in enumerate(fm.splitlines(), 1):
        if not FM_LINE_RE.match(ln):
            issues.append(f"malformed frontmatter line {n}: `{ln.strip()[:40]}`")
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):(.*)$", ln)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key in seen:
                issues.append(f"duplicate frontmatter key `{key}`")
            seen.add(key)
            if val.count("[") != val.count("]") or val.count("{") != val.count("}"):
                issues.append(f"unbalanced brackets in frontmatter value of `{key}`")
    for key in ("type", "status"):
        m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
        if not m or not m.group(1).strip():
            issues.append(f"frontmatter missing `{key}:`")
        elif key == "status" and (" " in m.group(1).strip() or ":" in m.group(1)):
            issues.append(f"`status:` must be a single token, got `{m.group(1).strip()[:40]}`")
    if len(frontmatter_tags(fm)) < 2:
        issues.append("frontmatter needs two or more `tags:`")
    return issues


def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def check_text(text, basename):
    """Violations for one note's text. `basename` is the filename without .md."""
    issues = []
    fm, body = parse_frontmatter(text)
    if fm is None:
        issues.append("missing frontmatter block")
        note_type = ""
    else:
        issues.extend(frontmatter_issues(fm))
        m = re.search(r"^type:\s*(\S+)", fm, re.M)
        note_type = m.group(1) if m else ""

    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    first = body_lines[0] if body_lines else ""
    if first.startswith("# ") and slug(first[2:]) == slug(basename):
        issues.append("redundant `# Title` H1 duplicating the filename")
        first = body_lines[1] if len(body_lines) > 1 else ""
    if note_type not in SUMMARY_EXEMPT_TYPES and not first.startswith("**Summary**:"):
        issues.append("first body line should be a `**Summary**:` line")

    if BANNED_SUBSTRINGS:
        in_fence = False
        for n, ln in enumerate(text.splitlines(), 1):
            if ln.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            stripped = re.sub(r"`[^`]*`", "", ln)
            for sub, label in BANNED_SUBSTRINGS.items():
                if sub in stripped:
                    issues.append(f"line {n}: banned {label}")
    return issues


def exempt(path):
    abs_path = os.path.abspath(path)
    try:
        rel = os.path.relpath(abs_path, VAULT_ROOT).replace(os.sep, "/")
    except ValueError:
        return True
    if rel.startswith(".."):
        return True
    parts = rel.split("/")
    if any(p in EXEMPT_DIRS for p in parts[:-1]):
        return True
    base = os.path.splitext(parts[-1])[0]
    if base == "CLAUDE":
        return True
    return base in {"README", "CONTRIBUTING"} and len(parts) <= 2


def check_file(path):
    if not path.endswith(".md") or exempt(path) or not os.path.isfile(path):
        return []
    text = open(path, encoding="utf-8", errors="ignore").read()
    return check_text(text, os.path.basename(path)[:-3])


def selfcheck():
    if not __debug__:
        sys.exit("selfcheck needs assertions enabled; run without -O / PYTHONOPTIMIZE")
    good = "---\ntype: reference\nstatus: active\ntags: [a, b]\n---\n\n**Summary**: fine.\n\n## Body\n"
    assert check_text(good, "my-page") == []
    assert "missing frontmatter block" in check_text("just prose\n", "x")
    assert any("status" in i for i in check_text("---\ntype: x\ntags: [a, b]\n---\n**Summary**: s\n", "x"))
    assert any("type" in i for i in check_text("---\nstatus: active\ntags: [a, b]\n---\n**Summary**: s\n", "x"))
    assert any("tags" in i for i in check_text("---\ntype: x\nstatus: active\ntags: [a]\n---\n**Summary**: s\n", "x"))
    assert any("Summary" in i for i in check_text("---\ntype: x\nstatus: active\ntags: [a, b]\n---\n## Heading\n", "x"))
    assert any("Summary" in i for i in check_text("---\ntype: x\nstatus: active\ntags: [a, b]\n---\n**Summary** no colon\n", "x"))
    assert any("single token" in i for i in check_text("---\ntype: x\nstatus: active: extra\ntags: [a, b]\n---\n**Summary**: s\n", "x"))
    assert any("malformed" in i for i in check_text("---\ntype: x\nstatus: active\ntags: [a, b]\nnot yaml\n---\n**Summary**: s\n", "x"))
    assert any("duplicate" in i for i in check_text("---\ntype: x\nstatus: active\ntags: [a, b]\ntags: [c, d]\n---\n**Summary**: s\n", "x"))
    assert any("unbalanced" in i for i in check_text("---\ntype: [reference\nstatus: active\ntags: [a, b]\n---\n**Summary**: s\n", "x"))
    daily = "---\ntype: daily-note\nstatus: active\ntags: [a, b]\n---\n\n## Priorities\n"
    assert check_text(daily, "2026-01-15") == [], "daily notes need no Summary line"
    dup = "---\ntype: x\nstatus: active\ntags: [a, b]\n---\n\n# My Page\n\n**Summary**: s\n"
    assert any("H1" in i for i in check_text(dup, "my-page"))
    block_tags = "---\ntype: x\nstatus: active\ntags:\n  - a\n  - b\n---\n**Summary**: s\n"
    assert check_text(block_tags, "x") == [], "block-style tags parse"
    globals()["BANNED_SUBSTRINGS"] = {"—": "em dash"}
    assert any("em dash" in i for i in check_text(good + "a — b\n", "x"))
    assert check_text(good + "`a — b`\n", "x") == [], "code spans are exempt"
    globals()["BANNED_SUBSTRINGS"] = {}
    # Exemption scoping: folder README is meta, a project README is a page.
    assert exempt(os.path.join(VAULT_ROOT, "Projects", "README.md"))
    assert exempt(os.path.join(VAULT_ROOT, "CONTRIBUTING.md"))
    assert exempt(os.path.join(VAULT_ROOT, "Projects", "x", "CLAUDE.md"))
    assert not exempt(os.path.join(VAULT_ROOT, "Projects", "x", "README.md")), "a project README is checked"
    assert exempt(os.path.join(VAULT_ROOT, "Inbox", "dropped.md"))
    print("selfcheck OK")


def main():
    if "--selfcheck" in sys.argv:
        selfcheck()
        return
    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
    else:
        try:
            payload = json.load(sys.stdin)
            path = (payload.get("tool_input") or {}).get("file_path", "")
        except Exception as e:
            print(f"check-note-standard: skipped (hook error: {e})", file=sys.stderr)
            return
    issues = check_file(path)
    if issues:
        rel = os.path.relpath(path, VAULT_ROOT)
        print(f"check-note-standard ({rel}): " + "; ".join(issues) + ". Rule 4: fix before moving on.",
              file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
