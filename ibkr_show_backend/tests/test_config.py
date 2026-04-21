import pytest

from app.core.config import get_settings


def test_prod_requires_explicit_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("AUTH_USERNAME", raising=False)
    monkeypatch.delenv("AUTH_PASSWORD", raising=False)
    monkeypatch.delenv("AUTH_SESSION_SECRET", raising=False)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="AUTH_USERNAME must be set explicitly"):
        get_settings()

    get_settings.cache_clear()


def test_prod_rejects_public_placeholder_auth_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "change-me")
    monkeypatch.setenv("AUTH_SESSION_SECRET", "change-me-session-secret")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="AUTH_PASSWORD cannot use the public placeholder value"):
        get_settings()

    get_settings.cache_clear()
