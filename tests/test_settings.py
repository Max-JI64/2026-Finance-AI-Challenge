from math import isclose

from src.settings import load_settings


def test_required_settings_and_seed() -> None:
    settings = load_settings()

    assert settings["project"]["random_seed"] == 42
    assert settings["prediction"]["target_unit"] == "commercial_area_and_business_type"
    assert settings["secrets"]["openai_api_key_env"] == "OPENAI_API_KEY"


def test_recommendation_weights_sum_to_one() -> None:
    weights = load_settings()["recommendation"]["weights"]

    assert isclose(sum(weights.values()), 1.0)

