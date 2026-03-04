from unittest.mock import MagicMock, patch

import pytest

from overlord.clients.copilot import CopilotClient
from overlord.exceptions import CopilotError
from overlord.models import AgentType, SessionReference, TaskDefinition


def _make_task(description: str = "Fix the bug", repo: str = "owner/repo") -> TaskDefinition:
    return TaskDefinition(
        task_id="t-1",
        description=description,
        target_repo=repo,
        agent_type=AgentType.COPILOT,
    )


def _make_session_ref(session_id: str = "owner/repo#42") -> SessionReference:
    return SessionReference(
        session_id=session_id,
        agent_type=AgentType.COPILOT,
        task_id="t-1",
        status="pending",
    )


async def test_dispatch_task_creates_issue() -> None:
    mock_issue = MagicMock()
    mock_issue.number = 42
    mock_repo = MagicMock()
    mock_repo.create_issue.return_value = mock_issue
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        ref = await client.dispatch_task(_make_task())

    mock_repo.create_issue.assert_called_once()
    call_kwargs = mock_repo.create_issue.call_args[1]
    assert "[Copilot]" in call_kwargs["title"]
    assert "@copilot" in call_kwargs["body"]
    assert ref.agent_type == AgentType.COPILOT


async def test_dispatch_returns_correct_session_ref() -> None:
    mock_issue = MagicMock()
    mock_issue.number = 42
    mock_repo = MagicMock()
    mock_repo.create_issue.return_value = mock_issue
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        ref = await client.dispatch_task(_make_task())

    assert ref.session_id == "owner/repo#42"
    assert ref.task_id == "t-1"
    assert ref.status == "pending"
    assert ref.agent_type == AgentType.COPILOT


async def test_get_status_pending_no_pr() -> None:
    mock_issue = MagicMock()
    mock_issue.state = "open"
    mock_repo = MagicMock()
    mock_repo.get_pulls.return_value = []
    mock_repo.get_issue.return_value = mock_issue
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        result = await client.get_status(_make_session_ref())

    assert result.status == "pending"
    assert result.session_id == "owner/repo#42"


async def test_get_status_in_progress_with_copilot_pr() -> None:
    mock_pr = MagicMock()
    mock_pr.head.ref = "copilot/fix-the-bug"
    mock_repo = MagicMock()
    mock_repo.get_pulls.return_value = [mock_pr]
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        result = await client.get_status(_make_session_ref())

    assert result.status == "in_progress"


async def test_get_status_completed_when_issue_closed() -> None:
    mock_issue = MagicMock()
    mock_issue.state = "closed"
    mock_repo = MagicMock()
    mock_repo.get_pulls.return_value = []
    mock_repo.get_issue.return_value = mock_issue
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        result = await client.get_status(_make_session_ref())

    assert result.status == "completed"


async def test_cancel_closes_issue() -> None:
    mock_issue = MagicMock()
    mock_repo = MagicMock()
    mock_repo.get_issue.return_value = mock_issue
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        await client.cancel(_make_session_ref())

    mock_repo.get_issue.assert_called_once_with(42)
    mock_issue.edit.assert_called_once_with(state="closed")


async def test_dispatch_repo_not_found_raises_copilot_error() -> None:
    from github.GithubException import UnknownObjectException

    mock_github = MagicMock()
    mock_github.get_repo.side_effect = UnknownObjectException(
        status=404, data={"message": "Not Found"}, headers={}
    )

    with patch("overlord.clients.copilot.Github", return_value=mock_github):
        client = CopilotClient(github_token="fake-token")
        with pytest.raises(CopilotError, match="Repository not found"):
            await client.dispatch_task(_make_task(repo="owner/nonexistent"))
