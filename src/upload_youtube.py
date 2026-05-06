from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
DEFAULT_PRIVACY_STATUS = "private"
REQUIRED_METADATA_KEYS = {
    "title",
    "description",
    "tags",
    "video_file",
    "config_file",
    "result",
}


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_metadata(path: Path) -> dict[str, Any]:
    metadata_path = resolve_path(path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file was not found: {metadata_path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    missing_keys = sorted(REQUIRED_METADATA_KEYS - metadata.keys())
    if missing_keys:
        raise ValueError(f"Metadata file is missing required keys: {', '.join(missing_keys)}")
    if not isinstance(metadata["tags"], list):
        raise ValueError("Metadata key `tags` must be a JSON array.")
    return metadata


def list_metadata_files() -> list[Path]:
    if not METADATA_DIR.exists():
        return []
    return sorted(METADATA_DIR.glob("*.json"))


def print_upload_plan(metadata: dict[str, Any], metadata_path: Path, privacy_status: str) -> None:
    video_path = resolve_path(Path(metadata["video_file"]))
    print("DRY RUN: no upload will be performed.")
    print(f"Metadata file: {resolve_path(metadata_path)}")
    print(f"Video file: {video_path}")
    print(f"Privacy status: {privacy_status}")
    print("")
    print("Upload payload preview:")
    print(f"Title: {metadata['title']}")
    print(f"Description: {metadata['description']}")
    print(f"Tags: {', '.join(str(tag) for tag in metadata['tags'])}")
    print(f"Config file: {metadata.get('config_file')}")
    print(f"Result status: {metadata.get('result', {}).get('status', 'UNKNOWN')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a YouTube upload from generated metadata.")
    parser.add_argument("--metadata", type=Path, help="Path to output/metadata/*.json.")
    parser.add_argument("--list", action="store_true", help="List available metadata JSON files.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview upload content without uploading.")
    parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Reserved for future use. Actual upload is not implemented yet.",
    )
    parser.add_argument(
        "--privacy-status",
        choices=["private", "unlisted", "public"],
        default=DEFAULT_PRIVACY_STATUS,
        help="YouTube privacy status to use when upload is implemented.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list:
        metadata_files = list_metadata_files()
        if not metadata_files:
            print(f"No metadata JSON files found under: {METADATA_DIR}")
            return 0
        for metadata_file in metadata_files:
            print(metadata_file)
        return 0

    if args.metadata is None:
        print("Upload preview failed: --metadata is required unless --list is used.", file=sys.stderr)
        return 1

    try:
        metadata = load_metadata(args.metadata)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Upload preview failed: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print_upload_plan(metadata, args.metadata, args.privacy_status)
        return 0

    print(
        "Upload aborted: actual YouTube upload is not implemented yet. "
        "Run with --dry-run to preview the upload payload.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
