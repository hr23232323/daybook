#!/usr/bin/env python3
"""Render Daybook's 15-second launch film with only system video tools."""

from __future__ import annotations

import argparse
import base64
import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path


WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 15
TOTAL_FRAMES = FPS * DURATION

ROOT = Path(__file__).resolve().parents[2]
VIDEO_DIR = Path(__file__).resolve().parent
SOURCE_DIR = VIDEO_DIR / "source"
OUTPUT_DIR = VIDEO_DIR / "output"

INK = "#17272c"
CREAM = "#f7f3eb"
PAPER = "#efe9de"
ORANGE = "#c9854d"
SAGE = "#b9d8cc"
MUTED = "#839094"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def progress(t: float, start: float, end: float) -> float:
    if end == start:
        return 1.0
    return clamp((t - start) / (end - start))


def ease_out(value: float) -> float:
    value = clamp(value)
    return 1 - (1 - value) ** 3


def ease_in_out(value: float) -> float:
    value = clamp(value)
    return 4 * value**3 if value < 0.5 else 1 - ((-2 * value + 2) ** 3) / 2


def scene_alpha(t: float, start: float, end: float, fade: float = 0.26) -> float:
    if t < start or t > end:
        return 0.0
    if t < start + fade:
        return ease_out(progress(t, start, start + fade))
    if t > end - fade:
        return ease_in_out(progress(t, end, end - fade))
    return 1.0


def esc(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@lru_cache(maxsize=12)
def data_uri(path: Path) -> str:
    media_type = "image/svg+xml" if path.suffix.lower() == ".svg" else "image/png"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{payload}"


def text(
    value: str,
    x: float,
    y: float,
    size: float,
    fill: str = CREAM,
    *,
    family: str = "Arial, sans-serif",
    weight: int = 700,
    anchor: str = "start",
    spacing: float = 0,
    opacity: float = 1,
    italic: bool = False,
) -> str:
    style = "italic" if italic else "normal"
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill}" font-family="{family}" '
        f'font-size="{size:.2f}" font-weight="{weight}" text-anchor="{anchor}" '
        f'letter-spacing="{spacing:.2f}" font-style="{style}" opacity="{opacity:.3f}">'
        f"{esc(value)}</text>"
    )


def screenshot(
    name: str,
    t: float,
    start: float,
    end: float,
    *,
    focus_start: tuple[float, float] = (800, 500),
    focus_end: tuple[float, float] = (800, 500),
    zoom_start: float = 1.0,
    zoom_end: float = 1.08,
) -> str:
    p = ease_in_out(progress(t, start, end))
    zoom = zoom_start + (zoom_end - zoom_start) * p
    focus_x = focus_start[0] + (focus_end[0] - focus_start[0]) * p
    focus_y = focus_start[1] + (focus_end[1] - focus_start[1]) * p
    width = WIDTH * zoom
    height = 800 * zoom
    x = WIDTH / 2 - (focus_x / 1600) * width
    y = HEIGHT / 2 - (focus_y / 1000) * height
    href = data_uri(SOURCE_DIR / f"{name}.png")
    return (
        f'<image href="{href}" x="{x:.2f}" y="{y:.2f}" width="{width:.2f}" '
        f'height="{height:.2f}" preserveAspectRatio="none"/>'
    )


def label_panel(
    headline: str,
    detail: str,
    t: float,
    start: float,
    *,
    width: float = 610,
    x: float = 54,
    y: float = 520,
    align: str = "left",
) -> str:
    p = ease_out(progress(t, start, start + 0.42))
    shift = (1 - p) * (70 if align == "left" else -70)
    panel_x = x + shift
    return f"""
      <g opacity="{p:.3f}">
        <rect x="{panel_x:.2f}" y="{y}" width="{width}" height="142" rx="8"
          fill="{INK}" opacity=".96"/>
        <rect x="{panel_x:.2f}" y="{y}" width="7" height="142" rx="3.5" fill="{ORANGE}"/>
        {text(headline, panel_x + 34, y + 56, 34, CREAM, spacing=1.4)}
        {text(detail, panel_x + 34, y + 98, 19, SAGE, weight=500)}
      </g>
    """


def screen_scene(
    name: str,
    t: float,
    start: float,
    end: float,
    headline: str,
    detail: str,
    *,
    focus_start: tuple[float, float] = (800, 500),
    focus_end: tuple[float, float] = (800, 500),
    zoom_end: float = 1.08,
    extras: str = "",
) -> str:
    alpha = scene_alpha(t, start, end)
    if alpha <= 0:
        return ""
    return f"""
      <g opacity="{alpha:.3f}">
        <rect width="{WIDTH}" height="{HEIGHT}" fill="{PAPER}"/>
        {screenshot(name, t, start, end, focus_start=focus_start,
                    focus_end=focus_end, zoom_end=zoom_end)}
        <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#vignette)" opacity=".32"/>
        {label_panel(headline, detail, t, start + 0.12)}
        {extras}
        <g transform="translate(1178 28)">
          <rect width="74" height="74" rx="18" fill="{INK}" opacity=".96"/>
          <image href="{data_uri(ROOT / 'assets/daybook-mark.svg')}"
            x="8" y="8" width="58" height="58"/>
        </g>
      </g>
    """


def intro_scene(t: float) -> str:
    alpha = 1.0 if t <= 1.58 else ease_in_out(progress(t, 1.86, 1.58))
    if alpha <= 0:
        return ""
    logo_p = 0.55 + 0.45 * ease_out(progress(t, 0.02, 0.45))
    first_p = 0.24 + 0.76 * ease_out(progress(t, 0.10, 0.58))
    second_p = ease_out(progress(t, 0.30, 0.86))
    detail_p = ease_out(progress(t, 0.62, 1.10))
    logo_scale = 0.76 + 0.24 * logo_p
    line_offset = (1 - first_p) * 80
    second_offset = (1 - second_p) * 110
    return f"""
      <g opacity="{alpha:.3f}">
        <rect width="{WIDTH}" height="{HEIGHT}" fill="{INK}"/>
        <g opacity=".18" stroke="{MUTED}" stroke-width="1">
          {''.join(f'<path d="M0 {98 + i * 74} H1280"/>' for i in range(8))}
          {''.join(f'<path d="M{80 + i * 120} 0 V720"/>' for i in range(11))}
        </g>
        <circle cx="{1090 - t * 44:.2f}" cy="110" r="260" fill="{ORANGE}" opacity=".08"/>
        <circle cx="160" cy="{680 - t * 30:.2f}" r="290" fill="{SAGE}" opacity=".06"/>
        <g transform="translate(72 62) scale({logo_scale:.3f})" opacity="{logo_p:.3f}">
          <image href="{data_uri(ROOT / 'assets/daybook-mark.svg')}" width="78" height="78"/>
        </g>
        {text("DAYBOOK", 168, 107, 22, CREAM, spacing=4, opacity=logo_p)}
        {text("LOCAL-FIRST FINANCE", 168, 136, 13, SAGE, weight=600, spacing=2.4, opacity=logo_p)}
        {text("YOUR MONEY.", 72 - line_offset, 326, 79, ORANGE, spacing=2.2, opacity=first_p)}
        {text("WITHOUT THE MYSTERY.", 72 - second_offset, 432, 71, CREAM,
              family="Georgia, serif", weight=700, opacity=second_p)}
        {text("A private ledger that runs on your machine.", 76, 505, 25, SAGE,
              weight=500, opacity=detail_p)}
        <rect x="76" y="552" width="{420 * detail_p:.2f}" height="4" rx="2" fill="{ORANGE}"/>
      </g>
    """


def discoveries_extras(t: float) -> str:
    p1 = ease_out(progress(t, 4.82, 5.24))
    p2 = ease_out(progress(t, 5.18, 5.62))
    return f"""
      <g transform="translate({900 + (1-p1)*80:.2f} 138)" opacity="{p1:.3f}">
        <rect width="280" height="96" rx="10" fill="{CREAM}" stroke="{ORANGE}" stroke-width="3"/>
        {text("$146 / MONTH", 22, 44, 29, INK, spacing=1)}
        {text("7 subscriptions surfaced", 22, 72, 16, MUTED, weight=500)}
      </g>
      <g transform="translate({940 + (1-p2)*90:.2f} 252)" opacity="{p2:.3f}">
        <rect width="240" height="76" rx="10" fill="{INK}"/>
        {text("COMPUTED LOCALLY", 20, 34, 16, SAGE, spacing=1.6)}
        {text("AUDIT EVERY NUMBER", 20, 58, 13, CREAM, spacing=1.2)}
      </g>
    """


def import_extras(t: float) -> str:
    labels = ["CSV", "OFX", "QFX", "SIMPLEFIN"]
    blocks = []
    for index, value in enumerate(labels):
        p = ease_out(progress(t, 8.02 + index * 0.10, 8.35 + index * 0.10))
        x = 780 + index * 104
        blocks.append(
            f'<g transform="translate({x:.2f} {142 + (1-p)*36:.2f})" opacity="{p:.3f}">'
            f'<rect width="90" height="42" rx="21" fill="{INK}"/>'
            f'{text(value, 45, 27, 14, CREAM, anchor="middle", spacing=1.3)}'
            "</g>"
        )
    return "".join(blocks)


def advisor_scene(t: float) -> str:
    start, end = 8.95, 12.35
    alpha = scene_alpha(t, start, end)
    if alpha <= 0:
        return ""
    tag_p = ease_out(progress(t, 10.0, 10.46))
    return f"""
      <g opacity="{alpha:.3f}">
        <rect width="{WIDTH}" height="{HEIGHT}" fill="{PAPER}"/>
        {screenshot("advisor", t, start, end, focus_start=(800, 500),
                    focus_end=(1015, 455), zoom_end=1.22)}
        <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#advisorShade)" opacity=".52"/>
        <g transform="translate({52 - (1-tag_p)*70:.2f} 62)" opacity="{tag_p:.3f}">
          <rect width="456" height="126" rx="9" fill="{INK}" opacity=".97"/>
          <rect width="456" height="6" rx="3" fill="{ORANGE}"/>
          {text("ASK YOUR LEDGER.", 28, 56, 34, CREAM, spacing=1.3)}
          {text("Read-only tools · adjustable thinking", 28, 92, 18, SAGE, weight=500)}
        </g>
        <g transform="translate(754 {574 + (1-tag_p)*46:.2f})" opacity="{tag_p:.3f}">
          <rect width="472" height="70" rx="35" fill="{CREAM}" stroke="{ORANGE}" stroke-width="3"/>
          {text("5 QUERIES  ·  2 PASSES  ·  GROUNDED", 236, 43, 16, INK,
                anchor="middle", spacing=1.3)}
        </g>
        <g transform="translate(1178 28)">
          <rect width="74" height="74" rx="18" fill="{INK}" opacity=".96"/>
          <image href="{data_uri(ROOT / 'assets/daybook-mark.svg')}"
            x="8" y="8" width="58" height="58"/>
        </g>
      </g>
    """


def end_scene(t: float) -> str:
    start = 12.0
    alpha = ease_out(progress(t, start, start + 0.32))
    if alpha <= 0:
        return ""
    logo_p = ease_out(progress(t, 12.08, 12.60))
    copy_p = ease_out(progress(t, 12.35, 12.95))
    cta_p = ease_out(progress(t, 12.82, 13.42))
    pulse = 1 + math.sin(max(0, t - 12.2) * 3.2) * 0.012
    return f"""
      <g opacity="{alpha:.3f}">
        <rect width="{WIDTH}" height="{HEIGHT}" fill="{INK}"/>
        <g opacity=".15" stroke="{MUTED}" stroke-width="1">
          <circle cx="640" cy="300" r="220"/>
          <circle cx="640" cy="300" r="300"/>
          <circle cx="640" cy="300" r="390"/>
        </g>
        <path d="M80 78 H{80 + 1120*cta_p:.2f}" stroke="{ORANGE}" stroke-width="3"/>
        <g transform="translate(584 104) scale({pulse:.3f})" opacity="{logo_p:.3f}">
          <image href="{data_uri(ROOT / 'assets/daybook-mark.svg')}" width="112" height="112"/>
        </g>
        {text("DAYBOOK", 640, 328, 82, CREAM, family="Georgia, serif",
              anchor="middle", opacity=copy_p)}
        {text("CLONE IT. OWN IT.", 640, 389, 27, ORANGE, anchor="middle",
              spacing=5.2, opacity=copy_p)}
        {text("PRIVATE  ·  LOCAL-FIRST  ·  OPEN SOURCE", 640, 450, 17, SAGE,
              anchor="middle", spacing=2.8, opacity=copy_p)}
        <g transform="translate(318 {500 + (1-cta_p)*40:.2f})" opacity="{cta_p:.3f}">
          <rect width="644" height="82" rx="41" fill="{CREAM}"/>
          {text("github.com/hr23232323/daybook", 322, 51, 24, INK,
                anchor="middle", weight=600)}
        </g>
        {text("v0.1.0", 640, 629, 14, MUTED, anchor="middle", spacing=2.2, opacity=cta_p)}
      </g>
    """


def transition_streaks(t: float) -> str:
    pieces = []
    for beat in (1.60, 4.20, 6.70, 7.76, 8.96, 12.02):
        p = progress(t, beat - 0.13, beat + 0.20)
        if 0 < p < 1:
            x = -180 + (WIDTH + 360) * ease_in_out(p)
            opacity = math.sin(math.pi * p) * 0.82
            pieces.append(
                f'<g opacity="{opacity:.3f}" transform="skewX(-12)">'
                f'<rect x="{x:.2f}" y="0" width="54" height="{HEIGHT}" fill="{ORANGE}"/>'
                f'<rect x="{x + 72:.2f}" y="0" width="9" height="{HEIGHT}" fill="{CREAM}"/>'
                "</g>"
            )
    return "".join(pieces)


def frame_svg(frame: int) -> str:
    t = frame / FPS
    statement = screen_scene(
        "statement",
        t,
        1.55,
        4.48,
        "SEE THE WHOLE PICTURE.",
        "Income → outflow. Nothing hidden.",
        focus_end=(910, 360),
        zoom_end=1.12,
    )
    discoveries = screen_scene(
        "discoveries",
        t,
        4.16,
        6.98,
        "FIND WHAT'S WORTH NOTICING.",
        "Patterns ranked against your own history.",
        focus_end=(920, 585),
        zoom_end=1.13,
        extras=discoveries_extras(t),
    )
    ledger = screen_scene(
        "ledger",
        t,
        6.66,
        7.96,
        "EVERY MOVEMENT. AUDITABLE.",
        "Search the source behind every number.",
        focus_end=(910, 500),
        zoom_end=1.09,
    )
    imports = screen_scene(
        "import",
        t,
        7.66,
        9.28,
        "BRING YOUR RECORDS HOME.",
        "Manual files stay entirely local.",
        focus_end=(680, 450),
        zoom_end=1.08,
        extras=import_extras(t),
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg"
      xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{HEIGHT}"
      viewBox="0 0 {WIDTH} {HEIGHT}">
      <defs>
        <linearGradient id="vignette" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="{INK}" stop-opacity=".08"/>
          <stop offset=".58" stop-color="{INK}" stop-opacity="0"/>
          <stop offset="1" stop-color="{INK}" stop-opacity=".38"/>
        </linearGradient>
        <linearGradient id="advisorShade" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="{INK}" stop-opacity=".22"/>
          <stop offset=".38" stop-color="{INK}" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <rect width="{WIDTH}" height="{HEIGHT}" fill="{INK}"/>
      {intro_scene(t)}
      {statement}
      {discoveries}
      {ledger}
      {imports}
      {advisor_scene(t)}
      {end_scene(t)}
      {transition_streaks(t)}
      <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="none"
        stroke="{INK}" stroke-opacity=".25" stroke-width="2"/>
    </svg>"""


def render_frame(args: tuple[int, Path, str]) -> Path:
    frame, frames_dir, rsvg = args
    output = frames_dir / f"frame-{frame:04d}.png"
    svg = frame_svg(frame).encode("utf-8")
    with output.open("wb") as handle:
        subprocess.run(
            [rsvg, "-w", str(WIDTH), "-h", str(HEIGHT)],
            input=svg,
            stdout=handle,
            check=True,
        )
    return output


def add_tone(samples: list[float], start: float, duration: float, frequency: float, amplitude: float) -> None:
    sample_rate = 44100
    first = max(0, int(start * sample_rate))
    count = min(int(duration * sample_rate), len(samples) - first)
    for index in range(count):
        local_t = index / sample_rate
        envelope = math.exp(-4.2 * local_t / max(duration, 0.001))
        samples[first + index] += math.sin(2 * math.pi * frequency * local_t) * amplitude * envelope


def add_kick(samples: list[float], start: float, amplitude: float = 0.72) -> None:
    sample_rate = 44100
    first = int(start * sample_rate)
    count = min(int(0.24 * sample_rate), len(samples) - first)
    phase = 0.0
    for index in range(count):
        local_t = index / sample_rate
        frequency = 112 * math.exp(-15 * local_t) + 43
        phase += 2 * math.pi * frequency / sample_rate
        envelope = math.exp(-19 * local_t)
        click = random.uniform(-1, 1) * math.exp(-90 * local_t) * 0.16
        samples[first + index] += (math.sin(phase) * envelope + click) * amplitude


def add_hat(samples: list[float], start: float, amplitude: float = 0.10) -> None:
    sample_rate = 44100
    first = int(start * sample_rate)
    count = min(int(0.075 * sample_rate), len(samples) - first)
    previous = 0.0
    for index in range(count):
        local_t = index / sample_rate
        noise = random.uniform(-1, 1)
        high = noise - previous * 0.72
        previous = noise
        samples[first + index] += high * math.exp(-52 * local_t) * amplitude


def add_whoosh(left: list[float], right: list[float], center: float) -> None:
    sample_rate = 44100
    start = center - 0.28
    first = max(0, int(start * sample_rate))
    count = min(int(0.52 * sample_rate), len(left) - first)
    lowpass = 0.0
    for index in range(count):
        local_t = index / sample_rate
        position = local_t / 0.52
        envelope = math.sin(math.pi * position) ** 1.8
        noise = random.uniform(-1, 1)
        lowpass += (noise - lowpass) * (0.08 + position * 0.22)
        signal = (noise - lowpass * 0.7) * envelope * 0.14
        pan = position
        left[first + index] += signal * (1 - pan * 0.55)
        right[first + index] += signal * (0.45 + pan * 0.55)


def synthesize_soundtrack(path: Path) -> None:
    sample_rate = 44100
    sample_count = DURATION * sample_rate
    left = [0.0] * sample_count
    right = [0.0] * sample_count
    random.seed(20260728)

    # Restrained D-minor pulse: enough energy to carry cuts, never required for meaning.
    bass_notes = [73.42, 73.42, 87.31, 65.41, 73.42, 98.00, 87.31, 65.41]
    beat = 0.5
    current = 0.08
    beat_index = 0
    while current < DURATION:
        add_kick(left, current, 0.58 if beat_index % 2 else 0.72)
        add_kick(right, current, 0.58 if beat_index % 2 else 0.72)
        add_hat(left, current + 0.25, 0.075)
        add_hat(right, current + 0.25, 0.11)
        if beat_index % 2 == 0:
            frequency = bass_notes[(beat_index // 2) % len(bass_notes)]
            add_tone(left, current + 0.015, 0.42, frequency, 0.16)
            add_tone(right, current + 0.015, 0.42, frequency, 0.16)
            add_tone(left, current + 0.015, 0.22, frequency * 2, 0.045)
            add_tone(right, current + 0.015, 0.22, frequency * 2, 0.045)
        current += beat
        beat_index += 1

    for transition in (1.60, 4.20, 6.70, 7.76, 8.96, 12.02):
        add_whoosh(left, right, transition)
        add_tone(left, transition, 0.38, 146.83, 0.13)
        add_tone(right, transition, 0.38, 146.83, 0.13)

    fade_samples = int(0.65 * sample_rate)
    for index in range(sample_count):
        fade_in = min(1.0, index / int(0.12 * sample_rate))
        fade_out = min(1.0, (sample_count - index - 1) / fade_samples)
        master = min(fade_in, fade_out)
        left[index] = math.tanh(left[index] * 1.38) * 0.72 * master
        right[index] = math.tanh(right[index] * 1.38) * 0.72 * master

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for l_sample, r_sample in zip(left, right):
            frames.extend(
                struct.pack(
                    "<hh",
                    int(clamp(l_sample, -1, 1) * 32767),
                    int(clamp(r_sample, -1, 1) * 32767),
                )
            )
        wav.writeframes(frames)


def command_path(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise SystemExit(f"Missing required command: {name}")
    return result


def render(output: Path, workers: int) -> None:
    rsvg = command_path("rsvg-convert")
    ffmpeg = command_path("ffmpeg")
    command_path("ffprobe")

    missing = [
        name
        for name in ("statement", "discoveries", "ledger", "import", "advisor")
        if not (SOURCE_DIR / f"{name}.png").exists()
    ]
    if missing:
        raise SystemExit(f"Missing source captures: {', '.join(missing)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="daybook-launch-") as temp_name:
        temp_dir = Path(temp_name)
        frames_dir = temp_dir / "frames"
        frames_dir.mkdir()
        soundtrack = temp_dir / "soundtrack.wav"

        print(f"Rendering {TOTAL_FRAMES} frames with {workers} workers…")
        tasks = ((frame, frames_dir, rsvg) for frame in range(TOTAL_FRAMES))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for completed, _ in enumerate(pool.map(render_frame, tasks), start=1):
                if completed % 90 == 0 or completed == TOTAL_FRAMES:
                    print(f"  {completed}/{TOTAL_FRAMES}")

        synthesize_soundtrack(soundtrack)
        cover = OUTPUT_DIR / "daybook-launch-cover.png"
        shutil.copy2(frames_dir / "frame-0024.png", cover)

        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "warning",
                "-framerate",
                str(FPS),
                "-i",
                str(frames_dir / "frame-%04d.png"),
                "-i",
                str(soundtrack),
                "-c:v",
                "libx264",
                "-preset",
                "slow",
                "-crf",
                "18",
                "-profile:v",
                "high",
                "-level",
                "4.0",
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(FPS),
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-ar",
                "48000",
                "-af",
                "loudnorm=I=-14:TP=-1.5:LRA=7",
                "-movflags",
                "+faststart",
                "-t",
                str(DURATION),
                str(output),
            ],
            check=True,
        )

    print(f"Wrote {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR / "daybook-launch-16x9.mp4",
        help="Output MP4 path",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(6, os.cpu_count() or 2),
        help="Parallel SVG render workers",
    )
    args = parser.parse_args()
    render(args.output.resolve(), max(1, args.workers))


if __name__ == "__main__":
    main()
