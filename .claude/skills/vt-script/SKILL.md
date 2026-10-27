---
name: vt-script
description: Writes or rewrites the narration script for the active video, scene by scene, from the approved brief. Use when the user asks for a script, rewrite, or narration text
---

# Script

Owner: ✍️ Quinn. Input: `brief.md`. Output: `script.md` in the format in `{project-root}/CLAUDE.md`.

1. Read `brief.md`, `status.md`, and `channel/*.md` if present. If the brief gate is not approved, say so and ask whether to proceed anyway.
2. **Plan the beats** in a few lines before writing: hook (0-5 s), setup/promise (to ~30 s), body sections with a re-hook every 30-45 s, payoff, CTA. Budget words at ~150/min of target length.
3. **Write `script.md`.** One scene per visual beat — usually 5-15 s of narration (12-40 words). Each scene has VO, Visual idea, and optional On screen and Sound. Write VO exactly as it should be spoken: numbers and acronyms spelled how they're said, no stage directions inside VO.
4. Report: scene count, word count, estimated runtime, and the hook. Quote the first two scenes.
5. Update `status.md` (Stage: script, log line) and run `uv run {project-root}/tools/vt.py review <slug>`.
6. **Gate:** ask the human to approve or give notes (offer: alternative hooks `HK`, punch-up `PU`). Revise until approved, keeping scene ids stable. On approval mark gate 2, set Stage to `storyboard`, and hand off to 🎨 Iris (`vt-storyboard`).
