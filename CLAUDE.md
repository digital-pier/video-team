# Video Team

An AI YouTube production team built on the BMad Method agent architecture (persona skills with menus, workflow skills, party mode). Seven agents take a video from idea to rendered MP4; the human reviews and approves every stage.

In skills, `{project-root}` means this repo root (run commands from here); `<slug>` is the video's folder name under `videos/`.

## The team

| Agent | Skill | Owns |
|---|---|---|
| 🎬 Paige — Producer | `vt-agent-producer` | brief, status, review gates, end-to-end runs |
| 🔎 Theo — YouTube Strategist | `vt-agent-strategist` | ideas, packaging, publish pack |
| ✍️ Quinn — Scriptwriter | `vt-agent-writer` | `script.md` |
| 🎨 Iris — Art Director | `vt-agent-art-director` | `storyboard.md`, `images/`, thumbnails |
| 🎧 Rhea — Sound Designer | `vt-agent-sound` | `audio/` (voiceover, SFX, music) |
| 🎥 Kai — Motion Designer | `vt-agent-motion` | motion plan, `clips/` |
| ✂️ Rowan — Video Editor | `vt-agent-editor` | `edit/timeline.json`, `renders/` |

Workflows: `vt-help`, `vt-new-video`, `vt-produce`, `vt-script`, `vt-storyboard`, `vt-images`, `vt-audio`, `vt-clips`, `vt-edit`, `vt-review`, `vt-publish`, `vt-party-mode`.

## Pipeline and gates

brief → script → storyboard → images → audio → clips → edit (draft) → final render → publish pack

Each stage ends at a **review gate**: rebuild the review page, show the human what changed, and wait. Only mark a gate `✅ approved` in `status.md` when the human approves in conversation. Update `**Stage:**` and add a log line (newest first) every time a stage starts, is approved, or is revised.

## Video project layout (`videos/<slug>/`)

```
brief.md            Producer + Strategist
status.md           stage, gates, log
script.md           Writer
storyboard.md       Art Director (+ Sound, Motion notes)
images/<id>.png     scene stills (1920x1080); variants <id>-b.png
clips/<id>.mp4      optional real video for a scene (overrides the still)
clips/ai-prompts.md prompts for external AI video tools
audio/vo/<id>.txt   exact narration for the scene (source of truth for TTS + captions)
audio/vo/<id>.wav   recorded narration
audio/sfx/*.wav     sound effects
audio/music/*       music bed
edit/timeline.json  Editor's cut
renders/draft-vN.mp4, final-vN.mp4 (+ .srt captions)
review/index.html   review page; review/feedback.md for written notes
publish/            packaging.md, publish.md, thumbnail-*.png
```

Scene ids are `s01`, `s02`, … and stay stable across revisions (insert as `s03a` rather than renumbering).

### `script.md` format

```markdown
# Script — <title>
Target: <length> · ~<words> words · Voice: <direction>

## s01 — <scene name>
**VO:** <exact narration, written for the ear>
**On screen:** <optional text overlay / lower third>
**Visual idea:** <what we see>
**Sound:** <optional SFX / music cue>
```

### `storyboard.md` format

```markdown
# Storyboard — <title>
## Style bible
<one paragraph prepended to every image prompt: medium, palette, lighting, lens, mood>
## Audio
Voice: <provider + voice + rate/style> · Music: <file or mood> · SFX palette: <list>

## s01 — <scene name>
- **Image prompt:** <subject, composition, framing; no style words — the bible adds those>
- **Motion:** zoom-in | zoom-out | pan-left | pan-right | pan-up | pan-down | static | clip
- **SFX:** <name> @ <seconds into scene> (vol 0-1)
- **Notes:** <text placement, continuity>
```

### `edit/timeline.json`

```json
{
  "resolution": [1920, 1080], "fps": 30, "fade": 0.25, "scene_padding": 0.4,
  "music": {"file": "audio/music/bed.wav", "volume": 0.12},
  "burn_captions": false,
  "scenes": [
    {"id": "s01", "visual": "images/s01.png", "motion": "zoom-in", "vo": "audio/vo/s01.wav",
     "vo_delay": 0.15, "sfx": [{"file": "audio/sfx/whoosh.wav", "at": 0.0, "volume": 0.7}]}
  ]
}
```

Scene length = VO length + `scene_padding` unless `duration` is set (use `min_duration` for silent scenes). `visual` may be a `.png` (gets a Ken Burns move) or a video file (trimmed/looped). Music is auto-ducked under narration and the mix is loudness-normalized to -14 LUFS.

## Toolkit: `uv run tools/vt.py <command>`

| Command | What it does |
|---|---|
| `doctor` | shows ffmpeg + which AI providers are configured |
| `new "<title>"` | creates `videos/<slug>/` with brief + status |
| `image --prompt P --out F [--size 1920x1080] [--provider auto\|openai\|placeholder]` | image generation |
| `voice --text-file F --out F.wav [--voice V] [--rate N] [--style S] [--provider auto\|elevenlabs\|openai\|say]` | narration |
| `sfx --prompt P --out F [--duration S] [--kind whoosh\|riser\|impact\|ding\|click\|pop\|static] [--provider auto\|elevenlabs\|synth]` | sound effects |
| `music --out F --duration S --mood calm\|uplifting\|tense\|dark` | placeholder ambient bed |
| `clip --image F --out F.mp4 --duration S --motion M` | Ken Burns preview clip |
| `render <slug> [--draft]` | renders timeline → `renders/` (draft = half resolution) |
| `thumb --image F --text T --out F` | YouTube thumbnail (1280x720) with headline text |
| `review <slug> [--open]` | builds `review/index.html` |
| `status [slug]` | stage + asset counts |

`auto` providers pick a paid API when its key is in `.env`, else the free local fallback. Placeholder images say PLACEHOLDER on them; tell the human when fallbacks were used. AI video generation (Runway/Kling/Veo/Sora) is not built in: the Motion Designer writes prompts, the human drops results in `clips/`.

## Rules

- The human is the director. Ask before spending on paid generation beyond the current stage's needs (e.g. regenerating all images).
- No real people's likenesses, trademarked characters, or copyrighted music in generated assets.
- Edit files in place and keep scene ids stable; never delete a previous render.
- Optional channel-wide guidance lives in `channel/*.md` (voice, brand, audience); every agent loads it.
- Personal agent overrides go in `custom/<skill-name>.toml` (same keys as the skill's `customize.toml`).
