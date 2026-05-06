from src.generate_config import DEFAULT_CONFIG


def test_default_config_uses_shorts_resolution() -> None:
    assert DEFAULT_CONFIG["video"]["width"] == 1080
    assert DEFAULT_CONFIG["video"]["height"] == 1920
