from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any


warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core._python_version_support")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = PROJECT_ROOT / "output" / "metadata"
CLIENT_SECRETS_PATH = PROJECT_ROOT / "client_secrets.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"
DEFAULT_PRIVACY_STATUS = "private"
YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]
SHORTS_DESCRIPTION = "#shorts #FoodBattle #PhysicsSimulation #BattleSimulation #satisfying"
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
    metadata["description"] = SHORTS_DESCRIPTION
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


def ensure_video_file(metadata: dict[str, Any]) -> Path:
    video_path = resolve_path(Path(metadata["video_file"]))
    if not video_path.exists():
        raise FileNotFoundError(f"Video file was not found: {video_path}")
    return video_path


def get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    credentials = None
    if TOKEN_PATH.exists():
        credentials = Credentials.from_authorized_user_file(str(TOKEN_PATH), YOUTUBE_UPLOAD_SCOPE)

    if credentials and credentials.valid:
        return credentials

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    else:
        if not CLIENT_SECRETS_PATH.exists():
            raise FileNotFoundError(
                f"OAuth client secrets were not found: {CLIENT_SECRETS_PATH}\n"
                "Download OAuth credentials from Google Cloud and save them as client_secrets.json "
                "at the project root. This file must not be committed."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_PATH), YOUTUBE_UPLOAD_SCOPE)
        credentials = flow.run_local_server(port=0)

    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def build_upload_body(metadata: dict[str, Any], privacy_status: str) -> dict[str, Any]:
    return {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": "24",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }


def upload_video(metadata: dict[str, Any], privacy_status: str) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    video_path = ensure_video_file(metadata)
    credentials = get_credentials()
    youtube = build("youtube", "v3", credentials=credentials)
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")

    request = youtube.videos().insert(
        part="snippet,status",
        body=build_upload_body(metadata, privacy_status),
        media_body=media,
    )
    response = request.execute()
    video_id = response.get("id")
    if not video_id:
        raise RuntimeError(f"YouTube upload completed but no video id was returned: {response}")
    return video_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload a generated video to YouTube from metadata.")
    parser.add_argument("--metadata", type=Path, help="Path to output/metadata/*.json.")
    parser.add_argument("--list", action="store_true", help="List available metadata JSON files.")
    parser.add_argument("--dry-run", action="store_true", help="Preview upload content without uploading.")
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default=DEFAULT_PRIVACY_STATUS,
        help="YouTube privacy status. Defaults to private.",
    )
    parser.add_argument("--privacy-status", dest="privacy", choices=["private", "unlisted", "public"], help=argparse.SUPPRESS)
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
        print_upload_plan(metadata, args.metadata, args.privacy)
        return 0

    try:
        video_id = upload_video(metadata, args.privacy)
    except FileNotFoundError as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        if exc.__class__.__name__ == "HttpError":
            print(f"Upload failed with a YouTube API error: {exc}", file=sys.stderr)
            return 1
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1

    print("Upload complete.")
    print(f"Video ID: {video_id}")
    print(f"Privacy status: {args.privacy}")
    print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
