#!/usr/bin/env python3
"""Vault health check: the audit the scheduled operator runs, also usable by hand.

    python3 .claude/scripts/vault-health.py [VAULT_ROOT] [--json] [--selfcheck]

Reports, for every markdown page outside the excluded folders:
  broken links      a [[wikilink]] or ![[embed]] whose target does not resolve
  ambiguous links   a bare [[basename]] link that matches more than one page
  orphans           a page with no inbound [[wikilink]] from any other page
  frontmatter       missing block, malformed line, missing `type:`/`status:`, fewer than two `tags:`
  summary           a page whose first body line is not a `**Summary**:` line
  redundant H1      a `# Title` heading that duplicates the filename

Resolution follows Obsidian's rules: a link with a `/` resolves as a vault-relative
path (with or without `.md`); a bare name resolves by basename, and is ambiguous
when more than one page shares it and none is a same-folder sibling. A `#heading`
suffix and a `|display` suffix are ignored for resolution. Code fences, inline code,
and HTML comments are stripped first, so a documented example link is never counted.

Convention files are exempt from the page checks: any `CLAUDE.md`, and a `README.md`
or `CONTRIBUTING.md` at the vault root or directly inside a top-level folder. A
README deeper than that (a project's README) is a page and is checked in full.

Frontmatter is validated by shape without a YAML library (standard library only):
every line must be `key: value`, a `- item` list entry, or blank, and `status:`
must be a single token. Deeper YAML validation needs a real parser; add one if you
adopt richer frontmatter.

Exit status: 0 when clean, 1 when any finding exists (so a scheduler can alert).
Read-only: this script never edits a page. Fixing is the agent's job, with the
report as its worklist. It reads every page once; on a very large vault expect a
few seconds, and nothing here is cached between runs.
"""
import json
import os
import re
import sys

SKIP_DIRS = {".git", ".claude", ".obsidian", "node_modules", ".venv", "Inbox", "raw"}
# Folders whose pages are exempt from the orphan check (dailies link outward, rarely inward).
ORPHAN_EXEMPT_DIRS = {"Daily"}
SUMMARY_EXEMPT_TYPES = {"daily-note", "daily-log"}

LINK_RE = re.compile(r"(!?)\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
FM_LINE_RE = re.compile(r"^(?:[A-Za-z_][\w-]*:(?:\s.*)?|\s+-\s+.*|\s*)$")


def is_meta(rel):
    """True for a convention file that is not a page. `rel` is vault-relative with '/'."""
    base = os.path.basename(rel)[:-3]
    if base == "CLAUDE":
        return True
    return base in {"README", "CONTRIBUTING"} and rel.count("/") <= 1


def md_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(".md"):
                out.append(os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/"))
    return out


def strip_code(text):
    """Blank fenced code, inline code, and HTML comments (a fill-in template's
    `<!-- FILL: ... -->` notes often quote an example link), preserving length."""
    text = re.sub(r"```.*?```", lambda m: " " * len(m.group(0)), text, flags=re.S)
    text = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), text, flags=re.S)
    return re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)


def parse_frontmatter(text):
    m = FM_RE.match(text)
    return (m.group(1), text[m.end():]) if m else (None, text)


def frontmatter_tags(fm):
    m = re.search(r"^tags:\s*\[(.*?)\]\s*$", fm, re.M)
    if m:
        return [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]
    m = re.search(r"^tags:\s*\n((?:\s+-\s+.*\n?)+)", fm, re.M)
    if m:
        return [ln.strip()[1:].strip() for ln in m.group(1).splitlines() if ln.strip().startswith("-")]
    return []


def frontmatter_issues(fm):
    """Shape and required-field problems in one frontmatter block (no YAML library)."""
    issues = []
    seen = set()
    for n, ln in enumerate(fm.splitlines(), 1):
        if not FM_LINE_RE.match(ln):
            issues.append(f"malformed frontmatter line {n}: {ln.strip()[:40]}")
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):(.*)$", ln)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key in seen:
                issues.append(f"duplicate frontmatter key: {key}")
            seen.add(key)
            if val.count("[") != val.count("]") or val.count("{") != val.count("}"):
                issues.append(f"unbalanced brackets in frontmatter value of {key}")
    for key in ("type", "status"):
        m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
        if not m or not m.group(1).strip():
            issues.append(f"missing {key}")
        elif key == "status" and (" " in m.group(1).strip() or ":" in m.group(1)):
            issues.append(f"status is not a single token: {m.group(1).strip()[:40]}")
    if len(frontmatter_tags(fm)) < 2:
        issues.append("fewer than two tags")
    return issues


def slug(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


class Vault:
    def __init__(self, root):
        self.root = root
        self.files = md_files(root)
        self.paths = set(self.files)
        self.by_basename = {}
        for f in self.files:
            self.by_basename.setdefault(os.path.basename(f)[:-3], []).append(f)
        self.texts = {f: open(os.path.join(root, f), encoding="utf-8", errors="ignore").read() for f in self.files}
        # Non-markdown attachments, indexed once so embed resolution is O(1) per embed.
        # raw/ is excluded from the PAGE walk (its markdown is not wiki content) but
        # included here: embedding a source PDF from a project's raw/ is supported.
        self.attachment_paths = set()
        self.attachment_names = {}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in (SKIP_DIRS - {"raw"})]
            for n in filenames:
                if not n.endswith(".md"):
                    rel = os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, "/")
                    self.attachment_paths.add(rel)
                    self.attachment_names.setdefault(n, []).append(rel)

    def resolve_attachment(self, target, source):
        """A path-qualified embed must resolve exactly (vault-relative or relative to the
        source's folder); only a bare filename falls back to a basename lookup."""
        if "/" in target:
            if target in self.attachment_paths:
                return True
            rel = os.path.normpath(os.path.join(os.path.dirname(source), target)).replace(os.sep, "/")
            return rel in self.attachment_paths
        return target in self.attachment_names

    def resolve(self, target, source):
        """Return (resolved_path_or_None, ambiguous: bool)."""
        target = target.strip()
        if not target:
            return None, False
        cand = target[:-3] if target.endswith(".md") else target
        if "/" in cand:
            for c in (cand + ".md", cand):
                if c in self.paths:
                    return c, False
            rel = os.path.normpath(os.path.join(os.path.dirname(source), cand)).replace(os.sep, "/") + ".md"
            if rel in self.paths:
                return rel, False
            return None, False
        homes = self.by_basename.get(cand, [])
        if not homes:
            return None, False
        if len(homes) == 1:
            return homes[0], False
        same_dir = [h for h in homes if os.path.dirname(h) == os.path.dirname(source)]
        if len(same_dir) == 1:
            return same_dir[0], False
        return homes[0], True

    def audit(self):
        findings = {"broken_links": [], "ambiguous_links": [], "orphans": [],
                    "frontmatter": [], "summary": [], "redundant_h1": []}
        inbound = {f: 0 for f in self.files}
        for f in self.files:
            text = strip_code(self.texts[f])
            for is_embed, target in LINK_RE.findall(text):
                t = target.strip()
                if is_embed and "." in os.path.basename(t) and not t.endswith(".md"):
                    if not self.resolve_attachment(t, f):
                        findings["broken_links"].append(f"{f}: ![[{t}]]")
                    continue
                resolved, ambiguous = self.resolve(t, f)
                if resolved is None:
                    findings["broken_links"].append(f"{f}: [[{t}]]")
                    continue
                if ambiguous:
                    name = t[:-3] if t.endswith(".md") else t
                    findings["ambiguous_links"].append(f"{f}: [[{t}]] ({len(self.by_basename[name])} homes)")
                if resolved != f:
                    inbound[resolved] += 1

        for f in self.files:
            if is_meta(f):
                continue
            base = os.path.basename(f)[:-3]
            if f.split("/")[0] not in ORPHAN_EXEMPT_DIRS and inbound[f] == 0:
                findings["orphans"].append(f)
            fm, body = parse_frontmatter(self.texts[f])
            note_type = ""
            if fm is None:
                findings["frontmatter"].append(f"{f}: missing frontmatter")
            else:
                findings["frontmatter"].extend(f"{f}: {i}" for i in frontmatter_issues(fm))
                m = re.search(r"^type:\s*(\S+)", fm, re.M)
                note_type = m.group(1) if m else ""
            lines = [ln for ln in body.splitlines() if ln.strip()]
            first = lines[0] if lines else ""
            if first.startswith("# ") and slug(first[2:]) == slug(base):
                findings["redundant_h1"].append(f)
                first = lines[1] if len(lines) > 1 else ""
            if note_type not in SUMMARY_EXEMPT_TYPES and not first.startswith("**Summary**:"):
                findings["summary"].append(f)
        return findings


def report(findings, as_json=False):
    total = sum(len(v) for v in findings.values())
    if as_json:
        print(json.dumps({"total": total, **findings}, indent=2))
        return total
    labels = [("broken_links", "broken links"), ("ambiguous_links", "ambiguous bare links"),
              ("orphans", "orphans"), ("frontmatter", "frontmatter drift"),
              ("summary", "missing Summary line"), ("redundant_h1", "redundant H1")]
    for key, label in labels:
        items = findings[key]
        print(f"{label}: {len(items)}")
        for it in items:
            print(f"  - {it}")
    print("RESULT:", "PASS" if total == 0 else f"FAIL ({total} findings)")
    return total


def selfcheck():
    if not __debug__:
        sys.exit("selfcheck needs assertions enabled; run without -O / PYTHONOPTIMIZE")
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp()
    try:
        def w(rel, text):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(text)

        good_fm = "---\ntype: reference\nstatus: active\ntags: [a, b]\n---\n\n"
        w("Resources/t/index.md", good_fm + "**Summary**: idx.\n\n- [[alpha]]\n- [[Resources/t/beta|Beta]]\n- [[gamma]]\n")
        w("Resources/t/alpha.md", good_fm + "**Summary**: a. See [[beta]] and [[missing-page]] and `[[not-a-link]]`.\n<!-- FILL: add [[an-example]] here -->\n![[diagram.png]] ![[missing.png]] ![[wrong/diagram.png]] ![[Projects/q/raw/source.pdf]] ![[../../Projects/q/raw/source.pdf]]\n")
        w("Resources/t/beta.md", good_fm + "**Summary**: b. Back to [[index]].\n")
        w("Resources/t/diagram.png", "not really an image")
        w("Projects/q/raw/source.pdf", "not really a pdf")
        w("Projects/q/raw/notes.md", "raw markdown is not a page [[zzz]]\n")
        w("Resources/t/gamma.md", "---\ntype: reference\ntags: [only-one]\n---\n\n# Gamma\n\nno summary here\n")
        w("Resources/t/lonely.md", good_fm + "**Summary**: nobody links here.\n")
        w("Resources/README.md", "# Resources\n\nfolder readme, meta\n")
        w("Projects/p/README.md", "# P\n\nlinks [[alpha]]\n")
        w("Projects/q/beta.md", good_fm + "**Summary**: a second beta.\n[[Resources/t/alpha]]\n")
        w("Daily/2026-01-15.md", "---\ntype: daily-note\nstatus: active\ntags: [a, b]\n---\n\n## Focus\n[[alpha]]\n")
        w("Inbox/dropped.md", "not a page [[zzz]]\n")
        w(".claude/skills/x/SKILL.md", "[[ignored-tooling-link]]\n")

        f = Vault(tmp).audit()
        assert f["broken_links"] == ["Resources/t/alpha.md: [[missing-page]]", "Resources/t/alpha.md: ![[missing.png]]",
                                     "Resources/t/alpha.md: ![[wrong/diagram.png]]"], f["broken_links"]
        # ![[wrong/diagram.png]] is broken even though diagram.png exists elsewhere (path-qualified = exact);
        # a raw/ attachment resolves both vault-relative and source-relative.
        assert f["ambiguous_links"] == [], f["ambiguous_links"]
        assert f["orphans"] == ["Projects/p/README.md", "Projects/q/beta.md", "Resources/t/lonely.md"], f["orphans"]
        assert "Resources/t/gamma.md: missing status" in f["frontmatter"]
        assert "Resources/t/gamma.md: fewer than two tags" in f["frontmatter"]
        assert "Projects/p/README.md: missing frontmatter" in f["frontmatter"], "a project README is a page"
        assert "Projects/p/README.md" in f["summary"]
        assert not any("Resources/README.md" in x for v in f.values() for x in v), "a folder README is meta"
        assert f["redundant_h1"] == ["Resources/t/gamma.md"]
        assert f["summary"] == ["Projects/p/README.md", "Resources/t/gamma.md"], f["summary"]
        assert not any("Daily/" in s for s in f["summary"]), "dailies need no Summary"
        assert not any("Inbox" in x or ".claude" in x for v in f.values() for x in v), "excluded dirs never scanned"

        # Bare link to a two-home basename, with and without .md, from a folder with no sibling: ambiguous, no crash.
        w("Resources/u/z.md", good_fm + "**Summary**: z. [[beta]] [[beta.md]] [[index]]\n")
        f2 = Vault(tmp).audit()
        assert "Resources/u/z.md: [[beta]] (2 homes)" in f2["ambiguous_links"], f2["ambiguous_links"]
        assert "Resources/u/z.md: [[beta.md]] (2 homes)" in f2["ambiguous_links"], f2["ambiguous_links"]

        # Frontmatter shape: malformed line, missing type, non-token status, Summary without a colon.
        w("Resources/u/bad.md", "---\nstatus: active: extra\ntags: [a, b]\nnot a yaml line\ntags: [\ntype: [reference\n---\n\n**Summary** no colon. [[index]]\n")
        w("Resources/u/index.md", good_fm + "**Summary**: u. [[bad]] [[z]]\n")
        f3 = Vault(tmp).audit()
        fm_bad = [x for x in f3["frontmatter"] if x.startswith("Resources/u/bad.md")]
        assert any("status is not a single token" in x for x in fm_bad), fm_bad
        assert any("malformed frontmatter line 3" in x for x in fm_bad), fm_bad
        assert any("duplicate frontmatter key: tags" in x for x in fm_bad), fm_bad
        assert any("unbalanced brackets in frontmatter value of tags" in x for x in fm_bad), fm_bad
        assert any("unbalanced brackets in frontmatter value of type" in x for x in fm_bad), fm_bad
        assert "Resources/u/bad.md" in f3["summary"], "Summary without a colon is not a Summary line"
        print("selfcheck OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selfcheck" in sys.argv:
        selfcheck()
        return
    root = os.path.abspath(args[0]) if args else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    total = report(Vault(root).audit(), as_json="--json" in sys.argv)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
