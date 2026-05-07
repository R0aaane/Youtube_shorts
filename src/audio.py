from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIO_ASSETS_DIR = PROJECT_ROOT / "assets" / "audio"
AUDIO_DIR = PROJECT_ROOT / "output" / "audio"
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
RESULT_PATH = METADATA_DIR / "simulation_result.json"
SAMPLE_RATE = 44_100
WAV_CACHE: dict[str, list[float]] = {}


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


def load_wav_asset(name: str) -> list[float] | None:
    if name in WAV_CACHE:
        return WAV_CACHE[name]
    path = AUDIO_ASSETS_DIR / f"{name}.wav"
    if not path.exists():
        return None
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_rate = wav_file.getframerate()
        if sample_width != 2:
            return None
        raw = wav_file.readframes(wav_file.getnframes())
    values: list[float] = []
    frame_width = sample_width * channels
    for offset in range(0, len(raw), frame_width):
        total = 0
        for channel in range(channels):
            start = offset + channel * sample_width
            total += struct.unpack("<h", raw[start : start + sample_width])[0]
        values.append((total / channels) / 32768)
    if frame_rate != SAMPLE_RATE and values:
        resampled_length = max(1, round(len(values) * SAMPLE_RATE / frame_rate))
        resampled: list[float] = []
        for index in range(resampled_length):
            source = index * frame_rate / SAMPLE_RATE
            left = min(len(values) - 1, math.floor(source))
            right = min(len(values) - 1, left + 1)
            blend = source - left
            resampled.append(values[left] * (1 - blend) + values[right] * blend)
        values = resampled
    WAV_CACHE[name] = values
    return values


def add_wav_asset(samples: list[float], start_seconds: float, name: str, *, volume: float = 0.72) -> bool:
    clip = load_wav_asset(name)
    if clip is None:
        return False
    start = max(0, round(start_seconds * SAMPLE_RATE))
    for index, value in enumerate(clip):
        target = start + index
        if target >= len(samples):
            break
        samples[target] += value * volume
    return True


def add_swept_tone(
    samples: list[float],
    start_seconds: float,
    duration: float,
    start_frequency: float,
    end_frequency: float,
    volume: float,
) -> None:
    start = max(0, round(start_seconds * SAMPLE_RATE))
    length = max(1, round(duration * SAMPLE_RATE))
    phase = 0.0
    for index in range(length):
        target = start + index
        if target >= len(samples):
            break
        progress = index / length
        frequency = start_frequency + (end_frequency - start_frequency) * progress
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        envelope = min(1.0, progress * 10) * min(1.0, (1 - progress) * 5)
        samples[target] += math.sin(phase) * volume * envelope


def add_noise_hit(samples: list[float], start_seconds: float, duration: float, volume: float, *, seed: int = 17, lowpass: float = 0.35) -> None:
    start = max(0, round(start_seconds * SAMPLE_RATE))
    length = max(1, round(duration * SAMPLE_RATE))
    filtered = 0.0
    for index in range(length):
        target = start + index
        if target >= len(samples):
            break
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        noise = ((seed / 0x7FFFFFFF) * 2) - 1
        filtered += (noise - filtered) * lowpass
        progress = index / length
        envelope = min(1.0, progress * 18) * ((1 - progress) ** 2.3)
        samples[target] += filtered * volume * envelope


def add_thump(samples: list[float], start_seconds: float, *, volume: float = 0.22, heavy: bool = False) -> None:
    base = 58 if heavy else 92
    duration = 0.19 if heavy else 0.11
    add_tone(samples, start_seconds, duration, base, volume)
    add_tone(samples, start_seconds + 0.012, duration * 0.7, base * 1.55, volume * 0.28)
    add_noise_hit(samples, start_seconds, duration * 0.8, volume * (0.72 if heavy else 0.48), seed=1203 if heavy else 412, lowpass=0.18)


def add_splat(samples: list[float], start_seconds: float, *, volume: float = 0.18) -> None:
    add_noise_hit(samples, start_seconds, 0.18, volume, seed=876, lowpass=0.18)
    add_swept_tone(samples, start_seconds + 0.012, 0.18, 165, 82, volume * 0.58)
    add_tone(samples, start_seconds + 0.055, 0.1, 96, volume * 0.26)


def add_wet_splat(samples: list[float], start_seconds: float, *, volume: float = 0.2) -> None:
    add_noise_hit(samples, start_seconds, 0.22, volume, seed=9342, lowpass=0.12)
    add_swept_tone(samples, start_seconds + 0.006, 0.2, 210, 72, volume * 0.7)
    add_noise_hit(samples, start_seconds + 0.045, 0.1, volume * 0.65, seed=223, lowpass=0.42)
    add_tone(samples, start_seconds + 0.04, 0.16, 68, volume * 0.28)


def add_food_bump(samples: list[float], start_seconds: float, *, volume: float = 0.16) -> None:
    add_noise_hit(samples, start_seconds, 0.1, volume, seed=5021, lowpass=0.14)
    add_swept_tone(samples, start_seconds + 0.004, 0.11, 132, 86, volume * 0.34)
    add_tone(samples, start_seconds + 0.016, 0.07, 78, volume * 0.16)


def add_soft_smack(samples: list[float], start_seconds: float, *, volume: float = 0.15) -> None:
    add_noise_hit(samples, start_seconds, 0.08, volume, seed=1188, lowpass=0.28)
    add_swept_tone(samples, start_seconds + 0.006, 0.09, 240, 138, volume * 0.32)
    add_noise_hit(samples, start_seconds + 0.032, 0.055, volume * 0.45, seed=404, lowpass=0.54)


def add_sizzle(samples: list[float], start_seconds: float, *, volume: float = 0.09) -> None:
    add_noise_hit(samples, start_seconds, 0.22, volume, seed=2219, lowpass=0.72)
    add_noise_hit(samples, start_seconds + 0.05, 0.16, volume * 0.55, seed=591, lowpass=0.86)


def add_crunch(samples: list[float], start_seconds: float, *, volume: float = 0.12) -> None:
    for offset, seed in [(0.0, 33), (0.025, 3401), (0.055, 780)]:
        add_noise_hit(samples, start_seconds + offset, 0.045, volume, seed=seed, lowpass=0.62)
    add_tone(samples, start_seconds + 0.02, 0.05, 240, volume * 0.35)


def add_squash(samples: list[float], start_seconds: float, *, volume: float = 0.18) -> None:
    add_crunch(samples, start_seconds, volume=volume * 0.7)
    add_wet_splat(samples, start_seconds + 0.018, volume=volume)
    add_swept_tone(samples, start_seconds + 0.025, 0.14, 125, 58, volume * 0.42)


def add_sub_bass_hit(samples: list[float], start_seconds: float, *, volume: float = 0.32) -> None:
    add_swept_tone(samples, start_seconds, 0.34, 58, 34, volume)
    add_tone(samples, start_seconds + 0.018, 0.26, 42, volume * 0.82)
    add_noise_hit(samples, start_seconds, 0.16, volume * 0.45, seed=8080, lowpass=0.09)
    add_wet_splat(samples, start_seconds + 0.025, volume=volume * 0.45)


def add_kitchen_ding(samples: list[float], start_seconds: float, *, volume: float = 0.12) -> None:
    add_tone(samples, start_seconds, 0.42, 1046, volume)
    add_tone(samples, start_seconds + 0.015, 0.38, 1568, volume * 0.38)


def add_voice_call(samples: list[float], start_seconds: float, word: str) -> None:
    if word == "ready":
        syllables = [(150, 185, 0.0, 0.16), (170, 135, 0.15, 0.18), (145, 175, 0.31, 0.16)]
        volume = 0.1
    else:
        syllables = [(125, 190, 0.0, 0.12), (190, 145, 0.1, 0.2)]
        volume = 0.13
    for start_frequency, end_frequency, offset, duration in syllables:
        add_swept_tone(samples, start_seconds + offset, duration, start_frequency, end_frequency, volume)
        add_swept_tone(samples, start_seconds + offset, duration, start_frequency * 2.1, end_frequency * 2.1, volume * 0.32)
        add_swept_tone(samples, start_seconds + offset, duration, start_frequency * 3.2, end_frequency * 3.2, volume * 0.14)
    add_noise_hit(samples, start_seconds + 0.02, 0.32, 0.035, seed=913, lowpass=0.2)


def add_event_sound(samples: list[float], kind: str, seconds: float) -> None:
    if kind == "ready":
        if not add_wav_asset(samples, seconds, "ready", volume=0.82):
            add_voice_call(samples, seconds, "ready")
    elif kind == "fight":
        if not add_wav_asset(samples, seconds, "fight", volume=0.86):
            add_voice_call(samples, seconds, "fight")
        add_thump(samples, seconds + 0.1, volume=0.18)
    elif kind == "impact":
        add_food_bump(samples, seconds, volume=0.14)
    elif kind == "soft_hit":
        add_soft_smack(samples, seconds, volume=0.15)
    elif kind == "heavy_hit":
        add_thump(samples, seconds, volume=0.2, heavy=True)
        add_splat(samples, seconds + 0.018, volume=0.12)
    elif kind == "big_hit":
        add_thump(samples, seconds, volume=0.27, heavy=True)
        add_splat(samples, seconds + 0.012, volume=0.18)
    elif kind == "burn":
        add_sizzle(samples, seconds, volume=0.1)
    elif kind == "fire_tick":
        add_sizzle(samples, seconds, volume=0.07)
    elif kind == "cheese_shot":
        add_splat(samples, seconds, volume=0.13)
        add_noise_hit(samples, seconds + 0.06, 0.09, 0.07, seed=1468, lowpass=0.28)
    elif kind == "cheese_stick":
        add_wet_splat(samples, seconds, volume=0.2)
    elif kind == "cheese_tick":
        add_sizzle(samples, seconds, volume=0.075)
    elif kind == "ingredient_spawn":
        add_crunch(samples, seconds, volume=0.105)
    elif kind == "ingredient_hit":
        add_squash(samples, seconds, volume=0.2)
    elif kind == "charge_start":
        add_noise_hit(samples, seconds, 0.18, 0.1, seed=7001, lowpass=0.2)
        add_tone(samples, seconds, 0.18, 118, 0.09)
    elif kind == "charge_hit":
        add_sub_bass_hit(samples, seconds, volume=0.34)
    elif kind in {"victory", "win"}:
        add_kitchen_ding(samples, seconds)


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
