"""Tests for the orchestrator module."""

import pytest

from overlord.orchestrator import AgentConfig, AgentOrchestrator


@pytest.fixture
def orchestrator() -> AgentOrchestrator:
    """Create a fresh orchestrator for each test."""
    return AgentOrchestrator()


def test_register_agent(orchestrator: AgentOrchestrator) -> None:
    """Test registering an agent."""
    config = AgentConfig(name="test", agent_type="test_type")
    orchestrator.register_agent("test", config)
    assert "test" in orchestrator.agents


@pytest.mark.asyncio
async def test_trigger_unknown_agent_raises(orchestrator: AgentOrchestrator) -> None:
    """Test that triggering an unknown agent raises an error."""
    with pytest.raises(ValueError, match="Unknown agent"):
        await orchestrator.trigger_agent("unknown", "test task")
