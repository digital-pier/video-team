# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10"]
# ///
"""Video Team media toolkit.

The agents call this CLI to turn plans (markdown/JSON) into media. Every
generator has a paid provider and a free local fallback so a whole video can be
produced with no API keys (placeholder art, macOS voice, synthesized SFX).

Run `uv run tools/vt.py --help` or `uv run tools/vt.py doctor`.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
TEMPLATES = ROOT / "tools" / "templates"


# --------------------------------------------------------------------------- utils

def load_env() -> None:
    """Load KEY=VALUE pairs from .env without overriding the real environment."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def need(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        die(f"`{binary}` not found. Install it (macOS: `brew install ffmpeg`).")
    return path


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        die(f"command failed: {' '.join(cmd[:6])} ...\n{proc.stderr[-2000:]}")


def probe_duration(path: Path) -> float:
    need("ffprobe")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    try:
        return float(out)
    except ValueError:
        die(f"could not read duration of {path}")
    return 0.0


def http_post(url: str, headers: dict, payload: dict) -> bytes:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers}
    )
    import time

    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 5:  # rate/concurrency limit: back off and retry
                time.sleep(2 ** attempt * 2)
                continue
            die(f"{url} -> HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")
    return b""


def pick(provider: str, order: list[tuple[str, str | None]]) -> str:
    """Resolve provider 'auto' to the first one whose env key is present."""
    if provider != "auto":
        return provider
    for name, key in order:
        if key is None or os.environ.get(key):
            return name
    return order[-1][0]


def to_audio(src: Path, out: Path) -> None:
    """Convert any audio file to the format implied by `out`'s extension."""
    need("ffmpeg")
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(src), "-ar", "48000", "-ac", "2", str(out)])


def video_dir(arg: str) -> Path:
    p = Path(arg)
    if not p.is_absolute() and not p.exists():
        p = VIDEOS / arg
    if not p.exists():
        die(f"video project not found: {arg}")
    return p.resolve()


# --------------------------------------------------------------------------- doctor

def cmd_doctor(_: argparse.Namespace) -> None:
    def row(ok: bool, label: str, hint: str = "") -> None:
        print(f"  {'✅' if ok else '⚪'} {label}" + (f"  — {hint}" if hint and not ok else ""))

    print("Video Team toolkit check\n\nRequired:")
    row(bool(shutil.which("ffmpeg")), "ffmpeg / ffprobe", "brew install ffmpeg")
    print("\nFree local fallbacks:")
    row(bool(shutil.which("say")), "macOS `say` voiceover", "macOS only; use OpenAI/ElevenLabs elsewhere")
    row(True, "placeholder images (Pillow)")
    row(bool(shutil.which("ffmpeg")), "synthesized SFX + music bed + Ken Burns motion")
    print("\nOptional AI providers (set in .env):")
    row(bool(os.environ.get("OPENAI_API_KEY")), "OPENAI_API_KEY — images + voiceover", "add to .env for AI images")
    row(bool(os.environ.get("ELEVENLABS_API_KEY")), "ELEVENLABS_API_KEY — voiceover + sound effects",
        "add to .env for premium voice/SFX")
    print()


# --------------------------------------------------------------------------- new project

def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "untitled"


def cmd_new(a: argparse.Namespace) -> None:
    slug = slugify(a.slug or a.title)
    d = VIDEOS / slug
    if d.exists():
        die(f"{d} already exists")
    for sub in ["images", "clips", "audio/vo", "audio/sfx", "audio/music", "edit", "renders", "review", "publish"]:
        (d / sub).mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    for name in ["brief.md", "status.md"]:
        text = (TEMPLATES / name).read_text()
        (d / name).write_text(text.replace("{{title}}", a.title).replace("{{slug}}", slug).replace("{{date}}", today))
    print(d)


# --------------------------------------------------------------------------- images

def placeholder_image(prompt: str, out: Path, w: int, h: int, label: str | None) -> None:
    from PIL import Image, ImageDraw, ImageFont

    seed = sum(map(ord, prompt)) % 360
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    import colorsys

    c1 = [int(x * 255) for x in colorsys.hsv_to_rgb(seed / 360, 0.55, 0.35)]
    c2 = [int(x * 255) for x in colorsys.hsv_to_rgb(((seed + 50) % 360) / 360, 0.6, 0.75)]
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))

    def font(size: int):
        for f in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
            if Path(f).exists():
                return ImageFont.truetype(f, size)
        return ImageFont.load_default()

    big, small = font(h // 12), font(h // 28)
    y = h // 3
    if label:
        draw.text((w // 12, y - h // 8), label, font=small, fill=(255, 255, 255, 180))
    for line in textwrap.wrap(prompt, width=38)[:5]:
        draw.text((w // 12, y), line, font=big, fill="white")
        y += int(h / 10)
    draw.text((w // 12, h - h // 10), "PLACEHOLDER — regenerate with an image provider", font=small,
              fill=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)


def cmd_image(a: argparse.Namespace) -> None:
    w, h = map(int, a.size.lower().split("x"))
    out = Path(a.out)
    provider = pick(a.provider, [("openai", "OPENAI_API_KEY"), ("placeholder", None)])
    if provider == "placeholder":
        placeholder_image(a.prompt, out, w, h, a.label)
    elif provider == "openai":
        # The API only supports a few sizes; generate landscape/portrait/square and fit to target.
        api_size = "1536x1024" if w > h else "1024x1536" if h > w else "1024x1024"
        body = http_post(
            "https://api.openai.com/v1/images/generations",
            {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            {"model": os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"), "prompt": a.prompt, "size": api_size,
             "n": 1},
        )
        data = json.loads(body)["data"][0]
        raw = base64.b64decode(data["b64_json"]) if data.get("b64_json") else urllib.request.urlopen(
            data["url"]).read()
        from PIL import Image, ImageOps
        import io

        img = ImageOps.fit(Image.open(io.BytesIO(raw)).convert("RGB"), (w, h), Image.LANCZOS)
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out)
    else:
        die(f"unknown image provider {provider}")
    print(f"{out}  [{provider}]")


# --------------------------------------------------------------------------- voice

def cmd_voice(a: argparse.Namespace) -> None:
    text = Path(a.text_file).read_text().strip() if a.text_file else a.text
    if not text:
        die("no text")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    provider = pick(a.provider, [("elevenlabs", "ELEVENLABS_API_KEY"), ("openai", "OPENAI_API_KEY"), ("say", None)])
    with tempfile.TemporaryDirectory() as tmp:
        if provider == "say":
            need("say")
            raw = Path(tmp) / "vo.aiff"
            cmd = ["say", "-o", str(raw)]
            if a.voice:
                cmd += ["-v", a.voice]
            if a.rate:
                cmd += ["-r", str(a.rate)]
            subprocess.run(cmd + [text], check=True)
        elif provider == "openai":
            raw = Path(tmp) / "vo.mp3"
            payload = {"model": os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
                       "voice": a.voice or os.environ.get("OPENAI_TTS_VOICE", "alloy"), "input": text}
            if a.style:
                payload["instructions"] = a.style
            raw.write_bytes(http_post("https://api.openai.com/v1/audio/speech",
                                      {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}, payload))
        elif provider == "elevenlabs":
            raw = Path(tmp) / "vo.mp3"
            voice = a.voice or os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
            raw.write_bytes(http_post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                {"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")}))
        else:
            die(f"unknown voice provider {provider}")
        to_audio(raw, out)
    print(f"{out}  [{provider}] {probe_duration(out):.2f}s")


# --------------------------------------------------------------------------- sfx / music

SYNTH = {
    # name: (lavfi source, filter chain) — duration is substituted as {d}
    "whoosh": ("anoisesrc=color=pink:d={d}", "bandpass=f=1200:w=1800,afade=t=in:d={d2},afade=t=out:st={d2}:d={d2},volume=0.6"),
    "riser": ("sine=f=200:d={d}", "vibrato=f=6,afade=t=in:d={d},asetrate=48000*1.0,volume=0.4"),
    "impact": ("sine=f=55:d={d}", "afade=t=out:st=0.05:d={d},volume=1.2"),
    "ding": ("sine=f=1318:d={d}", "afade=t=out:st=0.02:d={d},volume=0.5"),
    "click": ("anoisesrc=color=white:d=0.04", "highpass=f=2000,volume=0.6"),
    "pop": ("sine=f=600:d=0.12", "afade=t=out:st=0.01:d=0.11,volume=0.6"),
    "static": ("anoisesrc=color=white:d={d}", "volume=0.15"),
}


def synth(kind: str, dur: float, out: Path) -> None:
    need("ffmpeg")
    if kind not in SYNTH:
        die(f"synth sfx must be one of: {', '.join(SYNTH)}")
    src, chain = SYNTH[kind]
    fmt = {"d": f"{dur:.2f}", "d2": f"{dur / 2:.2f}"}
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", src.format(**fmt), "-af", chain.format(**fmt), "-ar", "48000",
         "-ac", "2", str(out)])


def cmd_sfx(a: argparse.Namespace) -> None:
    out = Path(a.out)
    provider = pick(a.provider, [("elevenlabs", "ELEVENLABS_API_KEY"), ("synth", None)])
    if provider == "synth":
        kind = a.kind or next((k for k in SYNTH if k in a.prompt.lower()), "whoosh")
        synth(kind, a.duration, out)
        provider = f"synth:{kind}"
    elif provider == "elevenlabs":
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "sfx.mp3"
            raw.write_bytes(http_post("https://api.elevenlabs.io/v1/sound-generation",
                                      {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                                      {"text": a.prompt, "duration_seconds": a.duration}))
            to_audio(raw, out)
    else:
        die(f"unknown sfx provider {provider}")
    print(f"{out}  [{provider}]")


MOODS = {  # chord root frequencies for a simple ambient pad
    "calm": [220.0, 277.18, 329.63], "uplifting": [261.63, 329.63, 392.0],
    "tense": [207.65, 246.94, 311.13], "dark": [146.83, 174.61, 220.0],
}


def cmd_music(a: argparse.Namespace) -> None:
    """Placeholder ambient pad. For real music drop a licensed track into audio/music/."""
    need("ffmpeg")
    freqs = MOODS.get(a.mood, MOODS["calm"])
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y"]
    for f in freqs:
        cmd += ["-f", "lavfi", "-i", f"sine=f={f}:d={a.duration}"]
    n = len(freqs)
    fc = (f"{''.join(f'[{i}]' for i in range(n))}amix=inputs={n},tremolo=f=0.2:d=0.4,lowpass=f=1200,"
          f"afade=t=in:d=2,afade=t=out:st={max(a.duration - 3, 0)}:d=3,volume=0.5[a]")
    run(cmd + ["-filter_complex", fc, "-map", "[a]", "-ar", "48000", "-ac", "2", str(out)])
    print(f"{out}  [synth pad: {a.mood}]")


# --------------------------------------------------------------------------- motion clips

def kenburns_filter(motion: str, frames: int, w: int, h: int, fps: int) -> str:
    z_in, z_out = f"1+0.18*on/{frames}", f"1.18-0.18*on/{frames}"
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    moves = {
        "zoom-in": (z_in, cx, cy),
        "zoom-out": (z_out, cx, cy),
        "pan-left": ("1.15", f"(iw-iw/zoom)*(1-on/{frames})", cy),
        "pan-right": ("1.15", f"(iw-iw/zoom)*on/{frames}", cy),
        "pan-up": ("1.15", cx, f"(ih-ih/zoom)*(1-on/{frames})"),
        "pan-down": ("1.15", cx, f"(ih-ih/zoom)*on/{frames}"),
        "static": ("1", "0", "0"),
    }
    if motion not in moves:
        die(f"motion must be one of: {', '.join(moves)}")
    z, x, y = moves[motion]
    # Upscale first so zoompan's integer cropping doesn't jitter.
    return (f"scale={w * 4}:{h * 4}:force_original_aspect_ratio=increase,crop={w * 4}:{h * 4},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps},format=yuv420p")


def make_kenburns(image: Path, out: Path, dur: float, motion: str, w: int, h: int, fps: int) -> None:
    need("ffmpeg")
    frames = max(int(round(dur * fps)), 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(image), "-vf",
         kenburns_filter(motion, frames, w, h, fps), "-frames:v", str(frames), "-c:v", "libx264",
         "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", str(out)])


def cmd_clip(a: argparse.Namespace) -> None:
    w, h = map(int, a.size.lower().split("x"))
    make_kenburns(Path(a.image), Path(a.out), a.duration, a.motion, w, h, a.fps)
    print(f"{a.out}  [kenburns:{a.motion}] {a.duration:.2f}s")


# --------------------------------------------------------------------------- render

def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def caption_chunks(text: str, start: float, dur: float, words_per: int = 8) -> list[tuple[float, float, str]]:
    """Split a scene's narration into evenly timed caption cards (weighted by length)."""
    words = text.split()
    if not words:
        return []
    chunks = [" ".join(words[i:i + words_per]) for i in range(0, len(words), words_per)]
    total = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        d = dur * len(c) / total
        out.append((t, t + d, c))
        t += d
    return out


BOLD_FONTS = ["/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def text_overlay(content: str, out: Path, w: int, h: int, position: str, scale: float) -> None:
    """Render bold, outlined title text onto a transparent full-frame PNG."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    size = int(h * 0.085 * scale)
    path = next((f for f in BOLD_FONTS if Path(f).exists()), None)
    font = ImageFont.truetype(path, size) if path else ImageFont.load_default()
    lines = content.split("\n")
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = max(size // 14, 2)
    boxes = [draw.textbbox((0, 0), ln, font=font, stroke_width=stroke) for ln in lines]
    line_h = int(size * 1.2)
    block_h = line_h * len(lines)
    y0 = {"top": int(h * 0.1), "bottom": int(h * 0.88) - block_h, "lower-third": int(h * 0.72) - block_h // 2,
          "left": (h - block_h) // 2, "right": (h - block_h) // 2}.get(position, (h - block_h) // 2)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for i, (ln, bb) in enumerate(zip(lines, boxes)):
        tw = bb[2] - bb[0]
        x = {"left": int(w * 0.07), "right": int(w * 0.93) - tw}.get(position, (w - tw) // 2)
        y = y0 + i * line_h
        sdraw.text((x + size // 16, y + size // 12), ln, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), ln, font=font, fill="white", stroke_width=stroke, stroke_fill=(10, 20, 30))
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(size // 10)), img).save(out)


def cmd_render(a: argparse.Namespace) -> None:
    need("ffmpeg")
    vdir = video_dir(a.video)
    tl_path = vdir / "edit" / "timeline.json"
    if not tl_path.exists():
        die(f"missing {tl_path} — the editor writes it from the storyboard")
    tl = json.loads(tl_path.read_text())
    w, h = tl.get("resolution", [1920, 1080])
    fps = tl.get("fps", 30)
    if a.draft:
        w, h = w // 2, h // 2
    pad = tl.get("scene_padding", 0.4)
    fade = tl.get("fade", 0.25)
    work = vdir / "edit" / ".build"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    segs, srt, t = [], [], 0.0
    for i, sc in enumerate(tl["scenes"]):
        sid = sc.get("id", f"s{i + 1:02}")
        vo = vdir / sc["vo"] if sc.get("vo") else None
        vo_len = probe_duration(vo) if vo and vo.exists() else 0.0
        if vo and not vo.exists():
            print(f"warning: {sid} voiceover missing ({sc['vo']}); scene is silent", file=sys.stderr)
        dur = float(sc.get("duration") or max(vo_len + pad, sc.get("min_duration", 3.0)))

        # Visual: a supplied clip (trimmed/looped) or a Ken Burns move over a still.
        visual = vdir / sc["visual"]
        if not visual.exists():
            die(f"{sid}: visual not found: {sc['visual']}")
        vid = work / f"{sid}_v.mp4"
        if visual.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
            run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(visual), "-t", f"{dur:.3f}", "-an", "-vf",
                 f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},format=yuv420p",
                 "-c:v", "libx264", "-crf", "20", str(vid)])
        else:
            make_kenburns(visual, vid, dur, sc.get("motion", "zoom-in"), w, h, fps)

        # Audio: voiceover (offset by vo_delay) + timed SFX, padded to exact scene length.
        inputs, labels, fc = [], [], []
        delay = float(sc.get("vo_delay", 0.15))
        if vo_len:
            inputs += ["-i", str(vo)]
            fc.append(f"[{len(inputs) // 2 - 1}]adelay={int(delay * 1000)}:all=1[vo]")
            labels.append("[vo]")
        for j, fx in enumerate(sc.get("sfx", [])):
            f = vdir / fx["file"]
            if not f.exists():
                print(f"warning: {sid} sfx missing ({fx['file']})", file=sys.stderr)
                continue
            inputs += ["-i", str(f)]
            k = len(inputs) // 2 - 1
            fc.append(f"[{k}]adelay={int(float(fx.get('at', 0)) * 1000)}:all=1,volume={fx.get('volume', 0.8)}[fx{j}]")
            labels.append(f"[fx{j}]")
        aud = work / f"{sid}_a.wav"
        if labels:
            fc.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad,atrim=0:{dur:.3f}[a]")
            run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[a]", "-ar", "48000", "-ac",
                 "2", str(aud)])
        else:
            run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", f"{dur:.3f}", str(aud)])

        # On-screen text: each overlay is a transparent PNG faded in/out over its time window.
        texts = sc.get("text") or []
        texts = [texts] if isinstance(texts, dict) else texts
        ov_inputs, chain, last = [], [], "[0:v]"
        for j, tx in enumerate(texts):
            png = work / f"{sid}_t{j}.png"
            text_overlay(tx["content"], png, w, h, tx.get("position", "center"), tx.get("size", 1.0))
            ov_inputs += ["-loop", "1", "-i", str(png)]
            st = float(tx.get("start", 0.3))
            en = min(float(tx.get("end", dur - 0.3)), dur)
            k = j + 2  # inputs 0 = video, 1 = audio
            chain.append(f"[{k}:v]format=rgba,fade=t=in:st={st:.3f}:d=0.3:alpha=1,"
                         f"fade=t=out:st={max(en - 0.3, st):.3f}:d=0.3:alpha=1[t{j}]")
            chain.append(f"{last}[t{j}]overlay=0:0:shortest=1[o{j}]")
            last = f"[o{j}]"
        chain.append(f"{last}" + (f"fade=t=in:d={fade},fade=t=out:st={max(dur - fade, 0):.3f}:d={fade}"
                                  if fade else "null") + "[v]")
        seg = work / f"{sid}.mp4"
        run(["ffmpeg", "-y", "-i", str(vid), "-i", str(aud), *ov_inputs, "-filter_complex", ";".join(chain),
             "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(fps),
             "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}", str(seg)])
        segs.append(seg)
        caption = sc.get("caption") or (vo.with_suffix(".txt").read_text().strip()
                                        if vo and vo.with_suffix(".txt").exists() else "")
        srt += caption_chunks(caption, t + delay, vo_len or dur - delay)
        t += dur
        print(f"  {sid}: {dur:.2f}s")

    concat_list = work / "concat.txt"
    concat_list.write_text("".join(f"file '{s}'\n" for s in segs))
    joined = work / "joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(joined)])

    renders = vdir / "renders"
    renders.mkdir(exist_ok=True)
    n = 1 + max([int(m.group(1)) for p in renders.glob("*-v*.mp4") if (m := re.search(r"-v(\d+)\.mp4$", p.name))]
                or [0])
    kind = "draft" if a.draft else "final"
    out = renders / f"{kind}-v{n}.mp4"
    srt_path = out.with_suffix(".srt")
    srt_path.write_text("\n".join(f"{i}\n{srt_time(s)} --> {srt_time(e)}\n{txt}\n"
                                  for i, (s, e, txt) in enumerate(srt, 1)))

    music = tl.get("music")
    mp = vdir / music["file"] if music else None
    cmd = ["ffmpeg", "-y", "-i", str(joined)]
    if mp and mp.exists():
        vol = music.get("volume", 0.12)
        # Duck the music under narration with a sidechain compressor.
        cmd += ["-stream_loop", "-1", "-i", str(mp), "-filter_complex",
                f"[1:a]volume={vol},atrim=0:{t:.3f},afade=t=out:st={max(t - 2, 0):.3f}:d=2[m];"
                f"[0:a]asplit=2[nar][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=6:release=400[duck];"
                f"[nar][duck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5", "-map", "0:v", "-map", "0:a"]
    run(cmd + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out)])

    has_subs = "subtitles" in subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True,
                                             text=True).stdout
    if tl.get("burn_captions") and srt and not has_subs:
        print("note: this ffmpeg has no libass, so captions were not burned in. Upload the .srt to YouTube "
              "instead (recommended), or install an ffmpeg built with libass.", file=sys.stderr)
    elif tl.get("burn_captions") and srt:
        burned = out.with_name(out.stem + "-captions.mp4")
        run(["ffmpeg", "-y", "-i", str(out), "-vf",
             f"subtitles={srt_path}:force_style='FontSize=22,Outline=2,MarginV=40'", "-c:a", "copy", str(burned)])
        print(burned)
    shutil.rmtree(work, ignore_errors=True)
    print(f"{out}  ({t:.1f}s, {w}x{h})\n{srt_path}")


# --------------------------------------------------------------------------- thumbnail text

def cmd_thumb(a: argparse.Namespace) -> None:
    """Overlay bold headline text onto a thumbnail background image (1280x720)."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    img = ImageOps.fit(Image.open(a.image).convert("RGB"), (1280, 720), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    font_path = next((f for f in ["/System/Library/Fonts/Supplemental/Impact.ttf",
                                  "/System/Library/Fonts/Supplemental/Arial Black.ttf",
                                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if Path(f).exists()), None)
    lines = textwrap.wrap(a.text.upper(), width=14)[:3]
    size = 140 if len(lines) == 1 else 110
    font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    y = 720 - 60 - len(lines) * (size + 10) if a.position == "bottom" else 60
    for line in lines:
        draw.text((60, y), line, font=font, fill=a.color, stroke_width=8, stroke_fill="black")
        y += size + 10
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    img.save(a.out)
    print(a.out)


# --------------------------------------------------------------------------- review page

def cmd_review(a: argparse.Namespace) -> None:
    vdir = video_dir(a.video)

    def rel(p: Path) -> str:
        return html.escape(os.path.relpath(p, vdir / "review"))

    def md(name: str) -> str:
        p = vdir / name
        return html.escape(p.read_text()) if p.exists() else "<em>not written yet</em>"

    renders = sorted((vdir / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    latest = renders[-1] if renders else None
    tl_path = vdir / "edit" / "timeline.json"
    scenes = json.loads(tl_path.read_text())["scenes"] if tl_path.exists() else []
    if not scenes:  # before the edit exists, show whatever stills and VO are on disk
        scenes = [{"id": im.stem, "visual": (f"clips/preview-{im.stem}.mp4" if (vdir / "clips" / f"preview-{im.stem}.mp4")
                                             .exists() else f"images/{im.name}"),
                   **({"vo": f"audio/vo/{im.stem}.wav"} if (vdir / "audio/vo" / f"{im.stem}.wav").exists() else {})}
                  for im in sorted((vdir / "images").glob("s*.png")) if re.fullmatch(r"s\d+[a-z]?", im.stem)]
    cards = []
    for sc in scenes:
        vis = vdir / sc.get("visual", "")
        media = ""
        if vis.is_file():
            media = (f'<video src="{rel(vis)}" muted loop autoplay playsinline></video>'
                     if vis.suffix in {".mp4", ".mov", ".webm"} else f'<img src="{rel(vis)}" loading="lazy">')
        vo = vdir / sc["vo"] if sc.get("vo") else None
        txt = vo.with_suffix(".txt") if vo else None
        cards.append(f"""<article class="card"><div class="frame">{media or '<div class="missing">no visual yet</div>'}</div>
<h3>{html.escape(sc.get('id', ''))} <small>{html.escape(sc.get('motion', ''))}</small></h3>
<p>{html.escape(txt.read_text()) if txt and txt.exists() else html.escape(sc.get('caption', ''))}</p>
{f'<audio controls src="{rel(vo)}"></audio>' if vo and vo.exists() else ''}</article>""")
    thumbs = sorted((vdir / "publish").glob("thumbnail*.png"))
    sfx = sorted((vdir / "audio" / "vo").glob("audition-*.wav")) + sorted((vdir / "audio" / "sfx").glob("*.*")) + sorted((vdir / "audio" / "music").glob("*.*"))

    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Review — {html.escape(vdir.name)}</title>
<style>
:root{{--bg:#0f1115;--card:#181b22;--fg:#e8e8ea;--mute:#9aa0aa;--acc:#ff4d4d}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif}}
main{{max-width:1200px;margin:auto;padding:24px}} h1{{margin:0 0 4px}} h2{{margin-top:40px;border-bottom:1px solid #333;padding-bottom:6px}}
.mute{{color:var(--mute)}} video.main{{width:100%;border-radius:10px;background:#000}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px}}
.card{{background:var(--card);border-radius:10px;padding:12px}} .card h3{{margin:8px 0 4px;font-size:14px}}
.card small{{color:var(--mute);font-weight:normal}} .card p{{font-size:13px;color:#cfd2d8}}
.frame img,.frame video{{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:6px}}
.missing{{aspect-ratio:16/9;display:grid;place-items:center;background:#222;border-radius:6px;color:var(--mute)}}
audio{{width:100%}} pre{{white-space:pre-wrap;background:var(--card);padding:16px;border-radius:10px;font-size:13px}}
details{{margin:12px 0}} summary{{cursor:pointer;font-weight:600}} .thumbs img{{width:320px;border-radius:8px;margin-right:12px}}
.box{{background:#2a1d1d;border-left:4px solid var(--acc);padding:12px 16px;border-radius:6px}}
</style></head><body><main>
<h1>🎬 {html.escape(vdir.name)}</h1><p class="mute">Review page generated {dt.datetime.now():%Y-%m-%d %H:%M}</p>
<div class="box">To give feedback: tell the team in chat (e.g. <em>“scene s03 image is too dark, VO in s05 too fast”</em>)
or write notes in <code>review/feedback.md</code> and ask <code>/vt-review</code> to process them.</div>
<h2>Latest render</h2>
{f'<video class="main" controls src="{rel(latest)}"><track kind="captions" src="{rel(latest.with_suffix(".srt"))}"></video><p class="mute">{html.escape(latest.name)} · {len(renders)} render(s) total</p>' if latest else '<p class="mute">No render yet.</p>'}
<h2>Storyboard ({len(scenes)} scenes)</h2><div class="grid">{''.join(cards) or '<p class="mute">No timeline yet.</p>'}</div>
<h2>Sound</h2>{''.join(f'<p>{html.escape(p.name)}<br><audio controls src="{rel(p)}"></audio></p>' for p in sfx) or '<p class="mute">None yet.</p>'}
<h2>Thumbnails</h2><div class="thumbs">{''.join(f'<img src="{rel(p)}">' for p in thumbs) or '<p class="mute">None yet.</p>'}</div>
<h2>Documents</h2>
<details><summary>Status</summary><pre>{md('status.md')}</pre></details>
<details><summary>Brief</summary><pre>{md('brief.md')}</pre></details>
<details open><summary>Script</summary><pre>{md('script.md')}</pre></details>
<details><summary>Storyboard</summary><pre>{md('storyboard.md')}</pre></details>
<details><summary>Publish pack</summary><pre>{md('publish/publish.md')}</pre></details>
</main></body></html>"""
    out = vdir / "review" / "index.html"
    out.write_text(page)
    if not (vdir / "review" / "feedback.md").exists():
        (vdir / "review" / "feedback.md").write_text("# Feedback\n\n<!-- Write notes here, one per line. "
                                                     "Reference scenes by id (s01, s02...). -->\n\n")
    print(out)
    if a.open and shutil.which("open"):
        subprocess.run(["open", str(out)])


# --------------------------------------------------------------------------- status

def cmd_status(a: argparse.Namespace) -> None:
    targets = [video_dir(a.video)] if a.video else sorted(p for p in VIDEOS.glob("*") if p.is_dir())
    if not targets:
        print("No video projects yet. Ask the Producer to start one (/vt-new-video).")
    for d in targets:
        s = d / "status.md"
        stage = re.search(r"^\*\*Stage:\*\*\s*(.+)$", s.read_text(), re.M) if s.exists() else None
        n = lambda g: len(list(d.glob(g)))
        print(f"{d.name:40} stage={stage.group(1) if stage else '?':18} images={n('images/*.png')} "
              f"vo={n('audio/vo/*.wav')} sfx={n('audio/sfx/*')} renders={n('renders/*.mp4')}")


# --------------------------------------------------------------------------- cli

def main() -> None:
    load_env()
    p = argparse.ArgumentParser(prog="vt", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="check ffmpeg and provider keys").set_defaults(fn=cmd_doctor)

    s = sub.add_parser("new", help="create a video project folder")
    s.add_argument("title"); s.add_argument("--slug")
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser("image", help="generate an image")
    s.add_argument("--prompt", required=True); s.add_argument("--out", required=True)
    s.add_argument("--size", default="1920x1080"); s.add_argument("--label")
    s.add_argument("--provider", default="auto", choices=["auto", "openai", "placeholder"])
    s.set_defaults(fn=cmd_image)

    s = sub.add_parser("voice", help="text to speech")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--text"); g.add_argument("--text-file")
    s.add_argument("--out", required=True); s.add_argument("--voice"); s.add_argument("--rate", type=int)
    s.add_argument("--style", help="delivery direction (OpenAI only)")
    s.add_argument("--provider", default="auto", choices=["auto", "elevenlabs", "openai", "say"])
    s.set_defaults(fn=cmd_voice)

    s = sub.add_parser("sfx", help="generate a sound effect")
    s.add_argument("--prompt", required=True); s.add_argument("--out", required=True)
    s.add_argument("--duration", type=float, default=1.0); s.add_argument("--kind", choices=list(SYNTH))
    s.add_argument("--provider", default="auto", choices=["auto", "elevenlabs", "synth"])
    s.set_defaults(fn=cmd_sfx)

    s = sub.add_parser("music", help="synthesize a placeholder ambient music bed")
    s.add_argument("--out", required=True); s.add_argument("--duration", type=float, default=60)
    s.add_argument("--mood", default="calm", choices=list(MOODS))
    s.set_defaults(fn=cmd_music)

    s = sub.add_parser("clip", help="animate a still into a motion clip (Ken Burns)")
    s.add_argument("--image", required=True); s.add_argument("--out", required=True)
    s.add_argument("--duration", type=float, default=5); s.add_argument("--motion", default="zoom-in")
    s.add_argument("--size", default="1920x1080"); s.add_argument("--fps", type=int, default=30)
    s.set_defaults(fn=cmd_clip)

    s = sub.add_parser("render", help="render edit/timeline.json to renders/")
    s.add_argument("video"); s.add_argument("--draft", action="store_true", help="half resolution, faster")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("thumb", help="put headline text on a thumbnail image")
    s.add_argument("--image", required=True); s.add_argument("--text", required=True)
    s.add_argument("--out", required=True); s.add_argument("--color", default="#FFE600")
    s.add_argument("--position", default="bottom", choices=["top", "bottom"])
    s.set_defaults(fn=cmd_thumb)

    s = sub.add_parser("review", help="build review/index.html")
    s.add_argument("video"); s.add_argument("--open", action="store_true")
    s.set_defaults(fn=cmd_review)

    s = sub.add_parser("status", help="show project status")
    s.add_argument("video", nargs="?")
    s.set_defaults(fn=cmd_status)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
