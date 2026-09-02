---
name: setup-vault
description: Turn the blank starter kit into the owner's own vault through a short interview, then keep customizing it as their needs change. First run: find every fill-in marker in the templates, ask about identity, active work, the areas they will use, which example rules to keep, and how the operator should run; write the answers into the templates, create the first project pages and today's daily, offer to remove the demo content and make the first commit. Later runs: add an area or a project, change the operator's cadence or backup, review the rules. Use when the owner types /setup-vault, says "set up my vault", "customize the vault", "add a new area", or when Context/me.md still holds FILL markers at session start and they accept the offer.
disable-model-invocation: true
---

# Set up the vault

Two modes, chosen by a pre-flight check. **Setup** fills a blank kit. **Customize** changes a vault that is already filled. Both follow the same shape: find out what is needed, ask only for that, wait for the answers, then write, then verify.

The templates are the source of truth for what needs filling. Every fill-in point in the kit is a `<!-- FILL: ... -->` comment whose text says what belongs there, so this skill never carries its own list of questions to keep in sync; it reads the markers. `references/interview.md` holds the question script and the order.

## Hard rules

- **No writes before answers.** The interview finishes (or the owner says "skip the rest") before the first file changes.
- **Real answers only.** Write what the owner said, rephrased for the file's voice if needed. Never invent a fact, a preference, a project, or a date. A question they skipped leaves its `FILL:` marker in place, and the report names it.
- **Never leave a marker for an answered question.** After the build, grep for `FILL:` and reconcile every remaining hit against the skipped list.
- **Templates are scaffolds.** A section with no answer and no marker is removed, not left as a placeholder sentence.
- **Never touch `.claude/scripts/` or `.claude/settings.json`.** Those are tooling; changing them is a different job. The only tooling file this skill writes is `.claude/operator/operator.config.json`.
- **Edit, never overwrite.** Every existing file is changed with targeted edits. A new file is a Write; a daily is created only if it does not exist.
- **A new top-level folder is created with `mkdir` first.** The root guard blocks a Write that would create one, and it is right to: creating an area is a structural decision the owner just made in the interview, so make the folder deliberately, then write its `README.md` and `CLAUDE.md`.
- **Commit only with a yes.** Offer the first commit; never push. Adding a remote is the owner's job, and it must be private.

## Pre-flight

1. Confirm the working directory is the vault root: `CLAUDE.md` and `.claude/settings.json` both exist here. If not, say which folder to open and stop.
2. List the markers: `grep -rn 'FILL:' --include='*.md' . | grep -v '^./.git/'`. Group them by file.
3. If `Context/me.md` has markers, run **Setup**. If it has none, run **Customize**. Say which, in one line, and how many markers remain.

## Setup

### Round 1: the interview

Ask in the rounds listed in `references/interview.md`, one round per `AskUserQuestion` call or one short free-text prompt, in this order: who you are, what you are working on, which areas you will use, which rules to keep, how the operator should run, what to do with the demo content. Keep each round to what its target file needs. Accept "skip" for any round and move on; accept "skip the rest" and go to the build with what you have.

Before the first round, send one orienting message: what the interview covers, that nothing is written until it ends, and that every answer can be changed later by hand or by re-running the skill.

Between rounds, if an answer reveals a fact that belongs in a different file than the one being asked about, note it for the build; do not re-ask.

### Round 2: the build

Work file by file, in this order, replacing each `FILL:` marker with the owner's answer for it:

1. `Context/me.md`: identity, current work (as plain text for now; the wikilinks come in step 4), working style, how to work with them, values. `updated:` becomes today.
2. Root `CLAUDE.md`: the opening paragraph, the Orientation section (one sentence per active area, linking each project README created in step 4), the Knowledge Routing rows for the areas they use, and the rules. A rule they dropped becomes a one-line tombstone keeping its number (`N. (Retired at setup; number not reused.)`) so numbering stays permanent; a rule they added takes the next unused number and a matching entry in `Intelligence/decisions/rule-provenance.md`.
3. Each folder `CLAUDE.md` they kept: the folder-specific markers. A folder they said they will not use keeps its files and gets one line at the top of its README saying it is unused for now; nothing is deleted.
4. `Projects/{slug}/README.md` for each active project they named, in the shape of `Projects/example-project/README.md` (frontmatter, Summary, Overview, Current Status, Next Steps) with only what they said. Add each to the Current projects list in `Projects/CLAUDE.md`. Then go back to `Context/me.md` and turn the plain-text project names into wikilinks.
5. A new top-level area, if they asked for one: `mkdir`, then a `README.md` and a `CLAUDE.md` in the shape of the existing pairs, a row in the Knowledge Routing table, and a line in `.claude/scripts/vault-health.py`'s docstring is not needed (the checker discovers folders). Remind them the area's folder name is now load-bearing for the routing table.
6. `.claude/operator/operator.config.json`: cadence and caps from their answers; `backup.enabled` only if they said yes and confirmed the remote is private.
7. Demo content, if they chose to remove it: delete `Daily/2026-01-15.md`, `Projects/example-project/`, `Resources/library/sample-topic/`, and `Intelligence/decisions/2026-01-15-example-decision-record.md` together, then remove the demo bullet from `Projects/CLAUDE.md` and the demo sentences from `Projects/README.md`, `Resources/README.md`, and `Daily/README.md`. Run the health check afterwards; zero broken links is the exit condition.
8. Today's daily: `Daily/<today>.md` with the full section skeleton from `Daily/CLAUDE.md`, Focus reading "Vault set up" plus one line per project created, Open Loops listing any skipped rounds.

### Round 3: verify and hand over

1. `bash .claude/scripts/run-selfchecks.sh` and `python3 .claude/scripts/vault-health.py`. Fix anything the build introduced.
2. `grep -rn 'FILL:'` again. Every remaining marker must correspond to a round the owner skipped; list them.
3. Offer the first commit with `AskUserQuestion`: yes (stage by explicit path, message `Initial vault setup`) or not now. Never push. Say in one line that the remote, when they add one, must be private.
4. Report: files written, projects created, rules kept and retired, operator settings, demo content kept or removed, markers remaining and why, and the one next action (drop something in `Inbox/` and ask to ingest it, or run the operator by hand).

## Customize

For a vault with no markers left in `Context/me.md`. Ask what they want with one `AskUserQuestion`:

- **Add an area**: a new top-level folder. Same as Setup step 5.
- **Add a project**: same as Setup step 4, one project.
- **Change the operator**: cadence, caps, backup. Edit `operator.config.json`; if backup is being turned on, confirm the remote is private first.
- **Review the rules**: read the current rules aloud in one list, ask which to retire or add, apply as in Setup step 2.
- **Fill remaining markers**: list the `FILL:` hits and ask about each.
- **Something else**: free text; if it is an ingest, a page, or a wrap-up, route to that skill instead.

Then verify as in Setup Round 3, without the commit offer unless they ask.

## Self-improvement

When the owner corrects a question's wording or order, fix `references/interview.md`. When they correct how an answer was written into a file, fix the matching build step here. When a setup run was well done, save the final report to `references/examples/` (create the folder on first save) as a model. Keep it small.

## Routing

| Concern | Route to |
|---|---|
| Material already in `Inbox/` | `ingest` skill, after setup |
| Writing a knowledge page | `author-page` skill |
| Closing the session | `wrap-up` skill |
| Any change to hooks, scripts, or `settings.json` | not this skill; edit by hand and run `run-selfchecks.sh` |
