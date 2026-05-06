from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "default.json"
GENERATED_DIR = PROJECT_ROOT / "configs" / "generated"


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


BASE_BOSS_BATTLE_CONFIG = {
    "video_width": 1080,
    "video_height": 1920,
    "fps": 60,
    "duration_seconds": 10,
    "initial_ball_count": 10,
    "boss_hp": 10000,
    "base_damage": 10,
    "item_spawn_interval": 75,
    "random_seed": 1,
    "output_name": "boss_battle_001",
}


def ensure_default_config(path: Path = CONFIG_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
    return path


def load_config(path: Path = CONFIG_PATH) -> dict:
    ensure_default_config(path)
    return json.loads(path.read_text(encoding="utf-8"))


def build_boss_battle_config(index: int, rng: random.Random, output_prefix: str) -> dict:
    config = BASE_BOSS_BATTLE_CONFIG.copy()
    boss_hp_options = [5000, 10000, 20000, 50000, 100000, 250000, 500000, 1000000]
    ball_count_options = [10, 20, 30, 50, 75, 100]
    item_interval_options = [45, 60, 75, 90, 120]

    config.update(
        {
            "initial_ball_count": rng.choice(ball_count_options),
            "boss_hp": rng.choice(boss_hp_options),
            "base_damage": rng.choice([10, 15, 20, 30, 40, 50]),
            "item_spawn_interval": rng.choice(item_interval_options),
            "random_seed": rng.randint(1, 999999),
            "output_name": f"{output_prefix}_{index:03d}",
        }
    )
    return config


def generate_configs(count: int, theme: str, seed: int, output_dir: Path = GENERATED_DIR) -> list[Path]:
    if count < 1:
        raise ValueError("--count must be 1 or greater.")
    if theme != "boss_battle":
        raise ValueError("Only --theme boss_battle is supported for now.")

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    created_paths = []

    for index in range(1, count + 1):
        config = build_boss_battle_config(index, rng, output_prefix=theme)
        config_path = output_dir / f"{theme}_{index:03d}.json"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        created_paths.append(config_path)

    return created_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate multiple simulation config JSON files.")
    parser.add_argument("--count", type=int, help="Number of configs to generate.")
    parser.add_argument("--theme", default="boss_battle", help="Config theme. Currently supports boss_battle.")
    parser.add_argument("--seed", type=int, default=20260506, help="Seed for deterministic config generation.")
    parser.add_argument("--output-dir", type=Path, default=GENERATED_DIR, help="Directory for generated config files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.count is None:
        created_path = ensure_default_config()
        print(f"Config ready: {created_path}")
        return

    output_dir = args.output_dir if args.output_dir.is_absolute() else PROJECT_ROOT / args.output_dir
    created_paths = generate_configs(args.count, args.theme, args.seed, output_dir)
    print("Generated configs:")
    for path in created_paths:
        print(path)


if __name__ == "__main__":
    main()
