# CHANGELOG

## 0.21.1 - 2026-05-08

### Changed

- Replaced the Ice Cream cone sprite with a more circular cup-style ice cream sprite so it fits the duel collision body better.

### Fixed

- Added a dedicated Food Duel tie result for simultaneous 0 HP endings, showing `UNBELIEVABLE TIE!`, `NO WINNER`, and `DRAW` instead of assigning a winner.
- Updated Food Duel metadata titles to describe tied duel results without naming a winner.

## 0.21.0 - 2026-05-08

### Added

- Added ICE CREAM as a Food Duel character with a generated realistic cone sprite.
- Added Ice Cream skills: `FREEZE SHOT`, `COLD DASH`, and `SWEET HEAL`.
- Added Ice Cream to the launcher matchup selector and default Food Duel config.

### Fixed

- Fixed Burger ingredient allies targeting the left-side character unconditionally, which could make Burger hit itself when Burger was on the left.
- Fixed Food Duel metadata titles so underscore food ids such as `ice_cream` render as readable names.

## 0.20.4 - 2026-05-08

### Changed

- Added minimum and maximum visible speed clamps for food duel characters so slows, bounces, and reload timing do not make late-fight movement stall.
- Kept the default food duel pacing within the Shorts-friendly 20-30 second range after the movement tempo adjustment.

## 0.20.3 - 2026-05-08

### Changed

- Added a light center-bias movement correction so Sushi spends less time fighting at the arena edge without changing the wooden-board layout.
- Raised skill/status labels, changed the reload callout to `RELOAD`, and enlarged endgame alerts and 50+ damage critical callouts.
- Strengthened cheese string trails, wasabi lingering particles, soy splash droplets, and Fresh Heal rings/sparkles.
- Updated the result screen flow so `FINAL HIT!` appears before the winner headline.
- Tuned the default food duel cheese damage so the generated duel stays near the existing 29-second pacing.

## 0.20.2 - 2026-05-08

### Changed

- Changed generated YouTube descriptions to use only the required Shorts hashtag line: `#shorts #FoodBattle #PhysicsSimulation #BattleSimulation #satisfying`.
- Normalized descriptions during YouTube upload so older metadata files do not publish winner, HP, damage, or elapsed-time summaries.
- Updated upload documentation for the required Shorts description policy.

## 0.20.1 - 2026-05-08

### Added

- Added food duel endgame callouts for `DANGER!`, `ONE HIT LEFT!`, and `FINAL HIT!`.

### Changed

- Shortened the default food duel pacing by increasing base damage, cheese damage, movement speed, charge speed, and skill frequency.
- Shortened the food duel result hold so the generated Shorts output stays closer to the 20-30 second target.
- Strengthened large-hit impact flashes, shockwaves, and light screen shake without changing the Sushi or cheese skill flow.
- Improved skill label readability with a thicker black outline and pop-fade scaling.
- Updated the duel result headline to show winner text with an exclamation mark.

## 0.20.0 - 2026-05-08

### Added

- Added a Food Duel config editor to the Tkinter launcher for matchup, HP, radius, speed, damage, seed, and audio settings.
- Added a generated transparent food skill effect sprite sheet for cheese, wasabi, soy, and fresh heal visuals.

### Changed

- Updated food duel skill rendering to layer generated realistic food/liquid effect sprites with the existing code-drawn trails, rings, and particles.
- Cleaned up launcher command labels and documented the config editor.

## 0.19.1 - 2026-05-08

### Changed

- Replaced the Sushi duel sprite with a larger photoreal salmon nigiri cutout and tightened sprite trimming so Sushi reads more clearly on Shorts.
- Improved Sushi skill visuals with distinct wasabi blobs/trails/status particles, soy droplets/slow rings, roll dash speed lines, and fresh heal rings/bubbles/callouts.
- Improved Pizza Cheese Shot visuals so projectiles and impacts look more like melted cheese instead of simple yellow balls.
- Differentiated Sushi and cheese skill sound cues with wetter food-style splats, liquid splashes, roll acceleration, and fresh heal pops.
- Updated food duel documentation for the enhanced Sushi and cheese skill presentation.

## 0.19.0 - 2026-05-08

### Added

- Added SUSHI as a technical food duel character with a transparent salmon nigiri sprite.
- Added Sushi skills: `WASABI SHOT`, `SOY SPLASH`, `ROLL DASH`, and `FRESH HEAL`.
- Added Sushi projectile/status audio cues and a default `PIZZA vs SUSHI` duel config.

### Changed

- Updated food duel metadata text and tags to use the configured duel foods.
- Updated tests and documentation for the Sushi duel character.

## 0.18.2 - 2026-05-08

### Changed

- Added a `Reloading...` label above food duel characters while Pizza cheese or Burger ingredients are reloading.
- Updated food duel documentation for the reload label.

## 0.18.1 - 2026-05-08

### Changed

- Enhanced food duel hit visuals with stronger shockwave rings, food-like particles, and brief large-hit flashes.
- Made strong damage popups larger and changed the top damage callout to `CRITICAL!`.
- Increased Pizza and Burger glow/shadow treatment and added animated skill label scaling/fading.
- Added subtle board depth, outer glow, and vignette-style center emphasis to the duel background.
- Updated food duel documentation for the revised visual polish.

## 0.18.0 - 2026-05-08

### Added

- Added a Tkinter launcher UI for preview, full generation, MP4 encoding, upload dry run, and private YouTube upload commands.

### Changed

- Changed food duel rendering so it continues until one side reaches 0 HP instead of ending at the configured 20-second limit.
- Changed food duel metadata duration to use the actual rendered frame count.
- Updated food duel documentation for the no-time-limit duel behavior and launcher UI.

## 0.17.3 - 2026-05-07

### Changed

- Changed the default food duel ball radius back to 70.
- Regenerated READY/FIGHT voice clips with an English voice.
- Changed regular collision and light-damage sounds so hit types are easier to distinguish.
- Updated the food duel config test for the smaller readable ball radius.

## 0.17.2 - 2026-05-07

### Added

- Added recorded READY/FIGHT voice WAV assets for the food duel intro.

### Changed

- Changed ball collision audio to use a wet food-bump sound.
- Changed normal duel collisions so shockwaves are only drawn for strong damage hits.
- Updated food duel documentation for the revised voice and impact behavior.

## 0.17.1 - 2026-05-07

### Changed

- Changed READY/FIGHT audio to use more voice-like synthesized callouts.
- Changed cheese stick, Burger charge hit, and ingredient hit sounds to wetter food-impact effects.
- Updated food duel documentation for the revised synthesized audio cues.

## 0.17.0 - 2026-05-07

### Added

- Added generated Pizza sprite variants with progressively depleted cheese.
- Added Burger and Pizza reload behavior that restores visual sprite states over about 3 seconds.

### Changed

- Changed Burger ingredient spawning so a fully emptied Burger reloads before spawning more ingredients.
- Changed Pizza cheese shots so the Pizza sprite loses cheese as shots are fired and reloads when empty.
- Updated food duel documentation for sprite reload behavior.

## 0.16.0 - 2026-05-07

### Added

- Added generated Burger sprite variants for missing lettuce, cheese, tomato, and patty states.

### Changed

- Changed Burger ingredient loss from dynamic drawn marks to generated burger image swaps when ingredients are summoned.
- Updated food duel documentation for generated Burger state sprites.

## 0.15.2 - 2026-05-07

### Changed

- Changed food sprite loading to prefer alpha-preserving surfaces when the display backend allows it.
- Replaced Burger's dark missing-ingredient marks with food-colored missing-filling marks.
- Changed the food duel battle area from a black grid to a wooden tray-style board with subtle cutting-board lines.
- Updated food duel documentation for the wooden tray arena and Burger missing-filling visuals.

## 0.15.1 - 2026-05-07

### Changed

- Changed sticky cheese patches to render as melted cheese stuck on top of the target food sprite.
- Replaced Burger's overlaid missing-filling bars with sprite-level missing ingredient marks based on summoned ingredient type.
- Updated food duel documentation for visible cheese attachment and Burger ingredient loss visuals.

## 0.15.0 - 2026-05-07

### Added

- Added damage-scaled food duel popups with longer/larger strong hits and `BIG HIT!` callouts for 50+ damage.
- Added stronger shockwave and screen shake treatment for high-damage food duel hits.

### Changed

- Reworked synthesized food duel sound effects toward softer thumps, squish impacts, cheese splats, melt sizzles, ingredient crunches, and a short victory ding.
- Updated food duel documentation for the food-themed audio and damage popup behavior.

## 0.14.1 - 2026-05-07

### Changed

- Enlarged and lowered the food duel arena to reduce empty space below the board.
- Tightened the top food duel HUD spacing so the vertical Shorts layout feels more balanced.
- Shortened the brown board background panel so it no longer stretches deep into unused lower space.

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
