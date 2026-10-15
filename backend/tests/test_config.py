import pytest

from app.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "DocSage"
    assert "postgresql" in str(settings.database_url)
    assert settings.storage_path == "./data/storage"


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "DocSage Test")
    monkeypatch.setenv("STORAGE_PATH", "/tmp/docsage")
    settings = Settings()
    assert settings.app_name == "DocSage Test"
    assert settings.storage_path == "/tmp/docsage"
