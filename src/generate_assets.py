from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"


def generate_boss_asset() -> Path | None:
    api_url = os.getenv("IMAGEGEN2_API_URL")
    api_key = os.getenv("IMAGEGEN2_API_KEY")
    if not api_url or not api_key:
        print("IMAGEGEN2_API_URL or IMAGEGEN2_API_KEY is not set. Skipping asset generation.")
        return None

    payload = {
        "prompt": "original simple red crystal boss sprite, transparent background, no text, no logo",
        "size": "1024x1024",
        "response_format": "b64_json",
    }
    request = Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Asset generation failed: {exc}")
        return None

    image_data = body.get("data", [{}])[0].get("b64_json")
    if not image_data:
        print("Asset generation response did not include data[0].b64_json.")
        return None

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ASSETS_DIR / "boss.png"
    output_path.write_bytes(base64.b64decode(image_data))
    print(f"Asset saved: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_boss_asset()
