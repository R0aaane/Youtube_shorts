# CHANGELOG

## 0.14.0 - 2026-05-07

### Changed

- Replaced the food duel photo background with a simpler brown cutting-board style background.
- Simplified arena framing and reduced grid line contrast so the battle area is the visual focus.
- Toned down food duel UI colors for a smaller, more consistent palette.
- Added subtle glow and shadow treatment to food sprites and ingredient allies for better separation from the background.
- Updated food duel documentation for the simplified Shorts visual style.

## 0.13.0 - 2026-05-07

### Changed

- Changed the food duel arena to a square layout and moved it higher on the screen.
- Moved Pizza and Burger HP bars to the top of the video with larger text and segmented bars.
- Changed Burger Charge trail, label, and charge impact effects from blue to Burger red.
- Removed the old lower HP HUD so Shorts UI is less likely to cover battle information.

## 0.12.0 - 2026-05-07

### Added

- Added HP to Burger ingredient allies; separated ingredients now deal their remaining HP as damage when they hit the enemy.
- Added a winner focus result screen that zooms in on the winning food and highlights the winning side.

### Changed

- Unified food duel damage colors so Pizza damage is yellow and Burger/ingredient damage is red.
- Changed the food duel arena to a shorter, wider battle area closer to the reference composition.
- Updated the result screen to show the loser's actual remaining HP when the duel ends by time limit.

## 0.11.0 - 2026-05-07

### Changed

- Limited food duel hit-stop to Burger Charge hits only so repeated damage ticks no longer freeze the action.
- Changed Burger ingredient allies to bounce around the arena instead of tracking the enemy.
- Changed Burger rendering so its inner filling visually disappears as HP is spent.
- Retuned default food duel HP values to keep the less-stopped battle near 20 seconds.
- Updated food duel documentation for the revised Burger Charge and ingredient ally behavior.

## 0.10.0 - 2026-05-07

### Added

- Added duel HP bars to make the battle state easier to read on smartphones.

### Changed

- Increased the default Pizza vs Burger character size for Shorts visibility.
- Narrowed the food duel arena and adjusted starting positions and velocities so early collisions happen near the center.
- Shortened the food duel READY/FIGHT intro so skills and damage appear in the opening second.
- Darkened the duel arena overlay for stronger contrast against food sprites and effects.
- Updated food duel documentation for the Shorts retention tuning.

## 0.9.0 - 2026-05-06

### Added

- Added a generated kitchen battle background for the food duel.
- Added realistic generated ingredient sprites for lettuce, cheese, tomato, and burger patty allies.

### Changed

- Changed Burger Charge to launch one larger ingredient ally per charge.
- Updated food duel typography to use a more modern system font preference.
- Changed food duel frame export to JPEG so photo backgrounds render in a practical amount of time.
- Updated food duel documentation for the kitchen background and revised ingredient ally behavior.

## 0.8.0 - 2026-05-06

### Added

- Added sticky cheese projectiles for Pizza that attach to the enemy and deal periodic melt damage.
- Added Burger Charge HP cost that spawns lettuce, cheese, tomato, and meat ally units.
- Added synthesized audio cues for cheese shots, cheese ticks, ingredient spawns, and ingredient hits.

### Changed

- Replaced Pizza's old FIRE/BURN damage-over-time behavior with the sticky cheese attack.
- Updated food duel documentation for the new Pizza and Burger skill mechanics.

## 0.7.0 - 2026-05-06

### Added

- Added realistic generated pizza and burger sprites for the food duel.
- Added hit-stop and screen shake on duel hits.
- Added stronger shockwave effects for duel impacts.
- Allowed project-owned food sprite PNG assets to be tracked.

### Changed

- Changed food duel rendering so the food image is the visible object while the circular hitbox stays internal.
- Updated food duel documentation for the new impact and sprite presentation.

## 0.6.0 - 2026-05-06

### Added

- Added duel speed tuning options for normal movement and charge movement.

### Changed

- Tuned the default food duel config for a slower, easier-to-follow 20-second video.
- Updated food duel documentation to explain the timing and speed controls.

## 0.5.0 - 2026-05-06

### Added

- Added synthesized audio generation for duel videos, including READY/FIGHT callouts, hit sounds, burn ticks, and charge impacts.
- Added MP4 audio muxing and local WAV output under `output/audio/`.
- Added audio file references to generated YouTube metadata.

## 0.4.1 - 2026-05-06

### Changed

- Improved food duel skill readability with visible Burn flames, damage-over-time ticks, Charge trails, and impact shockwaves.
- Documented the visible food duel skill effects in the README.

## 0.4.0 - 2026-05-06

### Added

- Added a `food_duel` simulation mode where two large food balls fight each other with unique skills.
- Added `configs/food_duel.json` for a Pizza Burn vs Burger Charge Shorts-style battle.
- Added duel-specific YouTube metadata and README usage documentation.

## 0.3.0 - 2026-05-06

### Added

- Added a food-themed `food_boss` simulation with pizza, burger, sushi, taco, donut, and fries ball visuals.
- Added `configs/food_boss.json` for generating a food-focused Shorts-style HP boss battle.
- Added food-themed YouTube metadata titles, descriptions, and tags.

### Changed

- Documented the food battle generation command in the README.

## 0.2.0 - 2026-05-06

### Added

- Added a Fibonacci vs Exponential number battle simulation mode inspired by the provided Shorts reference.
- Added `configs/fibonacci_vs_exponential.json` for generating a 100-ball vertical math battle video.

### Changed

- Updated video metadata generation to recognize the Fibonacci vs Exponential theme.
- Documented the new reference-style generation command.

## 0.1.0 - 2026-05-06

### Added

- Initial project structure.
