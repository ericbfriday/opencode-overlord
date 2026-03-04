"""Tests for OrchestratorConfig."""

import pytest
from pydantic import ValidationError

from overlord.config import OrchestratorConfig


def test_load_from_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading configuration from environment variables."""
    monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "ghp_test123")
    monkeypatch.setenv("OVERLORD_JULES_API_KEY", "key456")
    monkeypatch.setenv("OVERLORD_JULES_BASE_URL", "https://custom.example.com")

    config = OrchestratorConfig(github_token="ghp_test123")

    assert config.github_token == "ghp_test123"
    assert config.jules_api_key == "key456"
    assert config.jules_base_url == "https://custom.example.com"


def test_validation_error_missing_required_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that ValidationError is raised when required github_token is missing."""
    monkeypatch.delenv("OVERLORD_GITHUB_TOKEN", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        OrchestratorConfig.model_validate({})

    assert "github_token" in str(exc_info.value)


def test_default_values_are_correct(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that default values are set correctly."""
    monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "ghp_required")

    config = OrchestratorConfig(github_token="ghp_required")

    assert config.jules_api_key is None
    assert config.jules_base_url == "https://jules.googleapis.com/v1alpha"
    assert config.github_app_token is None
    assert config.default_target_branch == "main"
    assert config.jules_session_timeout == 3600
    assert config.jules_poll_interval == 30
    assert config.max_concurrent_sessions == 5
    assert config.merge_queue_enabled is True
    assert config.log_level == "INFO"


def test_overlord_jules_api_key_sets_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that OVERLORD_JULES_API_KEY environment variable sets jules_api_key."""
    monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "ghp_required")
    monkeypatch.setenv("OVERLORD_JULES_API_KEY", "secret_key_789")

    config = OrchestratorConfig(github_token="ghp_required")

    assert config.jules_api_key == "secret_key_789"


def test_overlord_max_concurrent_sessions_parses_as_int(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that OVERLORD_MAX_CONCURRENT_SESSIONS is parsed as integer."""
    monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "ghp_required")
    monkeypatch.setenv("OVERLORD_MAX_CONCURRENT_SESSIONS", "10")

    config = OrchestratorConfig(github_token="ghp_required")

    assert config.max_concurrent_sessions == 10
    assert isinstance(config.max_concurrent_sessions, int)
