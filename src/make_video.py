from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"
INPUT_PATTERN = FRAMES_DIR / "frame_%06d.png"
OUTPUT_VIDEO = VIDEOS_DIR / "simulation_001.mp4"
FPS = 60


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


def make_video() -> Path:
    ffmpeg_path = ensure_ffmpeg()
    ensure_frames_exist()
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    command = [
        ffmpeg_path,
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(INPUT_PATTERN),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "scale=1080:1920:flags=lanczos",
        "-movflags",
        "+faststart",
        str(OUTPUT_VIDEO),
    ]

    subprocess.run(command, check=True)
    return OUTPUT_VIDEO


def main() -> int:
    try:
        output_path = make_video()
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Video generation failed: {exc}", file=sys.stderr)
        return 1

    print(f"Video saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
