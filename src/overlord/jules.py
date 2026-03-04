"""Google Jules agent integration."""

from .models import AgentConfig, AgentType


def create_jules_config() -> AgentConfig:
    """Create configuration for Google Jules agent."""
    return AgentConfig(
        name="jules",
        agent_type=AgentType.JULES,
        endpoint=None,  # Jules uses GitHub App integration
    )
