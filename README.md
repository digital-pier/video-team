# Video Team 🎬

An AI YouTube production crew for Claude Code, built on the [BMad Method](https://github.com/bmad-code-org/BMAD-METHOD) agent architecture. BMad's software-delivery agents were rewritten as a video team that writes scripts, creates images, records voiceover, designs sound, animates scenes, edits, renders MP4s, and stops for **your review** at every stage.

## Quick start

```bash
brew install ffmpeg uv     # once
cp .env.example .env       # optional: add OPENAI_API_KEY / ELEVENLABS_API_KEY
uv run tools/vt.py doctor  # check setup
claude                     # open Claude Code in this folder
```

Then in Claude Code:

```
/vt-produce a 3-minute explainer on why octopuses are so smart
```

or talk to an agent directly: `/vt-agent-producer`, `/vt-agent-writer`, … Ask `/vt-help` any time.

## The team

| | Agent | Skill | Does |
|---|---|---|---|
| 🎬 | Paige — Producer | `/vt-agent-producer` | brief, status, review gates, end-to-end runs |
| 🔎 | Theo — Strategist | `/vt-agent-strategist` | ideas, titles, thumbnail concepts, publish pack |
| ✍️ | Quinn — Scriptwriter | `/vt-agent-writer` | scene-by-scene narration script |
| 🎨 | Iris — Art Director | `/vt-agent-art-director` | style bible, storyboard, images, thumbnails |
| 🎧 | Rhea — Sound Designer | `/vt-agent-sound` | voiceover, sound effects, music bed |
| 🎥 | Kai — Motion Designer | `/vt-agent-motion` | camera moves, preview clips, AI video prompts |
| ✂️ | Rowan — Editor | `/vt-agent-editor` | timeline, mix, draft/final renders, revisions |

`/vt-party-mode` puts them in a room to argue about your video.

## How review works

Every stage ends at a gate. The team rebuilds `videos/<slug>/review/index.html` (latest render, storyboard with images and audio players, script, sound) and waits for you. Give notes in chat ("s03 too dark, VO in s05 too fast") or in `review/feedback.md`, then `/vt-review` routes each note to the right agent, applies it, and re-renders.

## Providers

| Need | With a key | Free fallback |
|---|---|---|
| Images | OpenAI (`OPENAI_API_KEY`) | labeled placeholder cards |
| Voiceover | ElevenLabs or OpenAI | macOS `say` |
| Sound effects | ElevenLabs | synthesized (whoosh, impact, riser, ding…) |
| Music | your licensed track in `audio/music/` | synthesized ambient pad |
| Motion | AI video clips you generate from Kai's prompts | Ken Burns moves on stills |
| Edit/render | — | ffmpeg (local) |

## Customize

- Channel-wide voice/brand/audience notes: add `channel/*.md` — every agent loads them.
- Change an agent's persona, principles or menu: `custom/<skill-name>.toml` with the same keys as its `customize.toml`.

## Credits

Agent, menu, customization and party-mode architecture adapted from the BMad Method (MIT, see `LICENSE-BMAD-METHOD`). This project is not affiliated with or endorsed by BMad Code, LLC.
