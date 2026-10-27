---
name: vt-new-video
description: Starts a new YouTube video project and writes its brief with the human. Use when the user wants to start, create, or plan a new video
---

# New Video

Goal: a `videos/<slug>/` project with an approved `brief.md`.

1. **Get the idea.** If the user has not given one, ask what the video is about. If they are unsure, offer Theo's idea brainstorm (`vt-agent-strategist`, menu `ID`).
2. **Create the project:** `uv run {project-root}/tools/vt.py new "<working title>"`. It prints the folder path.
3. **Fill the brief by interview.** Ask in at most two short rounds, offering smart defaults the user can accept with "yes":
   - audience and what they want; format and target length (default: 16:9 explainer, 3-5 minutes; 9:16 Short = under 60 s at 1080x1920); tone; visual style; narrator voice.
   - key points, hook idea, call to action, constraints.
   Draft anything the user leaves open — label your guesses `(proposed)`.
4. Write `brief.md`. Propose 3 title + thumbnail-concept pairings in the brief's Hook section (Theo's packaging-first habit).
5. Update `status.md` (Stage: brief, log line), run `uv run {project-root}/tools/vt.py review <slug>`, and present the brief compactly.
6. **Gate:** ask the human to approve or change the brief. On approval mark gate 1 `✅ approved`, set Stage to `script`, and offer to hand off to ✍️ Quinn (`vt-script`) — or to continue end to end with `vt-produce`.
