from pathlib import Path

from src.settings import PROJECT_ROOT, load_settings


REQUIRED_DIRECTORIES = (
    "data/raw",
    "data/interim",
    "data/processed",
    "models",
    "rag/documents",
    "rag/metadata",
    "rag/index",
    "src/data",
    "src/features",
    "src/modeling",
    "src/finance",
    "src/recommendation",
    "src/rag",
    "app",
    "tests",
    "reports",
    "config",
)


def test_required_stage0_directories_exist() -> None:
    missing = [
        relative_path
        for relative_path in REQUIRED_DIRECTORIES
        if not (PROJECT_ROOT / relative_path).is_dir()
    ]

    assert missing == []


def test_configured_paths_stay_inside_project() -> None:
    settings = load_settings()
    project_root = PROJECT_ROOT.resolve()

    for configured_path in settings["paths"].values():
        resolved_path = (PROJECT_ROOT / configured_path).resolve()
        assert resolved_path == project_root or project_root in resolved_path.parents


def test_secret_configuration_contains_env_names_not_values() -> None:
    secrets = load_settings()["secrets"]

    assert all(key.endswith("_env") for key in secrets)
    assert all(str(value).endswith("_API_KEY") for value in secrets.values())


def test_environment_example_has_no_secret_values() -> None:
    env_example = Path(PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    for line in env_example.splitlines():
        if line and not line.startswith("#"):
            name, value = line.split("=", maxsplit=1)
            if name.endswith(("_KEY", "_TOKEN", "_SECRET", "_PASSWORD")):
                assert value == ""
