# YouTube Shorts 2D Simulation MVP

This project generates a vertical 2D physics simulation for YouTube Shorts. Multiple balls bounce in a 1080x1920 arena, collect upgrade items, and attack an HP boss.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## JSON Config

The default config is `configs/boss_battle_001.json`.

```json
{
  "video_width": 1080,
  "video_height": 1920,
  "fps": 60,
  "duration_seconds": 10,
  "initial_ball_count": 10,
  "boss_hp": 10000,
  "base_damage": 10,
  "item_spawn_interval": 75,
  "random_seed": 1,
  "output_name": "simulation_001"
}
```

Edit this JSON to change the ball count, boss HP, base damage, item interval, random seed, and output video name. Using the same `random_seed` makes results more reproducible.

## Generate Frames

```powershell
python src/simulate.py --config configs/boss_battle_001.json --no-window
```

PNG frames are written to `output/frames/` as `frame_000001.png`, `frame_000002.png`, and so on. Existing PNG frames are deleted before each run.

CLI options can override selected config values:

```powershell
python src/simulate.py --config configs/boss_battle_001.json --no-window --balls 20 --boss-hp 20000
```

## Preview Window

```powershell
python src/simulate.py --config configs/boss_battle_001.json --window
```

The preview window is scaled down to fit on screen. Saved PNG frames keep the configured resolution.

## Generate Everything

Use this command to run the full local pipeline from one config:

```powershell
python src/generate_video.py --config configs/boss_battle_001.json
```

It runs these steps in order:

1. Generate PNG frames
2. Encode the MP4 with FFmpeg
3. Save the matching YouTube metadata JSON

On success, it prints the generated video path and metadata path. If any step fails, it prints which part failed.

To preview while frames are generated:

```powershell
python src/generate_video.py --config configs/boss_battle_001.json --window
```

## Result Screen

The generated frame sequence ends with a 3-second result screen.

It shows:

- `CLEAR` or `FAILED`
- Clear time for `CLEAR`
- Remaining HP for `FAILED`
- Total damage
- The top damage ball ID, max hit damage, hit count, and total damage dealt

If the boss is defeated early, the simulation writes 3 seconds of result frames and then exits. If the boss survives, the final 3 seconds of the configured duration are reserved for the result screen.

## Generate MP4

FFmpeg is required. Make sure `ffmpeg` is available from PATH.

```powershell
ffmpeg -version
```

After generating frames:

```powershell
python src/make_video.py --config configs/boss_battle_001.json
```

Input:

```text
output/frames/frame_%06d.png
```

Output:

```text
output/videos/<output_name>.mp4
```

The MP4 uses the configured FPS and resolution, H.264, `yuv420p`, and faststart.

## YouTube Metadata

`make_video.py` also writes a matching YouTube metadata JSON file.

```text
output/metadata/<output_name>.json
```

For the default config, the file is:

```text
output/metadata/simulation_001.json
```

The metadata includes:

- `title`
- `description`
- `tags`
- `video_file`
- `config_file`
- `result`
- `duration_seconds`
- `boss_hp`
- `initial_ball_count`

The title is generated in English for Shorts, the description includes `#shorts`, and `tags` is a JSON array. This metadata is only saved locally; YouTube upload is not implemented.

## YouTube Upload

`src/upload_youtube.py` reads a generated metadata JSON file and can upload the matching MP4 with the YouTube Data API. The default privacy status is always `private`.

Dry-run preview:

```powershell
python src/upload_youtube.py --metadata output/metadata/simulation_001.json --dry-run
```

List available metadata files:

```powershell
python src/upload_youtube.py --list
```

OAuth setup:

1. Create a Google Cloud project.
2. Enable the YouTube Data API v3.
3. Configure the OAuth consent screen.
4. Create OAuth client credentials for a desktop app.
5. Download the credentials JSON.
6. Save it as `client_secrets.json` at the project root.

Do not commit credentials. `.gitignore` excludes:

- `client_secrets.json`
- `client_secret*.json`
- `token.json`
- `credentials.json`
- `oauth_token.json`
- `output/`

First private upload:

```powershell
python src/upload_youtube.py --metadata output/metadata/simulation_001.json --privacy private
```

On the first upload, a browser-based OAuth flow opens. After authorization, `token.json` is saved locally and reused for later uploads.

To upload as `unlisted` or `public`, you must explicitly choose it:

```powershell
python src/upload_youtube.py --metadata output/metadata/simulation_001.json --privacy unlisted
```

The script sends `title`, `description`, and `tags` from the metadata JSON to YouTube.

## Current Scope

- Physics: pymunk
- Rendering: pygame-ce
- Gravity: none
- Boss HP and HP bar
- Multiple balls
- Items: `damage_up`, `speed_up`
- Result screen
- Frame output: `output/frames/`
- Video output: `output/videos/<output_name>.mp4`
- YouTube upload: OAuth private upload supported
