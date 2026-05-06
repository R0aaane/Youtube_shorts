from pathlib import Path

from src.generate_config import DEFAULT_CONFIG
from src.simulate import load_config


def test_default_config_uses_shorts_resolution() -> None:
    assert DEFAULT_CONFIG["video"]["width"] == 1080
    assert DEFAULT_CONFIG["video"]["height"] == 1920


def test_food_boss_config_uses_food_theme() -> None:
    config = load_config(Path("configs/food_boss.json"))

    assert config.theme == "food_boss"
    assert config.video_width == 1080
    assert config.video_height == 1920
    assert config.initial_ball_count >= 6
    assert config.food_types is not None
    assert "pizza" in config.food_types
    assert "burger" in config.food_types


def test_food_duel_config_uses_large_versus_balls() -> None:
    config = load_config(Path("configs/food_duel.json"))

    assert config.theme == "food_duel"
    assert config.initial_ball_count == 2
    assert config.duel_ball_radius >= 70
    assert config.duration_seconds >= 20
    assert config.duel_speed_scale < 1.0
    assert config.duel_burger_charge_hp_cost > 0
    assert config.duel_ingredient_damage > 0
    assert config.duel_cheese_damage > 0
    assert config.duel_left_food == "pizza"
    assert config.duel_right_food == "burger"


def test_food_duel_realistic_sprites_exist() -> None:
    assert Path("assets/food_sprites/pizza_magenta.png").exists()
    assert Path("assets/food_sprites/burger_magenta.png").exists()
