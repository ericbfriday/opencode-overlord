"""Core orchestration logic for AI agent coordination."""

import structlog

from overlord.models import AgentConfig, AgentType

logger = structlog.get_logger()

__all__ = ["AgentConfig", "AgentOrchestrator", "AgentType"]


class AgentOrchestrator:
    def __init__(self) -> None:
        self.agents: dict[str, AgentConfig] = {}

    def register_agent(self, name: str, config: AgentConfig) -> None:
        self.agents[name] = config
        logger.info("agent_registered", name=name)

    async def trigger_agent(self, name: str, task: str) -> dict[str, str]:
        if name not in self.agents:
            raise ValueError(f"Unknown agent: {name}")

        logger.info("triggering_agent", name=name, task=task)
        return {"status": "triggered", "agent": name, "task": task}
