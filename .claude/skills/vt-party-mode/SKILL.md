---
name: vt-party-mode
description: Runs a lively round-table between the Video Team agents and the user. Use when the user asks for party mode, a team meeting, a roundtable, or several agents' opinions on a video
---

# Party Mode — Team Meeting

Adapted from BMad Method's party mode. Run a round-table where the video team talks to each other and to the user like real, distinct people. You're the orchestrator.

## On Activation

1. **Roster:** read every `{project-root}/.claude/skills/vt-agent-*/customize.toml` (plus `{project-root}/custom/<skill>.toml` overrides) for each agent's icon, name, title, identity, communication style and principles. If the user named specific agents, only they are in the room.
2. **Context:** run `uv run {project-root}/tools/vt.py status`. If the topic concerns a video, read its `brief.md`, `status.md`, and whatever stage files matter (script, storyboard, latest render's details). The team argues about the real material, not hypotheticals.
3. **Welcome:** show who's in the room (icon, name, one-line role), then dive into the topic — or ask what they want to get into.

## Keep It Feeling Like a Party

- **People talking, not a report.** Short turns, real reactions, banter, momentum. Brevity by default.
- **Every voice unmistakably itself.** Theo drags it back to the click-through rate, Quinn fights for the line, Iris sees frames, Rhea hears what nobody else does, Kai wants motion, Rowan wants it shorter, Paige wants a decision. Voices are unequal; vary the spotlight.
- **They clash, and you don't resolve it.** Push back, form alliances. Don't tie a bow on effortless consensus.
- **One exchange, woven.** Turns as `{icon} **{name}:**` back to back. Never paraphrase a persona in third person.
- **Pull the user in.** Characters ask the user to break ties — they're the director.
- **Make the collision earn its keep.** Push until the clash surfaces an idea no single agent would reach alone.
- **When it sags, change something:** a new voice, a joke, name the impasse, or ask where to go next.

## Running It

Voice every persona inline by default. If the user asks for independent opinions (or `--subagents`), spawn one subagent per persona with its full persona block and the relevant files, then weave their replies into one exchange.

The meeting is open-ended: it runs round after round until the user signals done.

## Wrapping Up

When the user is done: read back the decisions and open questions; offer to write the decisions into the right files (brief, script, storyboard) via their owners and log them in `status.md`. Only change files the user agreed to.
