# Hooks and scripts: what each one guarantees

"Enforced" drifts into covering everything from a hard block to a polite reminder. This file is the honest contract: every wired hook, classified by what it guarantees. When writing about a mechanism anywhere in the vault, use its class, not the word "enforced".

## The five enforcement classes

| Class | Guarantee |
|---|---|
| **Blocking guard** | The action is denied before it happens. Strongest mechanical class, still scoped to the tool events it matches. |
| **Post-action detector** | Reports a problem once the write has already landed. It prevents nothing and rolls nothing back. |
| **Non-blocking nudge** | Advisory context injected for the agent to weigh. No guarantee at all. |
| **Model convention** | A rule in `CLAUDE.md` or a skill that only the agent's discipline upholds. No mechanical backstop. |
| **Human gate** | The owner approves (a staged diff, a permission prompt, a go-ahead). Strongest overall, and the only class that covers judgment. |

## Wired hooks

Each row below is wired in `.claude/settings.json`.

| Script | Event | Class | Backs | What it does NOT prove |
|---|---|---|---|---|
| `guard-daily-overwrite.py` | PreToolUse Write + Edit + Bash | Blocking guard | Rule 8 | Blocks a full-file Write over an existing daily, an Edit whose `old_string` is the whole file, and any Bash that discards, removes, or clobbers a daily by path or bare basename, including a git `--output=` into it (or the whole tree, including forced checkout and `clean --force`, when run inside the vault). Pattern match on command text only: a command reaching a daily through a variable or a script file is not seen. No lock: two sessions can both create today's daily and the second wins. Same-day override marker `.claude/daily-overwrite-approved`. Fails open on its own errors. |
| `guard-vault-root.py` | PreToolUse Write | Blocking guard | Rule 9 | Blocks a Write creating a new root file or a new top-level folder. A Bash `mkdir` or redirect creating a root entry is not caught. Fails open. |
| `nudge-wikilinks.py` | PreToolUse Write/Edit | Non-blocking nudge | Rule 5 | Flags an exact existing page title written as plain text, and any `[[wikilink]]` into a dot-folder. Nothing forces the link or removes the bad one. |
| `check-note-standard.py` | PostToolUse Write/Edit | Post-action detector | Rule 4 | Reports missing frontmatter, a malformed frontmatter line, missing `type` or `status`, a multi-token `status`, fewer than two tags, a missing `**Summary**:` line, a redundant H1, and any configured banned substring. Shape validation without a YAML parser; a project README is checked, a folder README is not. The write has already landed. |
| `nudge-move-linkcheck.py` | PostToolUse Bash | Non-blocking nudge | Rule 10 | Fires after a `mv` or `rm` of a page and reminds the agent to sweep and repair inbound links. The repair is judgment; the hook fixes nothing. |
| `check-daily-log.sh` | Stop | Blocking guard (day-level) | Rule 2 | Blocks ending a session that changed content folders with no same-day daily change. Cannot attribute the daily change to *this* session; an earlier same-day commit satisfies it. |

Not a hook, run by hand or by the operator:

| Script | Purpose |
|---|---|
| `vault-health.py` | The audit: broken and ambiguous links, orphans, frontmatter drift (shape, `type`, `status`, tags), missing Summary lines, redundant H1s. Read-only; exit 1 on any finding. `--json` for machine output. Reads every page once per run; no cache. |
| `run-selfchecks.sh` | Runs every script's `--selfcheck`, refuses to run under `PYTHONOPTIMIZE` (assertions would be stripped), checks for `python3`, validates `settings.json`, then runs `vault-health.py` on this vault. |
| `operator-git.sh` | The operator's only git surface: three read-only queries (`recent`, `renames`, `folder-date`) with validated arguments and no flag pass-through. Exists because any `git log *` or `git diff *` wildcard also permits `--output=<file>`, which overwrites that file. |
| `../operator/run-operator.sh` and `operator-lib.sh` | The scheduler entry point for the operator: lock, durable pre-run snapshot (untracked files included), deny-by-default agent run with an exact allowlist, wall-clock timeout, optional post-run backup commit and push done by the wrapper rather than the agent. |
| `tests/test-settings-policy.py` | Independent check of the permission contract: no unvalidated Bash wildcards, no git writes or wildcard git reads in any allow rule, no raw git in the wrapper's allowlist, every hook rooted in `$CLAUDE_PROJECT_DIR`. |
| `tests/test-operator-lib.sh` | Exercises the wrapper's functions against a real temporary git repository: the snapshot captures an untracked daily and skips ignored secrets, the backup commits only what the run changed and pushes to an explicit branch, the lock is exclusive, a repository with no commits is refused, the timeout fires. |

Everything not in the first table (discuss-first ingest, propose-before-write for sensitive content, persisting before the final response) is a **model convention** or a **human gate**. No hook stands behind it, and the rule text says which it is.

## What the permission policy adds

The hooks match tool calls; the allowlist in `settings.json` decides which Bash commands run without asking at all. The two work together: a guard can only block a command it recognises, so the allowlist stays narrow (the kit's own scripts, two exact `git status` forms) and never pre-approves a wildcard whose command has a write-capable form: `find *` (`-delete`, `-exec`), `cat *` (reads anything), `git log *` and `git diff *` (`--output=<file>` overwrites). Git for the operator goes through `operator-git.sh`, which validates its arguments.

The `Read(...)` denies stop the Read tool; they do not stop a Bash command, which is why the same secret patterns are also denied for `cat`, `head`, `tail`, `grep`, `sed`, and `awk`. That list is not exhaustive and cannot be: a pattern deny covers the readers it names. The reliable rule is to keep secrets out of the vault directory entirely. Treat every allowlist entry as a command an injected note could ask the agent to run, and run `tests/test-settings-policy.py` (part of `run-selfchecks.sh`) after any change to the policy.

## Conventions every script follows

- **Vault root from `__file__`.** `.claude/scripts/<script>` is three levels below the root, so no script hardcodes a path. Folder names that a script depends on (`Daily`) are constants at the top of the file.
- **Fail open.** A hook-plumbing bug must never block a legitimate call. Every guard catches its own exceptions, prints a "skipped" line to stderr, and exits 0.
- **Blocking is exit 2 plus stderr.** That is how Claude Code surfaces the reason to the agent. A nudge prints `additionalContext` JSON on stdout (PreToolUse) or plain stderr with exit 0 (PostToolUse).
- **Every script carries `--selfcheck`.** It exercises the script against temporary files and asserts both directions (what must block and what must pass), including the bypasses found in review (a whole-file Edit, a redirect into a bare daily basename, `git clean --force`, a forced checkout, a bare project README, malformed frontmatter). `run-selfchecks.sh` runs them all and refuses optimized Python. A selfcheck proves the cases it lists, nothing more; when you find a new bypass, add it as a case before fixing it.
- **One hook, one file, no shared module.** Slight duplication (two scripts parse frontmatter) is the price of being able to read any hook in isolation.
- **A script that mutates vault content does not exist here.** Every shipped script is read-only or gate-only. If you add one that writes, give it a dry-run default and a backup, and say so in this table.

## Adding a hook

1. Write the rule first, in the root `CLAUDE.md`, with the next unused number.
2. Ask whether a deterministic check exists. If the rule turns on judgment ("is this outbound?"), stop: record it as a model convention here and do not build a hook that gives false confidence.
3. Copy the shape of the closest existing script. Keep the docstring honest about scope and known gaps.
4. Add a `--selfcheck` with both directions.
5. Wire it in `settings.json` with `$CLAUDE_PROJECT_DIR`, add a row to the table above, and run `run-selfchecks.sh`.
