"""Unit tests for application configuration."""

import pytest

from app.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_environment(self):
        """Default environment should be development."""
        settings = Settings()
        assert settings.environment == "development"

    def test_default_debug_is_false(self):
        """Debug should be False by default."""
        settings = Settings()
        assert settings.debug is False

    def test_is_production_false_in_development(self):
        """is_production should be False in development."""
        settings = Settings(environment="development")
        assert settings.is_production is False

    def test_is_production_true_in_production(self):
        """is_production should be True in production."""
        settings = Settings(environment="production")
        assert settings.is_production is True

    def test_default_session_expire_seconds(self):
        """Default session expire should be 24 hours."""
        settings = Settings()
        assert settings.session_expire_seconds == 86400

    def test_remember_me_session_expire_seconds(self):
        """Remember me session expire should be 30 days."""
        settings = Settings()
        assert settings.session_expire_remember_seconds == 2592000


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings_instance(self):
        """get_settings should return Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        """get_settings should return cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
