# Setup interview

The rounds, in order, with the file each one feeds. Ask one round at a time. Every round accepts "skip". Keep the wording; change it here when the owner corrects it so the fix sticks.

## Orienting message (before round 1)

"This takes about twenty minutes in six short rounds: who you are, what you are working on, which areas of the vault you will use, which of the ten example rules to keep, how the maintenance agent should run, and what to do with the demo content. Nothing is written until the rounds are done, and everything can be changed later by hand or by running this again. Say skip to pass on any round."

## Round 1: who you are (feeds `Context/me.md`)

Free text, one prompt, five parts:

- Name, and what you do in one line.
- Location and timezone.
- Languages you write in.
- Working style: deep and careful or fast and rough; best hours; the one weakness you want the agent to help you route around.
- How to work with you: terse or thorough, ask first or act first, anything to match or avoid in your writing voice, and the decisions you always want to make yourself.

Then one short follow-up: "Three to five values, one line each. These shape the judgment calls the rules do not cover."

## Round 2: what you are working on (feeds `Projects/`, `Context/me.md`, root `CLAUDE.md` Orientation)

"List your active projects, one line each: a short name and what done looks like. Active means it has a next step. Collections, reading lists, and reference you keep for interest go elsewhere; name those too and say they are passive."

For each active project, one follow-up if not already answered: "Current status in one or two sentences, and the next step."

## Round 3: which areas you will use (feeds each folder's `CLAUDE.md`, Knowledge Routing)

`AskUserQuestion`, multi-select, header `Areas`:

- **Inbox, Context, Projects, Daily**: the core. Always kept; shown for completeness.
- **Resources**: reusable reference, frameworks, prompts, knowledge pages.
- **Intelligence**: decision records, meeting notes, the archive of finished projects.
- **A new area**: name it. Common ones: a hobbies area for passive interests, a people index, a glossary.

Then, for each kept folder with markers, read its `FILL:` markers aloud in one message and ask for the answers together.

## Round 4: which rules to keep (feeds root `CLAUDE.md`, `rule-provenance.md`)

Show the ten example rules as a numbered list, each in one line. Ask: "Which to retire? A retired rule keeps its number as a one-line tombstone. Any to add? A new rule gets the next number and a one-line reason for the provenance file."

If they retire rule 2 (daily log) or rule 8 (daily guard), say in one line that the matching hook stays wired and will keep firing; removing a hook is a `settings.json` edit outside this skill.

## Round 5: how the operator should run (feeds `.claude/operator/operator.config.json`)

`AskUserQuestion`, header `Operator`:

- **Daily, morning (Recommended)**: one run before you start work. Cron `0 7 * * *`.
- **Weekly**: one run a week. Cron `0 7 * * 1`.
- **Not yet**: leave the example config; schedule later.

Then, unless "Not yet": "Should the operator commit and push its own changes after each run? Only say yes if the remote is private. Default is no."

## Round 6: demo content (feeds the build's removal step)

`AskUserQuestion`, header `Demo`:

- **Remove it now (Recommended)**: the sample daily, project, decision record, and two knowledge pages go away together, links repaired.
- **Keep it for now**: leave it as a worked example; remove later by hand or by re-running this skill.

## Closing question (after verification)

`AskUserQuestion`, header `Commit`:

- **Make the first commit**: stage by explicit path, message `Initial vault setup`. No push.
- **Not now**: leave the tree uncommitted.
