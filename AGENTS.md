# AGENTS.md

## Project Goal

This project generates short vertical simulation videos for YouTube Shorts.

The app should:
1. Run a 2D physics simulation.
2. Render the simulation frame by frame.
3. Export the result as an MP4 video.
4. Save metadata such as title, description, tags, and config.
5. Later support optional YouTube upload automation.

## Tech Stack

Use Python unless there is a strong reason not to.

Preferred libraries:
- pymunk for 2D physics
- pygame-ce or pygame for rendering
- ffmpeg for video encoding
- JSON files for simulation configs
- pytest for tests where practical

## Target Output

Default video format:
- Resolution: 1080x1920
- Aspect ratio: 9:16
- FPS: 60
- Duration: 30 to 60 seconds for the first MVP
- Output format: mp4

## Development Rules

- Keep changes small and incremental.
- Do not build the entire final system at once.
- Prefer simple, working MVPs over complex architecture.
- After each meaningful change, run the minimum necessary verification command.
- If a dependency is needed, update requirements.txt or pyproject.toml.
- Do not hardcode machine-specific absolute paths.
- Do not add YouTube upload until local video generation is stable.
- Do not use copyrighted game assets, logos, music, or textures.

## Simulation Design

Initial simulation theme:
"Evolving balls vs HP boss"

Core rules:
- Balls bounce inside a vertical 1080x1920 arena.
- A boss or HP wall exists in the scene.
- When balls hit the boss, boss HP decreases.
- Items may spawn and upgrade balls.
- The simulation ends when boss HP reaches 0 or time limit is reached.
- A result screen should be rendered at the end.

Possible upgrades:
- damage up
- speed up
- split ball
- critical hit
- explosion damage
- poison damage
- laser attack

## Folder Structure

Aim for this structure:

simulation_youtube/
  configs/
  assets/
  output/
    frames/
    videos/
    thumbnails/
    metadata/
  src/
    simulate.py
    render.py
    make_video.py
    upload_youtube.py
    generate_config.py
  tests/
  requirements.txt
  README.md

## Definition of Done

For each task:
- The code runs without obvious errors.
- A clear command is documented.
- Generated output is saved under output/.
- The implementation is simple enough to extend in the next step.