from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import generate_video


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "configs" / "generated"
BATCH_RESULT_PATH = PROJECT_ROOT / "output" / "metadata" / "batch_result.json"


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def collect_configs(config_dir: Path) -> list[Path]:
    resolved_dir = resolve_path(config_dir)
    if not resolved_dir.exists():
        raise FileNotFoundError(f"Config directory was not found: {resolved_dir}")
    configs = sorted(resolved_dir.glob("*.json"))
    if not configs:
        raise FileNotFoundError(f"No JSON config files found under: {resolved_dir}")
    return configs


def result_entry(config_path: Path, status: str, **kwargs: Any) -> dict[str, Any]:
    entry = {
        "config_file": str(config_path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "status": status,
    }
    entry.update(kwargs)
    return entry


def write_batch_result(results: list[dict[str, Any]], stopped_early: bool) -> Path:
    BATCH_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "succeeded": sum(1 for result in results if result["status"] == "SUCCESS"),
        "failed": sum(1 for result in results if result["status"] == "FAILED"),
        "stopped_early": stopped_early,
        "results": results,
    }
    BATCH_RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return BATCH_RESULT_PATH


def print_summary(results: list[dict[str, Any]], batch_result_path: Path) -> None:
    print("")
    print("Batch summary:")
    for result in results:
        if result["status"] == "SUCCESS":
            print(f"SUCCESS {result['config_file']} -> {result['video_file']}")
        else:
            print(f"FAILED  {result['config_file']} -> {result['error']}")

    succeeded = sum(1 for result in results if result["status"] == "SUCCESS")
    failed = sum(1 for result in results if result["status"] == "FAILED")
    print(f"Total: {len(results)}  Success: {succeeded}  Failed: {failed}")
    print(f"Batch log: {batch_result_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate multiple videos from config JSON files.")
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR, help="Directory containing config JSON files.")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue processing after a config fails.")
    parser.add_argument("--window", action="store_true", help="Show a scaled preview window while generating frames.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[dict[str, Any]] = []
    stopped_early = False

    try:
        config_paths = collect_configs(args.config_dir)
    except FileNotFoundError as exc:
        print(f"Batch generation failed: {exc}", file=sys.stderr)
        return 1

    for index, config_path in enumerate(config_paths, start=1):
        print(f"[{index}/{len(config_paths)}] Processing {config_path}")
        try:
            video_path, metadata_path = generate_video.generate(config_path, args.window)
        except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError, ValueError) as exc:
            results.append(result_entry(config_path, "FAILED", error=str(exc)))
            if not args.continue_on_error:
                stopped_early = True
                break
            continue

        results.append(
            result_entry(
                config_path,
                "SUCCESS",
                video_file=str(video_path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/"),
                metadata_file=str(metadata_path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/"),
            )
        )

    batch_result_path = write_batch_result(results, stopped_early)
    print_summary(results, batch_result_path)
    return 1 if any(result["status"] == "FAILED" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
