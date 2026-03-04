import pytest

from overlord.models import AgentConfig, AgentType
from overlord.orchestrator import AgentOrchestrator


@pytest.fixture
def orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def test_register_agent(orchestrator: AgentOrchestrator) -> None:
    config = AgentConfig(name="test", agent_type=AgentType.JULES)
    orchestrator.register_agent("test", config)
    assert "test" in orchestrator.agents


@pytest.mark.asyncio
async def test_trigger_unknown_agent_raises(orchestrator: AgentOrchestrator) -> None:
    with pytest.raises(ValueError, match="Unknown agent"):
        await orchestrator.trigger_agent("unknown", "test task")
