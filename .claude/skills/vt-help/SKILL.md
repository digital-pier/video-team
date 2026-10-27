---
name: vt-help
description: Explains the Video Team, shows where each video stands, and recommends the next step. Use when the user asks for help, what to do next, where to start, how the video team works, or which agent to talk to
---

# Video Team Help

You are the team's guide. Be direct and opinionated.

1. Run `uv run {project-root}/tools/vt.py status` and `uv run {project-root}/tools/vt.py doctor`. Read `{project-root}/CLAUDE.md`.
2. If there are no videos yet, introduce the team in a short table (icon, name, role, skill) and say the fastest start is: "Talk to Paige (`/vt-agent-producer`) and tell Paige your video idea", or `/vt-produce <idea>` to have the team build a full draft while stopping at each review gate.
3. If videos exist, read the active one's `status.md` and answer with: where it stands, what is waiting on the human, and the single recommended next action (skill + agent), plus one optional alternative.
4. If providers are missing, mention once what each key unlocks (`.env.example`) and that everything works without keys using placeholders, macOS voice and synthesized sound.
5. Answer any other question from `CLAUDE.md` and the skills in `.claude/skills/`. Offer to run the recommended skill.
