---
name: skill-maker
description: Turn a task the owner just finished into a small, single-job skill, reconstructed from what actually happened in the conversation rather than from a description. Use when the owner says "turn this into a skill", "make a skill out of what we just did", "skill-ify this", or after skill-finder hands over a chosen candidate. Not for a task that has not been done yet: do it once for real first, then come back.
---

# Make a skill from a finished task

Two rules carry this skill. A skill does **one job**. A skill is **never finished**: ship a small working version, then improve it through use.

## Steps

1. **Check it recurs.** A task done once does not need a skill; build only for what will come back.
2. **Name the single job** as one sentence, verb then object ("draft a reply to a complaint"). If the sentence needs an "and", it is two jobs; split them. Take the smallest slice that is useful on its own, not the whole end-to-end process.
3. **Reconstruct from what actually happened.** Walk back through the task as it was done in this conversation and list the real steps. A process described from memory is the tidy version that drops the judgment calls and exceptions, which are the parts worth capturing. If the owner only has an idea, stop: do the task once for real, then return.
4. **Make each step concrete.** For every step, record what information was in front of the owner and how they judged the result good enough to move on. "Research the competitor" is not a step. "Read their pricing page and last ten posts; done when you can state their offer, price, and angle in one sentence" is.
5. **Hunt the exceptions.** Where was a case handled differently? Where would a new colleague get it wrong? What did the owner almost get wrong and catch? Each becomes explicit guidance.
6. **Mark the checkpoints.** Before anything consequential (send, publish, spend, delete, commit), the skill stops and asks.
7. **Write it in the kit's shape**, under `.claude/skills/{name}/SKILL.md`: frontmatter `name` and a `description` that says what it does and when to use it including the trigger phrases; numbered steps; hard rules; a self-improvement section; a routing table for jobs it hands off. Add `disable-model-invocation: true` if it publishes, deletes, or spends. Then play it back: "this is what I saw us do; what is wrong or missing?" Apply the corrections.
8. **Prune.** For every line, ask whether removing it would change what the agent does. Would the agent already do this correctly without the instruction? Then the line teaches nothing; cut it.
9. **Register and verify.** Add a row to `.claude/skills/README.md`. Run the new skill once on the next real occurrence and fix what comes out wrong.

## Hard rules

- No skill from an untested idea.
- One job per skill.
- The play-back in step 7 happens before the file is considered done.
- A structural change to an existing skill is proposed and confirmed before it is applied; a typo fix is applied directly.

## Self-improvement

When the owner corrects a step of this skill, fix it here. When a skill built by it turns out well, note which step made the difference. Keep it small.

## Routing

| Concern | Route to |
|---|---|
| Deciding what to build in the first place | `skill-finder` |
| Overlap with an existing skill | `skill-health` |
