---
name: vt-publish
description: Creates the YouTube publish pack — title, description, chapters, tags, captions file and thumbnail. Use when the user asks for upload metadata, a description, chapters, tags, or the publish pack
---

# Publish Pack

Owner: 🔎 Theo, with 🎨 Iris for the thumbnail. Output: `publish/publish.md`, `publish/thumbnail-*.png`.

1. Read the brief, script, `publish/packaging.md` if present, and the latest render + `.srt` in `renders/`.
2. **Chapters:** compute scene start times by summing durations from the render (or from VO durations + `scene_padding` in `edit/timeline.json`). Group scenes into 3-8 chapters; the first must be `0:00`.
3. **Write `publish/publish.md`:** 3 title options (recommend one), a description (first two lines hook the search result; then summary, chapters, CTA, credits for any music/sources), 10-15 tags, hashtags (max 3), category, and the captions file to upload (the `.srt` next to the final render).
4. **Thumbnail:** if none exists, run the art director's thumbnail item (`vt-agent-art-director` menu `TH`).
5. Update `status.md` (Stage: publish, log) and rebuild the review page.
6. **Gate:** human approves. Mark gate 8 and set Stage to `done`. Tell them the upload itself is theirs to do in YouTube Studio: video file, `.srt` under Subtitles, thumbnail, and the text from `publish.md`.
