"""OpenCode agent integration with oh-my-opencode plugin."""

from .orchestrator import AgentConfig


def create_opencode_config() -> AgentConfig:
    """Create configuration for OpenCode agent with oh-my-opencode plugin."""
    return AgentConfig(
        name="opencode",
        agent_type="opencode",
        endpoint=None,  # Configured via environment or config file
    )
