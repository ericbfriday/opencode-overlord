"""Tests for OpenCodeClient stub."""

import pytest

from overlord.clients.opencode import OpenCodeClient
from overlord.models import AgentType, SessionReference, TaskDefinition


async def test_dispatch_task_raises_not_implemented() -> None:
    """Test that dispatch_task raises NotImplementedError."""
    client = OpenCodeClient()
    task = TaskDefinition(
        task_id="t-1",
        description="test",
        target_repo="owner/repo",
        agent_type=AgentType.OPENCODE,
    )
    with pytest.raises(NotImplementedError):
        await client.dispatch_task(task)


async def test_get_status_raises_not_implemented() -> None:
    """Test that get_status raises NotImplementedError."""
    client = OpenCodeClient()
    ref = SessionReference(
        session_id="s-1",
        agent_type=AgentType.OPENCODE,
        task_id="t-1",
        status="pending",
    )
    with pytest.raises(NotImplementedError):
        await client.get_status(ref)


async def test_cancel_raises_not_implemented() -> None:
    """Test that cancel raises NotImplementedError."""
    client = OpenCodeClient()
    ref = SessionReference(
        session_id="s-1",
        agent_type=AgentType.OPENCODE,
        task_id="t-1",
        status="pending",
    )
    with pytest.raises(NotImplementedError):
        await client.cancel(ref)
