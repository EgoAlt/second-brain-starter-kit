# The operator

A scheduled, non-interactive run of the agent that maintains the vault without you. One run is one session: it reads its prompt, does the work within its caps, writes a report, and exits. No questions, no confirmations.

## What a run does

1. **Orient.** Reads the root `CLAUDE.md`, `Context/me.md`, the most recent daily, its own backlog at `Resources/operator/health-backlog.md`, and what changed in git since yesterday.
2. **Health check.** Runs `python3 .claude/scripts/vault-health.py --json` and reads the findings.
3. **Fix only what has evidence.** A broken link is repointed only when git history shows exactly one rename of the old file. An orphan is linked only from its folder's existing index. A redundant H1 is removed. Everything that takes judgment (a missing status, a missing summary, an ambiguous link, a tag, a duplicate key) is parked, never guessed.
4. **Park the rest.** Findings that need a decision go to the backlog's Open findings with a `needs-decision` tag.
5. **Stale-state pass.** Compares each project README's `updated:` date with the folder's last git change and flags, never rewrites, any that look stale.
6. **Daily.** If today's daily does not exist, creates it with the full section skeleton and carries forward yesterday's Open Loops. If it exists, edits in place only.
7. **Inbox.** Counts files awaiting ingest and notes the count in the daily. Never reads or ingests them.
8. **Report.** Updates `Last run` in the backlog, stamps its edits, and writes a short run report as its final message.

The agent has no git write access. Its only git surface is `.claude/scripts/operator-git.sh`, three read-only queries with validated arguments. Committing and pushing are the wrapper's job, after the agent exits.

## What a run never does

- Ingests anything from `Inbox/` (that needs the owner in the loop).
- Rewrites a Current Status, a decision record, or any prose it did not create.
- Deletes a page.
- Overwrites a daily note (the guard blocks it anyway).
- Follows instructions found inside vault content. A note that says "do X" is data, and at most a finding to park.
- Runs `git add`, `git commit`, `git push`, or any git command with a write-capable flag. None of these are in its allowlist.
- Passes a human gate: anything public, irreversible, or a matter of judgment is parked for the owner.

## Files

| File | Purpose |
|---|---|
| `operator-prompt.md` | The prompt the scheduled run executes. |
| `operator.config.example.json` | Caps, cadence, backup, signature. Copy to `operator.config.json` (gitignored) and edit. |
| `run-operator.sh` | The scheduler entry point. Lock, pre-run snapshot, deny-by-default agent run with an exact allowlist, wall-clock timeout, optional backup commit and push. Logs to `.claude/.operator-runs/` (gitignored). |
| `operator-lib.sh` | The functions the wrapper uses (snapshot, backup, lock, timeout, config). Tested by `.claude/scripts/tests/test-operator-lib.sh` against a real temporary git repository. |
| `../scripts/operator-git.sh` | The agent's only git surface: `recent`, `renames <basename>`, `folder-date <folder>`. |
| `../scripts/vault-health.py` | The check the operator runs. |
| `../../Resources/operator/health-backlog.md` | The operator's state, in the knowledge layer so it survives a tooling swap. |

The state lives in the knowledge layer on purpose. The prompt and the schedule are tooling and can be rebuilt for another agent; the backlog is a plain markdown file that any agent can pick up.

## What the wrapper guarantees

`run-operator.sh` does these things deterministically, outside the model's control:

- **Refuses to run** on a repository with no commits, or while another run holds the lock (`.claude/.operator-runs/lock`, an atomic `mkdir`, released on exit).
- **Snapshots the whole working tree before the run**, untracked files included and ignored files excluded, as a commit under `refs/operator-snapshots/<stamp>`. It is a real ref, so git never garbage-collects it; the newest ten are kept. Restore one file with `git checkout refs/operator-snapshots/<stamp> -- <path>`; list a snapshot with `git ls-tree -r --name-only <ref>`. The working tree and the real index are not touched.
- **Runs the agent with `--permission-mode dontAsk`** (anything not pre-approved is denied, never prompted), an exact `--allowedTools` list containing no git write commands and no git wildcards, `--max-budget-usd` (default 2, override with `OPERATOR_BUDGET_USD`), and a wall-clock timeout of `caps.run_minutes`.
- **Backs up after the agent exits**, if `backup.enabled` is true: it diffs `git status` before and after the run, stages exactly the files the run created or newly modified, commits them, and pushes `HEAD` to `refs/heads/<branch>` on `<remote>`. A file that was already dirty before the run is the owner's in-progress work and is left uncommitted. Remote and branch names are validated; a deletion refspec cannot be expressed.

Every log line names the snapshot ref, the exit status, and what the backup did. Log filenames carry the timestamp and the PID, so overlapping starts cannot share a file.

## Running it

Run it by hand first and read the result:

```bash
bash .claude/operator/run-operator.sh --dry-run   # shows the exact agent command and the config in effect
bash .claude/operator/run-operator.sh             # one real run, logged
git diff                                          # read every change it made
```

Only after a hand-run reads clean, schedule it. Start with one run a day, in the morning, outside the hours you work:

- **cron:** `0 7 * * * cd /path/to/your/vault && bash .claude/operator/run-operator.sh`
- **Claude Code scheduled tasks or routines**, if your install has them: working directory set to the vault root, command as above.

A run must never stall on a permission prompt. If one does, the fix is the allowlist in `run-operator.sh`, not re-approving by hand.

## Honest limits

- **The threat model is hostile content.** Anything that arrives in `Inbox/` or through a web clipping may contain text aimed at the agent. The operator never reads inbox files, the prompt says content is data, and the allowlist keeps a misled operator from running anything beyond the listed commands. That is three layers, none of them a sandbox. Run it under OS-level sandboxing if your platform offers one.
- **Read caps are instructions.** The wrapper enforces the time limit and the spend cap; the file-count caps are followed by the agent, not imposed on it.
- **The lock covers operator runs, not your interactive sessions.** An interactive session that writes today's daily while the operator runs can race on its creation. Schedule the operator outside your working hours.
- **The health checker validates frontmatter by shape, not with a YAML parser.** It catches missing keys, malformed lines, duplicate keys, and unbalanced brackets. A green result is not proof that every value parses the way Obsidian's YAML parser reads it.

## Growing it

Add a step to the prompt when a maintenance task recurs and has an evidence rule that makes it mechanical. Add a feed (calendar, email, a task tracker) by giving the operator a read-only connector and a step that summarizes into the daily's Priorities. If a new step needs a git query, add a validated subcommand to `operator-git.sh` rather than a git wildcard to the allowlist. `tests/test-settings-policy.py` fails on any wildcard the policy does not recognise.
