"""GitHub Copilot agent integration."""

from .models import AgentConfig, AgentType


def create_copilot_config() -> AgentConfig:
    """Create configuration for GitHub Copilot agent."""
    return AgentConfig(
        name="copilot",
        agent_type=AgentType.COPILOT,
        endpoint=None,  # Copilot uses GitHub API
    )
