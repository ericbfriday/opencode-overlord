"""Google Jules agent integration."""

from .orchestrator import AgentConfig


def create_jules_config() -> AgentConfig:
    """Create configuration for Google Jules agent."""
    return AgentConfig(
        name="jules",
        agent_type="google_jules",
        endpoint=None,  # Jules uses GitHub App integration
    )
