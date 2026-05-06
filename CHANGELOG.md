# CHANGELOG

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
