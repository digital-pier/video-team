---
name: vt-edit
description: Assembles the timeline from the storyboard and assets and renders a draft video. Use when the user asks to edit, cut, assemble, or render the video
---

# Edit

Owner: ✂️ Rowan. Input: `storyboard.md`, `images/`, `clips/`, `audio/`. Output: `edit/timeline.json`, `renders/draft-vN.mp4` + `.srt`.

1. Check assets: every scene needs `images/<id>.png` or `clips/<id>.mp4`, and normally `audio/vo/<id>.wav`. List anything missing and offer to have the owner make it, or to render with the gap (silent scene, `min_duration`).
2. **Write `edit/timeline.json`** (schema in `{project-root}/CLAUDE.md`):
   - `visual` = `clips/<id>.mp4` when it exists, else `images/<id>.png`; `motion` from the storyboard.
   - `vo` = `audio/vo/<id>.wav`; SFX from the storyboard cues with `at` seconds and volume (0.4-0.8 under narration).
   - `music` = the bed in `audio/music/` at volume ~0.10-0.15. `fade` 0.25, `scene_padding` 0.3-0.6 (tighter for fast-paced videos). Vertical videos: `"resolution": [1080, 1920]`.
   - Preserve any manual tweaks already in an existing timeline unless the human asked to rebuild it.
3. **Render a draft:** `uv run {project-root}/tools/vt.py render <slug> --draft`. Fix errors yourself (missing file, typo) and re-run.
4. Sanity-check: grab 2-3 frames with `ffmpeg -ss <t> -i <render> -frames:v 1 <scratch>.png` and look at them; confirm the duration matches the sum of scenes.
5. Rebuild the review page with `--open`, update `status.md` (Stage: edit, log), and report: render path, runtime vs target, scene timings, and anything you'd tighten.
6. **Gate:** the human watches the draft. Notes go through `vt-review`. On approval mark gate 7, render the final (editor menu `FN`), then hand off to 🔎 Theo (`vt-publish`).
