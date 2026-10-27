---
name: vt-images
description: Generates or regenerates the still image for each storyboard scene. Use when the user asks to create images, generate visuals, or redo a scene's picture
---

# Images

Owner: 🎨 Iris. Input: `storyboard.md`. Output: `images/<id>.png` (1920x1080, or 1080x1920 for vertical videos).

1. Read `storyboard.md`. Run `uv run {project-root}/tools/vt.py doctor`. If no image provider key is set, tell the human images will be labeled placeholders (great for timing the edit; swap later) and that `OPENAI_API_KEY` in `.env` enables real images. For a paid provider with more than ~12 images, state the count and confirm before generating.
2. For each scene (or only the scenes the human named), run:
   `uv run {project-root}/tools/vt.py image --prompt "<style bible>. <scene image prompt>" --label <id> --out {project-root}/videos/<slug>/images/<id>.png`
   Independent scenes can run in parallel. When regenerating, keep the old image as `<id>-prev.png` so the human can compare.
3. Look at each generated image (read the file). Regenerate once on your own if it clearly misses the prompt, has garbled text, or breaks the style; mention what you redid.
4. Rebuild the review page with `--open` the first time, update `status.md` (Stage: images, log), and summarize.
5. **Gate:** ask for approval or per-scene notes ("s04 too dark"). Apply notes by editing that scene's prompt in `storyboard.md` and regenerating only that scene. On approval mark gate 4, set Stage to `audio`, and hand off to 🎧 Rhea (`vt-audio`).
