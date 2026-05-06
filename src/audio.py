from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = PROJECT_ROOT / "output" / "audio"
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
RESULT_PATH = METADATA_DIR / "simulation_result.json"
SAMPLE_RATE = 44_100


def load_result() -> dict:
    if not RESULT_PATH.exists():
        return {}
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def add_tone(samples: list[float], start_seconds: float, duration: float, frequency: float, volume: float) -> None:
    start = max(0, round(start_seconds * SAMPLE_RATE))
    length = max(1, round(duration * SAMPLE_RATE))
    for index in range(length):
        target = start + index
        if target >= len(samples):
            break
        progress = index / length
        envelope = min(1.0, progress * 12) * min(1.0, (1 - progress) * 8)
        samples[target] += math.sin(2 * math.pi * frequency * index / SAMPLE_RATE) * volume * envelope


def add_noise_hit(samples: list[float], start_seconds: float, duration: float, volume: float) -> None:
    start = max(0, round(start_seconds * SAMPLE_RATE))
    length = max(1, round(duration * SAMPLE_RATE))
    seed = 17
    for index in range(length):
        target = start + index
        if target >= len(samples):
            break
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        noise = ((seed / 0x7FFFFFFF) * 2) - 1
        progress = index / length
        envelope = (1 - progress) ** 2
        samples[target] += noise * volume * envelope


def add_arcade_call(samples: list[float], start_seconds: float, word: str) -> None:
    if word == "ready":
        notes = [(392, 0.0), (494, 0.12), (659, 0.24)]
        duration = 0.28
    else:
        notes = [(220, 0.0), (440, 0.08), (880, 0.16)]
        duration = 0.34
    for frequency, offset in notes:
        add_tone(samples, start_seconds + offset, duration, frequency, 0.26)
        add_tone(samples, start_seconds + offset, duration, frequency * 1.5, 0.08)


def add_event_sound(samples: list[float], kind: str, seconds: float) -> None:
    if kind == "ready":
        add_arcade_call(samples, seconds, "ready")
    elif kind == "fight":
        add_arcade_call(samples, seconds, "fight")
        add_noise_hit(samples, seconds + 0.05, 0.18, 0.25)
    elif kind == "impact":
        add_tone(samples, seconds, 0.11, 120, 0.22)
        add_noise_hit(samples, seconds, 0.09, 0.18)
    elif kind == "burn":
        add_tone(samples, seconds, 0.28, 360, 0.18)
        add_tone(samples, seconds, 0.28, 720, 0.08)
        add_noise_hit(samples, seconds, 0.18, 0.08)
    elif kind == "fire_tick":
        add_tone(samples, seconds, 0.08, 620, 0.14)
    elif kind == "cheese_shot":
        add_tone(samples, seconds, 0.12, 540, 0.16)
        add_tone(samples, seconds + 0.04, 0.12, 760, 0.12)
    elif kind == "cheese_stick":
        add_tone(samples, seconds, 0.16, 310, 0.18)
        add_noise_hit(samples, seconds, 0.08, 0.08)
    elif kind == "cheese_tick":
        add_tone(samples, seconds, 0.07, 690, 0.13)
    elif kind == "ingredient_spawn":
        add_tone(samples, seconds, 0.14, 260, 0.16)
        add_tone(samples, seconds + 0.06, 0.14, 420, 0.13)
    elif kind == "ingredient_hit":
        add_tone(samples, seconds, 0.1, 180, 0.18)
        add_noise_hit(samples, seconds, 0.07, 0.12)
    elif kind == "charge_start":
        add_tone(samples, seconds, 0.22, 180, 0.18)
        add_tone(samples, seconds + 0.04, 0.22, 520, 0.16)
    elif kind == "charge_hit":
        add_tone(samples, seconds, 0.16, 92, 0.28)
        add_tone(samples, seconds, 0.13, 780, 0.18)
        add_noise_hit(samples, seconds, 0.14, 0.25)


def write_wav(samples: list[float], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample))
            wav_file.writeframes(struct.pack("<h", round(clamped * 32767)))


def generate_audio(config: dict, result: dict | None = None) -> Path | None:
    if not config.get("audio_enabled", True):
        return None

    result = result or load_result()
    frames_rendered = int(result.get("frames_rendered", config.get("fps", 60) * config.get("duration_seconds", 10)))
    fps = int(result.get("fps", config.get("fps", 60)))
    duration = max(1.0, frames_rendered / max(1, fps))
    samples = [0.0] * (round((duration + 0.5) * SAMPLE_RATE))

    events = result.get("audio_events") or []
    if not events and config.get("theme") == "food_duel":
        events = [{"frame": 1, "kind": "ready"}, {"frame": 46, "kind": "fight"}]

    for event in events:
        frame = int(event.get("frame", 1))
        kind = str(event.get("kind", "impact"))
        add_event_sound(samples, kind, max(0.0, (frame - 1) / max(1, fps)))

    output_path = AUDIO_DIR / f"{config['output_name']}.wav"
    write_wav(samples, output_path)
    return output_path
