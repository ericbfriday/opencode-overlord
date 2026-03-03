"""GitHub Copilot agent integration."""

from .orchestrator import AgentConfig


def create_copilot_config() -> AgentConfig:
    """Create configuration for GitHub Copilot agent."""
    return AgentConfig(
        name="copilot",
        agent_type="github_copilot",
        endpoint=None,  # Copilot uses GitHub API
    )
