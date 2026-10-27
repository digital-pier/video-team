---
name: vt-audio
description: Records the voiceover for every scene, creates sound effects and the music bed. Use when the user asks for voiceover, narration, sound effects, SFX, or music
---

# Audio

Owner: 🎧 Rhea. Input: `script.md`, `storyboard.md` (Audio section, SFX cues). Output: `audio/vo/<id>.txt` + `.wav`, `audio/sfx/*.wav`, `audio/music/*`.

1. Read the script and storyboard; run `uv run {project-root}/tools/vt.py doctor` to see which providers are live. If the voice was never chosen, offer a quick audition (sound designer menu `VC`) or use the storyboard's choice.
2. **Voiceover.** For each scene write the VO text verbatim from `script.md` to `videos/<slug>/audio/vo/<id>.txt`, then:
   `uv run {project-root}/tools/vt.py voice --text-file videos/<slug>/audio/vo/<id>.txt --out videos/<slug>/audio/vo/<id>.wav [--voice V] [--rate N] [--style "<delivery>"]`
   Use the same voice settings for every scene. Collect durations and compare the total with the target length; flag any scene over ~20 s.
3. **SFX.** Make each sound in the storyboard's SFX palette once, named for what it is (`whoosh.wav`, `impact.wav`):
   `uv run {project-root}/tools/vt.py sfx --prompt "<description>" --duration <s> --out videos/<slug>/audio/sfx/<name>.wav` (add `--kind` from the synth list when no ElevenLabs key is set).
4. **Music.** If the human supplied a track in `audio/music/`, use it. Otherwise make a placeholder bed covering the total runtime + 5 s: `uv run {project-root}/tools/vt.py music --mood <mood> --duration <s> --out videos/<slug>/audio/music/bed.wav`, and say it is a placeholder and that licensed tracks (e.g. YouTube Audio Library) can be dropped in.
5. Update `status.md` (Stage: audio, log), rebuild the review page, and report: provider used, total VO runtime vs target, list of SFX and music.
6. **Gate:** approve or notes (re-record with menu `VO`). On approval mark gate 5, set Stage to `clips`, and hand off to 🎥 Kai (`vt-clips`).
