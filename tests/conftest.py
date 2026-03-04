"""Shared test fixtures for the test suite."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from overlord.config import OrchestratorConfig
from overlord.models import AgentType, SessionReference
from overlord.protocols import AgentClient


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch) -> OrchestratorConfig:
    """OrchestratorConfig with test values."""
    monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "ghp_test_token")
    monkeypatch.setenv("OVERLORD_JULES_API_KEY", "jules_test_key")
    return OrchestratorConfig(github_token="ghp_test_token")


@pytest.fixture
def mock_jules_client() -> AgentClient:
    """Mock Jules agent client."""
    client = MagicMock(spec=AgentClient)
    client.dispatch_task = AsyncMock(
        return_value=SessionReference(
            session_id="jules-sess-1",
            agent_type=AgentType.JULES,
            task_id="t-1",
            status="pending",
        )
    )
    client.get_status = AsyncMock(
        return_value=SessionReference(
            session_id="jules-sess-1",
            agent_type=AgentType.JULES,
            task_id="t-1",
            status="running",
        )
    )
    client.cancel = AsyncMock(return_value=None)
    return cast(AgentClient, client)


@pytest.fixture
def mock_copilot_client() -> AgentClient:
    """Mock Copilot agent client."""
    client = MagicMock(spec=AgentClient)
    client.dispatch_task = AsyncMock(
        return_value=SessionReference(
            session_id="owner/repo#42",
            agent_type=AgentType.COPILOT,
            task_id="t-2",
            status="pending",
        )
    )
    client.get_status = AsyncMock(
        return_value=SessionReference(
            session_id="owner/repo#42",
            agent_type=AgentType.COPILOT,
            task_id="t-2",
            status="in_progress",
        )
    )
    client.cancel = AsyncMock(return_value=None)
    return cast(AgentClient, client)
