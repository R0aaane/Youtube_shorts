from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "boss_battle_001.json"
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"
INPUT_PATTERN = FRAMES_DIR / "frame_%06d.png"
DEFAULT_OUTPUT_NAME = "simulation_001"
DEFAULT_FPS = 60
DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920


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
    first_frame = FRAMES_DIR / "frame_000001.png"
    if not first_frame.exists():
        raise FileNotFoundError(
            f"Input frames were not found: {first_frame}\n"
            "Generate frames first with: python src/simulate.py --frames 600 --no-window"
        )


def load_video_config(path: Path | None) -> dict:
    config = {
        "fps": DEFAULT_FPS,
        "video_width": DEFAULT_WIDTH,
        "video_height": DEFAULT_HEIGHT,
        "output_name": DEFAULT_OUTPUT_NAME,
    }
    if path is not None:
        config_path = path if path.is_absolute() else PROJECT_ROOT / path
        config.update(json.loads(config_path.read_text(encoding="utf-8")))
    elif DEFAULT_CONFIG_PATH.exists():
        config.update(json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")))
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert rendered PNG frames to MP4.")
    parser.add_argument("--config", type=Path, help="Path to a simulation JSON config.")
    return parser.parse_args()


def make_video(config: dict) -> Path:
    ffmpeg_path = ensure_ffmpeg()
    ensure_frames_exist()
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    output_video = VIDEOS_DIR / f"{config['output_name']}.mp4"

    command = [
        ffmpeg_path,
        "-y",
        "-framerate",
        str(config["fps"]),
        "-i",
        str(INPUT_PATTERN),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        f"scale={config['video_width']}:{config['video_height']}:flags=lanczos",
        "-movflags",
        "+faststart",
        str(output_video),
    ]

    subprocess.run(command, check=True)
    return output_video


def main() -> int:
    args = parse_args()
    config = load_video_config(args.config)
    try:
        output_path = make_video(config)
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Video generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Video saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
