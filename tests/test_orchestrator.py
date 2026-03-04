"""Tests for AgentOrchestrator."""

from unittest.mock import AsyncMock, patch

import pytest

from overlord.config import OrchestratorConfig
from overlord.exceptions import AgentError
from overlord.models import (
    AgentType,
    MergeQueueEntry,
    PRReference,
    SessionReference,
    TaskDefinition,
)
from overlord.orchestrator import AgentOrchestrator
from overlord.protocols import AgentClient


async def test_dispatch_task_routes_to_jules(
    mock_config: OrchestratorConfig,
    mock_jules_client: AgentClient,
) -> None:
    """dispatch_task routes to jules client when agent_type is JULES."""
    orchestrator = AgentOrchestrator(config=mock_config)
    orchestrator.register_client("jules", mock_jules_client)

    task = TaskDefinition(
        task_id="t-1",
        description="Fix the bug",
        target_repo="owner/repo",
        agent_type=AgentType.JULES,
    )
    ref = await orchestrator.dispatch_task(task)
    dispatch_mock = mock_jules_client.dispatch_task
    assert isinstance(dispatch_mock, AsyncMock)
    dispatch_mock.assert_called_once_with(task)
    assert ref.session_id == "jules-sess-1"


async def test_dispatch_unknown_agent_raises(mock_config: OrchestratorConfig) -> None:
    """dispatch_task raises AgentError for unregistered agent."""
    orchestrator = AgentOrchestrator(config=mock_config)
    task = TaskDefinition(
        task_id="t-1",
        description="test",
        target_repo="owner/repo",
        agent_type=AgentType.JULES,
    )
    with pytest.raises(AgentError, match="No client registered"):
        _ = await orchestrator.dispatch_task(task)


async def test_get_task_status_delegates_to_registered_client(
    mock_config: OrchestratorConfig,
    mock_jules_client: AgentClient,
) -> None:
    """get_task_status delegates to the correct client."""
    orchestrator = AgentOrchestrator(config=mock_config)
    orchestrator.register_client("jules", mock_jules_client)

    ref = SessionReference(
        session_id="sess-1",
        agent_type=AgentType.JULES,
        task_id="t-1",
        status="pending",
    )
    result = await orchestrator.get_task_status(ref)
    status_mock = mock_jules_client.get_status
    assert isinstance(status_mock, AsyncMock)
    status_mock.assert_called_once_with(ref)
    assert result.status == "running"


async def test_get_task_status_unknown_agent_raises(mock_config: OrchestratorConfig) -> None:
    """get_task_status raises AgentError when no matching client exists."""
    orchestrator = AgentOrchestrator(config=mock_config)
    ref = SessionReference(
        session_id="sess-1",
        agent_type=AgentType.COPILOT,
        task_id="t-2",
        status="pending",
    )
    with pytest.raises(AgentError, match="No client registered"):
        _ = await orchestrator.get_task_status(ref)


async def test_compute_merge_order_returns_all_prs(mock_config: OrchestratorConfig) -> None:
    """compute_merge_order returns topological ordering of all input PRs."""
    orchestrator = AgentOrchestrator(config=mock_config)

    pr1 = PRReference(owner="me", repo="proj", number=1)
    pr2 = PRReference(owner="me", repo="proj", number=2)
    pr3 = PRReference(owner="me", repo="proj", number=3)

    ordered = await orchestrator.compute_merge_order("me", "proj", [pr1, pr2, pr3])
    assert len(ordered) == 3
    assert set(ordered) == {pr1, pr2, pr3}


async def test_enqueue_for_merge_fetches_node_id_when_missing(
    mock_config: OrchestratorConfig,
) -> None:
    """enqueue_for_merge resolves node_id before enqueue when absent."""
    orchestrator = AgentOrchestrator(config=mock_config)
    pr = PRReference(owner="me", repo="proj", number=1)

    mock_client = AsyncMock()
    mock_client.get_pr_node_id.return_value = "PR_node123"
    mock_client.enqueue_pr.return_value = MergeQueueEntry(
        entry_id="entry-1",
        pr_ref=PRReference(owner="me", repo="proj", number=1, node_id="PR_node123"),
        position=1,
    )
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("overlord.orchestrator.MergeQueueClient", return_value=mock_client):
        entry = await orchestrator.enqueue_for_merge(pr)

    assert entry.entry_id == "entry-1"
    mock_client.get_pr_node_id.assert_awaited_once_with(pr)
    enqueued_pr = mock_client.enqueue_pr.await_args.args[0]
    assert isinstance(enqueued_pr, PRReference)
    assert enqueued_pr.node_id == "PR_node123"


async def test_orchestrate_merge_enqueues_in_computed_order(
    mock_config: OrchestratorConfig,
) -> None:
    """orchestrate_merge enqueues PRs in the same order from compute_merge_order."""
    orchestrator = AgentOrchestrator(config=mock_config)

    pr1 = PRReference(owner="me", repo="proj", number=1, node_id="n1")
    pr2 = PRReference(owner="me", repo="proj", number=2, node_id="n2")
    ordered = [pr1, pr2]

    compute_mock = AsyncMock(return_value=ordered)
    enqueue_mock = AsyncMock(
        side_effect=[
            MergeQueueEntry(entry_id="e1", pr_ref=pr1, position=1),
            MergeQueueEntry(entry_id="e2", pr_ref=pr2, position=2),
        ]
    )

    with (
        patch.object(orchestrator, "compute_merge_order", compute_mock),
        patch.object(orchestrator, "enqueue_for_merge", enqueue_mock),
    ):
        entries = await orchestrator.orchestrate_merge("me", "proj", ordered)

    assert [entry.entry_id for entry in entries] == ["e1", "e2"]
    compute_mock.assert_awaited_once_with("me", "proj", ordered)
    assert enqueue_mock.await_count == 2
    assert enqueue_mock.await_args_list[0].args == (pr1,)
    assert enqueue_mock.await_args_list[1].args == (pr2,)
