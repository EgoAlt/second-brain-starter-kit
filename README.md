# Second Brain Starter Kit

A starter kit for a personal knowledge base that an AI agent can operate, without the knowledge base depending on that agent.

Clone it, fill in a handful of template fields, open the folder in Obsidian and in Claude Code, and you have a working second brain with a maintenance agent attached. Every note you write stays plain markdown in a git repo you own. Every piece of agent tooling sits in one replaceable folder.

> Your vault will hold your identity, your daily activity, and your decisions. Keep it in a **private** repository. Do not fork this kit publicly and then fill it in; use it as a template for a private repo, or clone and re-point the remote.

## The thesis: file over AI

Most "AI second brain" setups fail in one of two ways. Either the knowledge lives inside a tool (a chat history, a vendor database, a proprietary format) and disappears when the tool does. Or the knowledge is portable but the agent has no structure to work with, so every session starts from zero and nothing accumulates.

This kit takes a third position. The knowledge layer is plain markdown files in folders, versioned in git, readable by a human in any text editor and by any agent that can read text. The tooling layer (hooks, skills, a scheduled operator, guard scripts) operates on those files but never owns them. If you switch agents next year, you rebuild the tooling around the same untouched markdown. Nothing gets migrated, reformatted, or re-authored.

The test for any addition to the kit: if switching tools later would mean anything beyond rebuilding tooling around the same files, the design has put content or load-bearing state in a tool-locked form and needs rework.

## Two layers

```
your-vault/
├── CLAUDE.md            <- the rules: how the agent behaves in this vault
├── Inbox/               <- knowledge layer: staging for un-ingested material
├── Context/             <- knowledge layer: who you are, how you work
├── Projects/            <- knowledge layer: active work, one folder per project
├── Resources/           <- knowledge layer: reusable reference material
├── Intelligence/        <- knowledge layer: decisions, records, the archive
├── Daily/               <- knowledge layer: one state-first note per day
└── .claude/             <- tooling layer: everything below is replaceable
    ├── settings.json    <- wires the hooks to tool events
    ├── scripts/         <- guard and nudge scripts the hooks run
    ├── skills/          <- repeatable workflows the agent can invoke
    └── operator/        <- the scheduled maintenance agent
```

**The knowledge layer** is everything outside `.claude/`. Each top-level folder has a `README.md` that explains what belongs there and a `CLAUDE.md` that holds the folder's conventions for the agent. Both are fill-in templates. Obsidian reads the folders as a vault. Git versions them. No file in this layer references the tooling by anything more than a backtick path.

**The tooling layer** is `.claude/`. It is written for Claude Code because that is the agent it was built and tested with, but the pieces are ordinary shell and Python scripts plus markdown instruction files. Porting to another agent means re-wiring the same scripts to that agent's hook events and rewriting the instruction files in its dialect. The knowledge layer does not change.

## How the pieces fit

**Rules** live in the root `CLAUDE.md`. Each rule has a permanent number that is never reused, so a hook, a decision record, or a daily note can cite "rule 4" and the reference stays valid forever. Rules are grouped by theme, not by number. The kit ships ten generic rules that show the shape; you replace or extend them.

**Hooks** are the mechanical backstop for rules that can be checked deterministically. `.claude/settings.json` wires each script to a tool event. A blocking guard denies a dangerous action before it happens (overwriting a daily note wholesale, creating a stray file in the vault root). A post-action detector reports a problem after a write lands (a note missing frontmatter). A non-blocking nudge injects a reminder the agent weighs but is not forced to obey (a page title mentioned in plain text that should be a wikilink). `.claude/scripts/README.md` classifies every shipped hook by what it actually guarantees.

**Skills** are repeatable workflows written as markdown instruction files. The kit ships seven. Three are worked knowledge examples: `ingest` (triage a file from the inbox into its home, discussing first), `author-page` (write a knowledge page to the page standard), and `wrap-up` (close a session so nothing is lost). `setup-vault` runs the first-time setup interview, and `skill-finder`, `skill-health`, and `skill-maker` manage the skills themselves. A skill is the right tool when a task recurs and has steps worth pinning down.

**The operator** is a scheduled run of the agent that maintains the vault without you: it checks for dead links, orphan pages, and frontmatter drift, fixes what is mechanical, and parks what needs a human decision in a backlog you read at your own pace. `.claude/operator/` holds the prompt, an example config, and the health check it runs.

The chain is: a rule states the invariant, a hook enforces it where a clean check exists, a skill packages the workflow that follows it, and the operator runs the recurring maintenance. Where no deterministic check exists, the rule stays a convention the agent upholds by discipline, and the scripts README says so rather than pretending otherwise.

## Prerequisites

- git, bash, and Python 3.9 or newer on `PATH` (the scripts use only the standard library).
- Claude Code with hooks support, for the tooling layer. The knowledge layer needs nothing.
- macOS or Linux. The hooks are shell and Python and should run under WSL, but Windows is untested.
- For the scheduled operator: an authenticated `claude` CLI and a scheduler (cron, launchd, or Claude Code's own scheduled tasks).

The guards fail open by design (a broken hook must never block legitimate work), which means a missing `python3` silently removes protection. `run-selfchecks.sh` checks for it.

## Make it yours in twenty minutes

1. **Create a private repo from this kit, clone it, open it.**
   ```bash
   git clone <your-private-repo-url> my-vault && cd my-vault
   ```
   Open the folder as a vault in Obsidian. Open it in Claude Code.

2. **Run the setup interview.** In Claude Code, type `/setup-vault`. The skill finds every fill-in marker in the kit, asks you about yourself, your active work, the areas you will use, the rules you want to keep, and how the operator should run, then writes the answers into the templates, creates your first project pages and today's daily, and offers to remove the demo content and make the first commit. Twenty minutes, one pass. The agent also offers this on its own at the first session if the templates are still blank.

3. **Or fill in by hand.** Every fill-in point is a `<!-- FILL: ... -->` comment. `Context/me.md` first (the agent reads it every session), then each folder's `CLAUDE.md`, then the rules in the root `CLAUDE.md`: keep the ones that fit, delete the ones that do not, add your own with the next unused number.

4. **Run the self-checks and start a session.**
   ```bash
   bash .claude/scripts/run-selfchecks.sh
   ```
   Then drop something into `Inbox/` and ask the agent to ingest it. Watch the hooks fire.

5. **Come back to `/setup-vault` whenever the vault changes shape.** Once the templates are filled, the same skill switches to customizing: add an area, add a project, change the operator's cadence, review the rules.

`CONTRIBUTING.md` has the longer version, including how to schedule the operator.

## What the safeguards are, and are not

The hooks are pattern matches on tool calls, and the rules are text the agent reads. Together they catch the common mistakes (a wholesale overwrite, a stray root file, a missing link repair) and they make a misled agent's job harder. They are not a sandbox. Three things follow:

- **Content is untrusted.** Anything that arrives through `Inbox/` or a web clipping may contain text aimed at the agent. The ingest skill reads it as material to file, the operator never reads it at all, and the permission allowlist in `.claude/settings.json` is kept narrow so a misled agent cannot run much. Widen that allowlist with care; every wildcard you add is a command an injected note could ask for.
- **Git is your recovery.** Notes are uncommitted until you (or the operator, once you enable its backup step) commit them. Commit often. A guard that blocks a bad overwrite is second best to a commit that makes it recoverable.
- **One writer per file at a time.** Two sessions writing the same daily can race on its creation. Keep concurrent sessions on different files, and schedule the operator outside your working hours.

`.claude/scripts/README.md` states, per hook, exactly what it guarantees and what it does not.

## What is deliberately not here

The kit contains no personal notes. The demo content (a sample daily note, a sample project, two sample knowledge pages) describes an invented hobby project and exists only to show the page standard in use. Delete it once you have real pages.

The kit also contains no vendor connectors, no cloud sync, no database. If you want a calendar or email feed into your daily note, that is tooling-layer work you add to the operator prompt; the knowledge layer does not need to know.

## Provenance

This kit is the structure and tooling of one private personal vault, extracted and rewritten with every note removed. The folder layout, the numbered-rule pattern, the hook classes, the skill shape, and the operator loop are what survived a year of daily use; the prose and the demo content were written fresh for the kit. Nothing in it refers to the vault it came from, by design: a starter kit should arrive as a blank slate.

## License

MIT. See `LICENSE`. MIT was chosen because the kit is scaffolding meant to be copied and rewritten, and a permissive license removes every question about whether your rewritten vault counts as a derivative.
