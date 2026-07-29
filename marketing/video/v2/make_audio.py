#!/usr/bin/env python3
"""Create an original ambient UI-demo soundtrack for Daybook v2."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path


SAMPLE_RATE = 48_000
DURATION = 15
COUNT = SAMPLE_RATE * DURATION
OUTPUT = Path(__file__).resolve().parent / "public" / "soundtrack.wav"


def add_tone(
    channel: list[float],
    start: float,
    duration: float,
    frequency: float,
    amplitude: float,
    decay: float = 3.0,
) -> None:
    first = max(0, int(start * SAMPLE_RATE))
    length = min(int(duration * SAMPLE_RATE), COUNT - first)
    for index in range(length):
        local = index / SAMPLE_RATE
        attack = min(1.0, local / 0.025)
        envelope = attack * math.exp(-decay * local / max(duration, 0.001))
        fundamental = math.sin(2 * math.pi * frequency * local)
        overtone = math.sin(2 * math.pi * frequency * 2.01 * local) * 0.22
        channel[first + index] += (fundamental + overtone) * envelope * amplitude


def add_click(left: list[float], right: list[float], start: float, pan: float) -> None:
    first = int(start * SAMPLE_RATE)
    length = min(int(0.11 * SAMPLE_RATE), COUNT - first)
    phase = 0.0
    for index in range(length):
        local = index / SAMPLE_RATE
        phase += 2 * math.pi * (1650 - local * 7200) / SAMPLE_RATE
        envelope = math.exp(-52 * local)
        sample = (
            math.sin(phase) * 0.12 + random.uniform(-1, 1) * 0.035
        ) * envelope
        left[first + index] += sample * (1.0 - pan * 0.55)
        right[first + index] += sample * (0.45 + pan * 0.55)


def add_whoosh(left: list[float], right: list[float], center: float, direction: int) -> None:
    start = center - 0.36
    first = max(0, int(start * SAMPLE_RATE))
    length = min(int(0.66 * SAMPLE_RATE), COUNT - first)
    smooth = 0.0
    for index in range(length):
        local = index / SAMPLE_RATE
        position = local / 0.66
        envelope = math.sin(math.pi * position) ** 2.4
        noise = random.uniform(-1, 1)
        smooth += (noise - smooth) * (0.025 + position * 0.16)
        airy = (noise - smooth) * envelope * 0.095
        pan = position if direction > 0 else 1 - position
        left[first + index] += airy * (1 - pan * 0.62)
        right[first + index] += airy * (0.38 + pan * 0.62)


def add_sub_impact(left: list[float], right: list[float], start: float) -> None:
    first = int(start * SAMPLE_RATE)
    length = min(int(0.72 * SAMPLE_RATE), COUNT - first)
    phase = 0.0
    for index in range(length):
        local = index / SAMPLE_RATE
        frequency = 72 * math.exp(-7 * local) + 34
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        envelope = math.exp(-6.8 * local)
        sample = math.sin(phase) * envelope * 0.24
        left[first + index] += sample
        right[first + index] += sample


def main() -> None:
    random.seed(7282026)
    left = [0.0] * COUNT
    right = [0.0] * COUNT

    # A slow, warm D-minor-nine bed. No drum loop—the movement comes from the UI.
    chord = (73.42, 87.31, 110.00, 146.83, 164.81)
    for frequency_index, frequency in enumerate(chord):
        phase = frequency_index * 0.83
        for index in range(COUNT):
            time = index / SAMPLE_RATE
            fade_in = min(1.0, time / 1.2)
            fade_out = min(1.0, (DURATION - time) / 1.1)
            breathe = 0.62 + 0.38 * math.sin(2 * math.pi * (0.055 + frequency_index * 0.006) * time + phase)
            signal = math.sin(2 * math.pi * frequency * time + phase) * 0.011
            signal += math.sin(2 * math.pi * frequency * 0.5 * time + phase) * 0.004
            left[index] += signal * breathe * fade_in * fade_out * (0.88 if frequency_index % 2 else 1)
            right[index] += signal * breathe * fade_in * fade_out * (1 if frequency_index % 2 else 0.82)

    transition_times = (3.58, 6.70, 10.28, 13.22)
    for index, moment in enumerate(transition_times):
        add_whoosh(left, right, moment, 1 if index % 2 == 0 else -1)
        add_sub_impact(left, right, moment)
        note = (293.66, 349.23, 440.00, 587.33)[index]
        add_tone(left, moment + 0.04, 1.4, note, 0.045, decay=4.8)
        add_tone(right, moment + 0.06, 1.4, note * 1.002, 0.045, decay=4.8)

    click_times = (2.26, 3.58, 4.82, 6.70, 7.76, 9.02, 10.28, 11.68, 14.38)
    for index, moment in enumerate(click_times):
        add_click(left, right, moment, (index % 4) / 3)

    # Small glassy motifs reward the detail zooms.
    for moment, note in ((1.08, 587.33), (4.18, 659.25), (7.18, 523.25), (10.92, 698.46), (13.76, 440.0)):
        add_tone(left, moment, 1.1, note, 0.025, decay=5.5)
        add_tone(right, moment + 0.018, 1.1, note * 1.5, 0.018, decay=5.5)

    for index in range(COUNT):
        fade_in = min(1.0, index / int(0.18 * SAMPLE_RATE))
        fade_out = min(1.0, (COUNT - index - 1) / int(0.8 * SAMPLE_RATE))
        master = min(fade_in, fade_out)
        left[index] = math.tanh(left[index] * 1.35) * 0.82 * master
        right[index] = math.tanh(right[index] * 1.35) * 0.82 * master

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUTPUT), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        payload = bytearray()
        for left_sample, right_sample in zip(left, right):
            payload.extend(
                struct.pack(
                    "<hh",
                    max(-32767, min(32767, int(left_sample * 32767))),
                    max(-32767, min(32767, int(right_sample * 32767))),
                )
            )
        output.writeframes(payload)

    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
