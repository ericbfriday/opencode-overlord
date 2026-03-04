"""Configuration management for OpenCode Overlord using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorConfig(BaseSettings):
    """Configuration for the OpenCode Orchestrator.

    All configuration is loaded from environment variables with the OVERLORD_ prefix.
    """

    model_config = SettingsConfigDict(env_prefix="OVERLORD_")

    # Jules configuration
    jules_api_key: str | None = None
    jules_base_url: str = "https://jules.googleapis.com/v1alpha"

    # GitHub configuration
    github_token: str  # Required field — no default
    github_app_token: str | None = None

    # Orchestration settings
    default_target_branch: str = "main"
    jules_session_timeout: int = 3600
    jules_poll_interval: int = 30
    max_concurrent_sessions: int = 5
    merge_queue_enabled: bool = True
    log_level: str = "INFO"
