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

## Generate Multiple Configs

Use `generate_config.py` to create many simulation variants for batch production.

```powershell
python src/generate_config.py --count 10 --theme boss_battle
```

Generated files are saved under:

```text
configs/generated/
```

Each generated config varies:

- `boss_hp`
- `initial_ball_count`
- `item_spawn_interval`
- `random_seed`
- `base_damage`
- `output_name`

The `output_name` is unique, so generated videos and metadata files do not overwrite each other.

Generate a video from one generated config:

```powershell
python src/generate_video.py --config configs/generated/boss_battle_001.json
```

Batch-generate videos from all generated configs:

```powershell
python src/batch_generate.py --config-dir configs/generated
```

By default, the batch stops on the first failed config. To keep processing the remaining configs:

```powershell
python src/batch_generate.py --config-dir configs/generated --continue-on-error
```

At the end, the command prints a success/failure summary and writes a log to:

```text
output/metadata/batch_result.json
```

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

Reference-style number battle:

```powershell
python src/generate_video.py --config configs/fibonacci_vs_exponential.json
```

This creates a vertical "100 Fibonacci VS Exponential" simulation with 50 Fibonacci-number balls and 50 exponential-number balls attacking a shared HP wall.

Food-themed Shorts battle:

```powershell
python src/generate_video.py --config configs/food_boss.json
```

This creates a vertical food ball battle where pizza, burger, sushi, taco, donut, and fries balls bounce around and attack a hunger HP boss.

Food skill duel:

```powershell
python src/generate_video.py --config configs/food_duel.json
```

This creates a large-ball 1v1 battle where two food balls use their own skills instead of cooperating against a boss. The default matchup is Pizza Cheese vs Sushi Technique.
Pizza Cheese fires sticky cheese projectiles that attach and melt for periodic damage. Burger Charge shows a red dash trail, spends HP to launch one realistic ingredient ally per charge, and only the charge impact triggers hit-stop.
Ingredient allies bounce around the arena after separating instead of chasing the opponent. Each ingredient keeps the HP Burger spent to create it, and deals that remaining HP as red Burger-side damage when it hits Pizza. As Burger summons ingredients, its sprite switches to generated missing-ingredient burger variants such as no-lettuce, no-cheese, no-tomato, and no-patty states. Once all ingredients are spent, Burger reloads for about 3 seconds and the sprite refills in reverse order.
Damage colors are side-based for readability: Pizza attacks use yellow numbers and effects, while Burger and ingredient attacks use red. Burger Charge also uses red trails and impact rings. The result screen zooms the winning food into focus so the winner is clear at the end.
The food duel uses a square wooden tray-style battle area with subtle cutting-board lines and large segmented HP panels at the top of the frame so Shorts UI does not cover them.
The generated MP4 includes food-battle audio: English READY/FIGHT voice clips when available, wet food bumps for ball collisions, distinct light smacks for small damage, low charge impacts, wet cheese splats, Sushi wasabi/soy/roll/heal sounds, melt sizzles, ingredient squash sounds, and a short victory ding. The matching WAV is saved under `output/audio/`.
The default duel config uses `duration_seconds` only as an initial layout/progress estimate. The duel keeps going until one side reaches 0 HP. `duel_speed_scale` controls normal movement speed, and `duel_charge_speed` controls charge speed.
Food duel uses realistic generated food sprites from `assets/food_sprites/`, including Burger and Pizza state variants, with subtle glow and shadow so the characters stand out from the simplified arena. Collision remains circle-based internally, but the visible objects are the food sprites. Heavy hits trigger hit-stop, screen shake, and larger shockwave effects.
Damage text scales by damage amount: small ticks stay short and compact, medium hits use the standard popup, strong hits add larger text, and only strong hits show shockwaves. 50+ damage shows an extra `CRITICAL!` callout. Sticky cheese is drawn on top of the target food sprite as melted cheese so the ongoing Pizza effect is visible. Pizza loses visible cheese as it fires and reloads its cheese over about 3 seconds when empty.
Food duel visuals keep the simple wooden-board style, but add stronger character glow, subtle board depth, center emphasis, food-like hit particles, animated skill labels, and brief flashes on large impacts.
Pizza and Burger show a `RELOAD` label while their cheese or ingredients are being restored.
Food duel finish polish keeps Sushi from drifting too far to the edges, raises skill labels above the characters, shortens reload callouts to `RELOAD`, strengthens cheese strings, wasabi/soy/heal readability, and shows `FINAL HIT!` before the winner headline.
Food duel movement clamps Pizza and Sushi to a minimum visible speed so slows, bounces, and reload timing do not make the late battle look stalled.
The duel intro is shortened for Shorts retention: READY lasts under half a second, FIGHT starts quickly, and the default starting positions force the first skill and hit in the opening second. The main food sprites and HUD HP bars are sized for smartphone viewing.
Food duel no longer ends by the configured 20-second limit. It keeps rendering until one side reaches 0 HP, then writes the 3-second result screen.
SUSHI is available as a technical duel character. The default food duel config uses `PIZZA vs SUSHI`; Sushi has a larger photoreal salmon nigiri sprite and cycles through visually distinct `WASABI SHOT`, `SOY SPLASH`, `ROLL DASH`, and `FRESH HEAL` effects. Wasabi uses green blobs, trails, splash, and DOT particles; Soy uses translucent brown droplets and slow rings; Roll Dash uses fast spin, pale speed lines, and a larger impact ring; Fresh Heal uses aqua rings, bubbles, and a visible heal callout.
Food skill effects can use the generated alpha sprite sheet at `assets/skill_effects/food_skill_sheet_alpha.png` so cheese, wasabi, soy, and heal visuals have more realistic food/liquid texture while keeping the existing code-drawn trails and rings.

## Launcher UI

Run the local command launcher with:

```powershell
python src/launcher_ui.py
```

The launcher provides buttons for a windowed preview, full frame/audio/MP4/metadata generation, MP4 encoding from existing frames, YouTube upload dry run, and private YouTube upload. It also includes a small Food Duel config editor for changing the left/right foods, HP, radius, speed, damage, random seed, and audio toggle before running commands.

It runs these steps in order:

1. Generate image frames
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

The title is generated in English for Shorts, and `tags` is a JSON array. The generated YouTube description is kept short and always uses:

```text
#shorts #FoodBattle #PhysicsSimulation #BattleSimulation #satisfying
```

Winner names, HP values, damage totals, and elapsed time are kept out of the public description.

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

The script sends `title`, `description`, and `tags` to YouTube. During upload, the description is normalized to the required Shorts hashtag line above, even when an older metadata JSON contains a longer result summary.

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
