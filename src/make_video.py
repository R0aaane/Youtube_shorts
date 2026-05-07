from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import audio


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "boss_battle_001.json"
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
PROJECT_AUDIO_DIR = PROJECT_ROOT / "output" / "audio"
RESULT_PATH = METADATA_DIR / "simulation_result.json"
DEFAULT_OUTPUT_NAME = "simulation_001"
DEFAULT_FPS = 60
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
SHORTS_DESCRIPTION = "#shorts #FoodBattle #PhysicsSimulation #BattleSimulation #satisfying"


def ensure_ffmpeg() -> str:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is not None:
        return ffmpeg_path

    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    candidates = sorted(winget_packages.glob("Gyan.FFmpeg_*/*/bin/ffmpeg.exe"), reverse=True)
    if candidates:
        return str(candidates[0])

    raise RuntimeError(
        "FFmpeg was not found. Install FFmpeg and make sure the `ffmpeg` command is available in PATH."
    )


def ensure_frames_exist() -> None:
    if not (FRAMES_DIR / "frame_000001.png").exists() and not (FRAMES_DIR / "frame_000001.jpg").exists():
        raise FileNotFoundError(
            f"Input frames were not found under: {FRAMES_DIR}\n"
            "Generate frames first with: python src/simulate.py --frames 600 --no-window"
        )


def input_pattern() -> Path:
    if (FRAMES_DIR / "frame_000001.jpg").exists():
        return FRAMES_DIR / "frame_%06d.jpg"
    return FRAMES_DIR / "frame_%06d.png"


def resolve_config_path(path: Path | None) -> Path | None:
    if path is not None:
        return path if path.is_absolute() else PROJECT_ROOT / path
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    return None


def load_video_config(path: Path | None) -> tuple[dict, Path | None]:
    config = {
        "fps": DEFAULT_FPS,
        "video_width": DEFAULT_WIDTH,
        "video_height": DEFAULT_HEIGHT,
        "output_name": DEFAULT_OUTPUT_NAME,
        "duration_seconds": 10,
        "boss_hp": 10000,
        "initial_ball_count": 10,
        "theme": "boss_battle",
        "fibonacci_count": 50,
        "exponential_count": 50,
        "food_types": None,
        "duel_left_food": "pizza",
        "duel_right_food": "burger",
        "duel_left_hp": 240,
        "duel_right_hp": 260,
        "duel_ball_radius": 118,
        "duel_speed_scale": 1.0,
        "duel_charge_speed": 1220,
        "duel_burger_charge_hp_cost": 40,
        "duel_ingredient_damage": 10,
        "duel_cheese_damage": 6,
        "duel_cheese_projectile_speed": 760,
        "audio_enabled": True,
    }
    config_path = resolve_config_path(path)
    if config_path is not None:
        config.update(json.loads(config_path.read_text(encoding="utf-8")))
    return config, config_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert rendered PNG frames to MP4.")
    parser.add_argument("--config", type=Path, help="Path to a simulation JSON config.")
    return parser.parse_args()


def make_video(config: dict) -> Path:
    ffmpeg_path = ensure_ffmpeg()
    ensure_frames_exist()
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    output_video = VIDEOS_DIR / f"{config['output_name']}.mp4"
    result = load_result()
    audio_path = audio.generate_audio(config, result)

    command = [
        ffmpeg_path,
        "-y",
        "-framerate",
        str(config["fps"]),
        "-i",
        str(input_pattern()),
    ]
    if audio_path is not None:
        command.extend(["-i", str(audio_path)])
    command.extend(
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-vf",
            f"scale={config['video_width']}:{config['video_height']}:flags=lanczos",
        ]
    )
    if audio_path is not None:
        command.extend(["-c:a", "aac", "-b:a", "128k", "-shortest"])
    command.extend(["-movflags", "+faststart", str(output_video)])

    subprocess.run(command, check=True)
    return output_video


def relative_path(path: Path) -> str:
    return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")


def load_result() -> dict:
    if not RESULT_PATH.exists():
        return {}
    return json.loads(RESULT_PATH.read_text(encoding="utf-8"))


def build_title(config: dict, result: dict) -> str:
    def display_food(value: str) -> str:
        return value.replace("_", " ").title()

    if config.get("theme") == "fibonacci_vs_exponential":
        return "100 Fibonacci VS Exponential Balls"

    if config.get("theme") == "food_boss":
        ball_count = config["initial_ball_count"]
        boss_hp = config["boss_hp"]
        status = result.get("status")
        if status == "CLEAR":
            clear_time = result.get("clear_time_seconds")
            if clear_time is not None:
                return f"Pizza and Burger Balls Beat {boss_hp:,} HP in {clear_time:.2f}s"
        return f"Can {ball_count} Food Balls Beat a {boss_hp:,} HP Boss?"

    if config.get("theme") == "food_duel":
        winner = result.get("winner")
        left = display_food(str(config.get("duel_left_food", "pizza")))
        right = display_food(str(config.get("duel_right_food", "burger")))
        if result.get("tie"):
            return f"{left} VS {right}: Unbelievable Tie in the Food Skill Battle"
        if winner:
            return f"{left} VS {right}: {winner} Wins the Food Skill Battle"
        return f"{left} VS {right}: Food Skill Battle"

    ball_count = config["initial_ball_count"]
    boss_hp = config["boss_hp"]
    status = result.get("status")
    if status == "CLEAR":
        clear_time = result.get("clear_time_seconds")
        if clear_time is not None:
            return f"Can {ball_count} Balls Destroy a {boss_hp:,} HP Boss in {clear_time:.2f}s?"
    return f"Can {ball_count} Balls Destroy a {boss_hp:,} HP Boss?"


def write_youtube_metadata(config: dict, config_path: Path | None, video_path: Path) -> Path:
    result = load_result()

    if config.get("theme") == "food_duel":
        description = SHORTS_DESCRIPTION
        tags = [
            "shorts",
            "food",
            str(config.get("duel_left_food", "pizza")),
            str(config.get("duel_right_food", "burger")),
            "versus",
            "physics simulation",
            "2d physics",
            "pymunk",
            "pygame",
            "skill battle",
            "satisfying",
        ]
    elif config.get("theme") == "food_boss":
        description = SHORTS_DESCRIPTION
        tags = [
            "shorts",
            "food",
            "pizza",
            "burger",
            "physics simulation",
            "2d physics",
            "pymunk",
            "pygame",
            "boss battle",
            "evolving balls",
            "satisfying",
        ]
    else:
        description = SHORTS_DESCRIPTION
        tags = [
            "shorts",
            "physics simulation",
            "2d physics",
            "pymunk",
            "pygame",
            "boss battle",
            "evolving balls",
            "fibonacci",
            "exponential",
            "math balls",
        ]

    actual_duration = round(result.get("frames_rendered", config["duration_seconds"] * config["fps"]) / max(1, config["fps"]), 3)
    metadata = {
        "title": build_title(config, result),
        "description": description,
        "tags": tags,
        "video_file": relative_path(video_path),
        "audio_file": relative_path(PROJECT_AUDIO_DIR / f"{config['output_name']}.wav")
        if config.get("audio_enabled", True)
        else None,
        "config_file": relative_path(config_path) if config_path is not None else None,
        "result": result,
        "duration_seconds": actual_duration,
        "configured_duration_seconds": config["duration_seconds"],
        "boss_hp": config["boss_hp"],
        "initial_ball_count": config["initial_ball_count"],
    }

    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = METADATA_DIR / f"{config['output_name']}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata_path


def main() -> int:
    args = parse_args()
    config, config_path = load_video_config(args.config)
    try:
        output_path = make_video(config)
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Video generation failed: {exc}", file=sys.stderr)
        return 1

    metadata_path = write_youtube_metadata(config, config_path, output_path)
    print(f"Video saved: {output_path}")
    print(f"Metadata saved: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
