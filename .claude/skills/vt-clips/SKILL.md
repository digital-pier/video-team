---
name: vt-clips
description: Plans the motion for every scene, renders preview motion clips from stills, and writes AI video prompts for hero shots. Use when the user asks for motion, animation, video clips, or b-roll
---

# Clips

Owner: 🎥 Kai. Input: `storyboard.md`, `images/`, `audio/vo/*.wav`. Output: final Motion per scene in `storyboard.md`, `clips/ai-prompts.md` when needed, any `clips/<id>.mp4`.

The toolkit animates stills with camera moves (zoom, pan) at render time; that is the default for every scene. Real video only enters through `clips/<id>.mp4` files.

1. Read the storyboard and look at the images. Get each scene's VO duration (`ffprobe` or the audio report).
2. **Motion pass.** Confirm or change each scene's Motion so the move matches the narration (push in on a reveal, pan along a process, zoom out on a big-picture line) and no two consecutive scenes repeat. Update `storyboard.md`.
3. **Preview.** For 2-3 representative scenes render a preview so the human can judge the feel:
   `uv run {project-root}/tools/vt.py clip --image videos/<slug>/images/<id>.png --motion <move> --duration <vo seconds + 0.4> --out videos/<slug>/clips/preview-<id>.mp4`
   (Previews are not used by the edit — only `clips/<id>.mp4` is.)
4. **Hero shots.** For scenes marked `Motion: clip`, write AI video prompts to `clips/ai-prompts.md` (menu `AI`) and tell the human how to drop results in as `clips/<id>.mp4`. Any scene without a clip falls back to its still + move, so this never blocks the edit.
5. Update `status.md` (Stage: clips, log), rebuild the review page.
6. **Gate:** approve or notes. On approval mark gate 6, set Stage to `edit`, and hand off to ✂️ Rowan (`vt-edit`).
