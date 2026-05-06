from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import make_video
import simulate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_config_path(path: Path) -> Path:
    config_path = path if path.is_absolute() else PROJECT_ROOT / path
    if not config_path.exists():
        raise FileNotFoundError(f"Config file was not found: {config_path}")
    return config_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate frames, MP4, and YouTube metadata from one config.")
    parser.add_argument("--config", type=Path, required=True, help="Path to a simulation JSON config.")
    parser.add_argument("--window", action="store_true", help="Show a scaled preview window while generating frames.")
    return parser.parse_args()


def generate(config_path: Path, show_window: bool) -> tuple[Path, Path]:
    simulation_config = simulate.load_config(config_path)
    simulate.update_layout(simulation_config.video_width, simulation_config.video_height)

    print("[1/3] Generating frames...")
    simulate.run(
        frame_count=simulation_config.frame_count,
        show_window=show_window,
        ball_count=simulation_config.initial_ball_count,
        boss_max_hp=simulation_config.boss_hp,
        damage=simulation_config.base_damage,
        seed=simulation_config.random_seed,
        fps=simulation_config.fps,
        item_spawn_interval=simulation_config.item_spawn_interval,
        output_name=simulation_config.output_name,
    )

    print("[2/3] Encoding MP4...")
    video_config, resolved_video_config_path = make_video.load_video_config(config_path)
    video_path = make_video.make_video(video_config)

    print("[3/3] Writing YouTube metadata...")
    metadata_path = make_video.write_youtube_metadata(video_config, resolved_video_config_path, video_path)
    return video_path, metadata_path


def main() -> int:
    args = parse_args()

    try:
        config_path = resolve_config_path(args.config)
        video_path, metadata_path = generate(config_path, args.window)
    except FileNotFoundError as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Generation failed while running FFmpeg: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Generation failed because the config is invalid: {exc}", file=sys.stderr)
        return 1

    print("Generation complete.")
    print(f"Video file: {video_path}")
    print(f"Metadata file: {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
