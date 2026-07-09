import pytest

from app.core.config import load_settings


def test_load_settings_missing_required_vars_raises_clear_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        load_settings(_env_file=None)

    assert ".env.example" in str(exc_info.value)


def test_load_settings_succeeds_with_required_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")

    settings = load_settings()

    assert settings.DATABASE_URL == "postgresql+asyncpg://u:p@localhost:5432/db"
    assert settings.JWT_SECRET == "test-secret"
