from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "default.json"


DEFAULT_CONFIG = {
    "video": {
        "width": 1080,
        "height": 1920,
        "fps": 60,
        "duration_seconds": 30,
    },
    "simulation": {
        "theme": "Evolving balls vs HP boss",
        "boss_hp": 100,
        "ball_count": 3,
        "ball_radius": 24,
        "ball_damage": 1,
        "gravity": [0, 900],
    },
    "metadata": {
        "title": "Evolving Balls vs HP Boss",
        "description": "A short 2D physics simulation for YouTube Shorts.",
        "tags": ["simulation", "physics", "shorts"],
    },
}


def ensure_default_config(path: Path = CONFIG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return path


def load_config(path: Path = CONFIG_PATH) -> dict:
    ensure_default_config(path)
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    created_path = ensure_default_config()
    print(f"Config ready: {created_path}")
