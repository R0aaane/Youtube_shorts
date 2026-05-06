from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_DIR = PROJECT_ROOT / "output" / "frames"
VIDEOS_DIR = PROJECT_ROOT / "output" / "videos"


def main() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    print("Video encoding is not implemented yet.")
    print(f"Frames directory: {FRAMES_DIR}")
    print(f"Videos directory: {VIDEOS_DIR}")


if __name__ == "__main__":
    main()
