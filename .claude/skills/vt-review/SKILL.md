---
name: vt-review
description: Collects the human's review notes on the active video, routes each note to the right agent, applies the changes, and re-renders. Use when the user gives feedback, notes, or revisions, or asks to review the video
---

# Review

Owner: 🎬 Paige coordinates; each note is fixed by its owner.

1. Rebuild and open the review page: `uv run {project-root}/tools/vt.py review <slug> --open`. Point the human at the latest render and the stage awaiting approval.
2. **Collect notes** from the conversation and from `review/feedback.md` (ignore its comment lines). If the human just says "review it", give a short critique of your own first — hook strength, pacing, audio balance, visual consistency — as suggestions, not changes.
3. **Triage** into a numbered table: note → owner → concrete change → files touched. Routing: wording/structure → ✍️ Quinn (`script.md`, then VO re-record); look of a scene → 🎨 Iris (prompt + regenerate that image); voice/SFX/music → 🎧 Rhea; movement → 🎥 Kai; timing, order, mix levels, cuts → ✂️ Rowan (`timeline.json`). Ask about any note that is ambiguous; otherwise proceed.
4. **Apply** in dependency order (script → images/VO → motion → timeline), each in its owner's voice. Keep scene ids stable. A script change to a scene means its `.txt` and `.wav` must be regenerated too.
5. If anything visual or audible changed, render a new draft (`vt.py render <slug> --draft`) — versions increment automatically.
6. Rebuild the review page, add a log line to `status.md` listing the notes addressed, clear the processed notes from `review/feedback.md` (move them under a `## Done` heading), and ask: approve, or another round?
