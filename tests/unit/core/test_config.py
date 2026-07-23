"""Unit tests for Settings secrets validator."""

import pytest


def test_settings_production_rejects_empty_secret(monkeypatch):
    """Settings with environment=production fails when SECRET_KEY missing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "")
    monkeypatch.setenv("MAIL_PASSWORD", "")

    with pytest.raises(ValueError) as exc:
        from src.core.config import Settings

        Settings()
    assert "SECRET_KEY" in str(exc.value)


def test_settings_production_rejects_empty_mail_password(monkeypatch):
    """Settings with environment=production fails when MAIL_PASSWORD missing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "valid-secret")
    monkeypatch.setenv("MAIL_PASSWORD", "")

    with pytest.raises(ValueError) as exc:
        from src.core.config import Settings

        Settings()
    assert "MAIL_PASSWORD" in str(exc.value)


def test_settings_production_passes_when_secrets_set(monkeypatch):
    """Settings loads successfully when both secrets are set in production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "some-secret-value")
    monkeypatch.setenv("MAIL_PASSWORD", "some-mail-pwd")

    from src.core.config import Settings

    s = Settings()
    assert s.secret_key == "some-secret-value"


def test_settings_development_allows_empty_secrets(monkeypatch):
    """In non-production env the validator allows empty secrets."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SECRET_KEY", "")
    monkeypatch.setenv("MAIL_PASSWORD", "")

    from src.core.config import Settings

    s = Settings()
    assert s.secret_key == ""
