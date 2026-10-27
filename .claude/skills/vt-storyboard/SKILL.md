---
name: vt-storyboard
description: Turns the approved script into a storyboard with a style bible, image prompts, motion, and sound cues per scene. Use when the user asks for a storyboard, shot list, or visual plan
---

# Storyboard

Owner: 🎨 Iris, with notes from 🎧 Rhea (Audio section, SFX) and 🎥 Kai (Motion). Input: `script.md`, `brief.md`. Output: `storyboard.md` in the format in `{project-root}/CLAUDE.md`.

1. Read the brief and script. If the script gate is not approved, say so and ask whether to proceed.
2. **Style bible.** Propose 2 short style options matching the brief (medium, palette, lighting, lens/rendering, mood), recommend one, and use it unless the human picks the other. Keep it under 60 words; it is prepended to every image prompt.
3. **Audio line.** Voice (provider, voice, rate or delivery style — run `uv run {project-root}/tools/vt.py doctor` to see what is available), music mood or file, and a small SFX palette (3-6 sounds reused across the video).
4. **Per scene** write an image prompt (subject, action, composition, camera distance, where text will sit — no style words), a motion that fits the narration and differs from the previous scene, SFX cues with timings in seconds from scene start, and notes. Mark scenes that deserve real video as `Motion: clip`.
5. Show a compact table (id, image idea, motion, SFX) rather than the whole file.
6. Update `status.md` (Stage: storyboard, log), rebuild the review page.
7. **Gate:** approve or notes. On approval mark gate 3, set Stage to `images`, and continue to `vt-images`.
