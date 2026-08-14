"""Central settings loader with structural validation."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"


@lru_cache(maxsize=1)
def load_settings(path: Path = DEFAULT_SETTINGS_PATH) -> dict[str, Any]:
    """Load YAML settings and fail clearly when required sections are absent."""

    with path.open("r", encoding="utf-8") as stream:
        settings = yaml.safe_load(stream)

    if not isinstance(settings, dict):
        raise ValueError(f"Settings must be a mapping: {path}")

    required_sections = {
        "project",
        "app",
        "paths",
        "prediction",
        "finance",
        "recommendation",
        "secrets",
    }
    missing = sorted(required_sections.difference(settings))
    if missing:
        raise ValueError(f"Missing required settings sections: {', '.join(missing)}")

    return settings
