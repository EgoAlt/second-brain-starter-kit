# Make it yours

This file is the longer version of the README's quickstart: how to turn the kit into your vault, how to wire the tooling, and how to contribute back if you improve the generic parts.

## 0. Prerequisites

git, bash, Python 3.9+, and Claude Code with hooks. macOS or Linux (WSL should work; Windows is untested). For the operator, an authenticated `claude` CLI and a scheduler. Run `bash .claude/scripts/run-selfchecks.sh` after cloning; it checks for `python3` and exercises every hook.

## 1. Create a private repo, clone, open

Use the kit as a template for a **private** repository (on GitHub: "Use this template", then choose Private), or clone it and re-point the remote to a private one. Do not fill in a public fork: `Context/me.md`, your dailies, and your decisions are personal by design. Then open the folder twice: once as a vault in Obsidian, once as a project in Claude Code. Both read the same files. Obsidian gives you the graph and the editor; Claude Code gives you the agent.

Two things about secrets. The `.gitignore` excludes `.env`, key files, `credentials/`, `secrets/`, and Obsidian plugin state (`.obsidian/plugins/*/data.json`, where some plugins keep API keys in plaintext). If a secret ever lands in a commit, deleting the file does not remove it from history: rotate the secret, then rewrite history before any push.

If you do not use Obsidian, any markdown editor works. The only Obsidian-specific syntax in the kit is `[[wikilinks]]` and `> [!type]` callouts, and both degrade to readable plain text.

## 2. Fill in the templates

The guided way: open the vault in Claude Code and type `/setup-vault`. It scans for every fill-in marker, interviews you in short rounds (identity, active work, the areas you will use, which rules to keep, how the operator should run), writes your answers into the templates, creates your first project pages and today's daily note, and offers to remove the demo content and make the first commit. It never writes before you have answered, never invents a fact you did not give it, and never leaves a marker behind for a question you answered. Run it again later and it switches to customizing an already-set-up vault.

The manual way: every fill-in field looks like `<!-- FILL: ... -->` or `{{PLACEHOLDER}}`. Find them all:

```bash
grep -rn -e 'FILL:' -e '{{' --include='*.md' --include='*.json' . | grep -v '^./.git/'
```

Work through them in this order:

1. `Context/me.md`: who you are and how you want the agent to work with you. Read at every session start.
2. Root `CLAUDE.md`: the rules. Keep, cut, or add. Any rule you add gets the next unused number and goes in the section it belongs to.
3. Each folder's `CLAUDE.md`: the folder's conventions. Fill in what matters now.
4. `.claude/operator/operator.config.example.json`: copy to `operator.config.json` (gitignored) and set the caps, cadence, and whether the operator may commit. Folder names are not configurable there: they are constants at the top of each script in `.claude/scripts/` and in the operator prompt. Renaming `Daily/` means changing all of them, so the default is to keep the names.

Delete the demo content when you have real pages: `Daily/2026-01-15.md`, `Projects/example-project/`, and `Resources/library/sample-topic/`. The sample daily note links to the sample project and pages, so remove them together or the link check will report broken links.

## 3. Verify the tooling

```bash
bash .claude/scripts/run-selfchecks.sh
```

Every guard and nudge script carries a `--selfcheck` that exercises it against temporary files. The runner also runs two independent tests (`.claude/scripts/tests/`: the permission contract, and the operator wrapper's snapshot, backup, and lock against a real temporary git repository) and the vault health check against the kit itself. All green means the hooks will behave as documented on your machine. The same runner is the CI job in `.github/workflows/selfchecks.yml`, which also verifies a fresh clone contains the kit.

Hooks are wired in `.claude/settings.json` using `$CLAUDE_PROJECT_DIR`, so the paths resolve wherever you clone. If your agent does not set that variable, replace it with the absolute path to your vault.

## 4. Commit, then schedule the operator

Make your first commit as soon as the templates are filled in, and commit often after that. Nothing in the kit commits for you until you enable the operator's backup step, and a note that exists only in the working tree is one disk failure from gone.

The operator is a prompt file (`.claude/operator/operator-prompt.md`) that a non-interactive agent run executes. Run it by hand first, through its wrapper, and read the diff:

```bash
bash .claude/operator/run-operator.sh --dry-run
bash .claude/operator/run-operator.sh
git diff
```

The wrapper pins a deny-by-default permission mode, the exact tools the prompt needs, and a spend cap; a bare `claude -p` would stall on the first permission prompt. Once a hand-run reads clean, schedule the same command (cron, launchd, or Claude Code's scheduled tasks) once a day. `.claude/operator/README.md` explains what a run does, where it writes, and what it cannot guarantee.

## 5. Grow it

- A recurring task with steps worth pinning becomes a skill: copy the shape of `.claude/skills/wrap-up/SKILL.md`.
- A rule that can be checked deterministically gets a hook: copy the shape of `.claude/scripts/guard-vault-root.py`, add a `--selfcheck`, wire it in `settings.json`, and add a row to `.claude/scripts/README.md` stating what class of guarantee it gives.
- A rule that turns on judgment stays a convention. Say so in the scripts README rather than shipping a hook that gives false confidence.

## Contributing back

Improvements to the generic scaffolding, scripts, and documentation are welcome. Keep pull requests to the tooling and template layers: the kit ships no personal content by design, and a PR that adds real notes, real names, or a real project will not be merged. Run `bash .claude/scripts/run-selfchecks.sh` before opening a PR. Commit messages are plain and describe the change.
