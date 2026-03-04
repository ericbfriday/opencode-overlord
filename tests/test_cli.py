"""Tests for the CLI module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from overlord.cli import main, parse_args
from overlord.exceptions import OverlordError
from overlord.models import AgentType, MergeQueueEntry, PRReference, SessionReference
from overlord.protocols import AgentClient


class TestParseArgs:
    """Tests for parse_args function."""

    def test_parse_dispatch_args(self) -> None:
        """Test parsing dispatch subcommand arguments."""
        args = parse_args(
            ["dispatch", "--agent", "jules", "--repo", "owner/repo", "--task", "fix bug"]
        )
        assert args.command == "dispatch"
        assert args.agent == "jules"
        assert args.repo == "owner/repo"
        assert args.task == "fix bug"
        assert args.branch == "main"

    def test_parse_status_args(self) -> None:
        """Test parsing status subcommand arguments."""
        args = parse_args(["status", "--session-id", "ses_123", "--agent", "copilot"])
        assert args.command == "status"
        assert args.session_id == "ses_123"
        assert args.agent == "copilot"

    def test_parse_merge_order_args(self) -> None:
        """Test parsing merge-order subcommand arguments."""
        args = parse_args(["merge-order", "--repo", "owner/repo"])
        assert args.command == "merge-order"
        assert args.repo == "owner/repo"

    def test_parse_enqueue_args(self) -> None:
        """Test parsing enqueue subcommand arguments with --jump."""
        args = parse_args(["enqueue", "--repo", "owner/repo", "--pr", "42", "--jump"])
        assert args.command == "enqueue"
        assert args.repo == "owner/repo"
        assert args.pr == 42
        assert args.jump is True

    def test_parse_enqueue_no_jump(self) -> None:
        """Test parsing enqueue subcommand arguments without --jump."""
        args = parse_args(["enqueue", "--repo", "owner/repo", "--pr", "1"])
        assert args.command == "enqueue"
        assert args.repo == "owner/repo"
        assert args.pr == 1
        assert args.jump is False


class TestMainDispatch:
    """Tests for main function with dispatch command."""

    @pytest.mark.asyncio
    async def test_main_dispatch_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test dispatch command returns 0 on success."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(
            ["dispatch", "--agent", "jules", "--repo", "owner/repo", "--task", "fix bug"]
        )

        mock_client = MagicMock(spec=AgentClient)
        mock_client.dispatch_task = AsyncMock(
            return_value=SessionReference(
                session_id="sess-1",
                agent_type=AgentType.JULES,
                task_id="t-1",
                status="pending",
            )
        )

        mock_config = MagicMock()
        mock_config.github_token = "test-token"
        mock_config.jules_api_key = "test-key"
        mock_config.julius_base_url = "https://test.com"

        with (
            patch("overlord.cli.JulesClient", return_value=mock_client),
            patch("overlord.cli.OrchestratorConfig", return_value=mock_config),
        ):
            result = await main(args)
            assert result == 0
            mock_client.dispatch_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_dispatch_copilot(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test dispatch command with copilot agent."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(
            ["dispatch", "--agent", "copilot", "--repo", "owner/repo", "--task", "fix bug"]
        )

        mock_client = MagicMock(spec=AgentClient)
        mock_client.dispatch_task = AsyncMock(
            return_value=SessionReference(
                session_id="owner/repo#42",
                agent_type=AgentType.COPILOT,
                task_id="t-2",
                status="pending",
            )
        )

        mock_config = MagicMock()
        mock_config.github_token = "test-token"
        mock_config.julius_api_key = None
        mock_config.julius_base_url = "https://test.com"

        with (
            patch("overlord.cli.CopilotClient", return_value=mock_client),
            patch("overlord.cli.OrchestratorConfig", return_value=mock_config),
        ):
            result = await main(args)
            assert result == 0
            mock_client.dispatch_task.assert_called_once()


class TestMainStatus:
    """Tests for main function with status command."""

    @pytest.mark.asyncio
    async def test_main_status_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test status command returns 0 on success."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(["status", "--session-id", "ses_123", "--agent", "jules"])

        mock_client = MagicMock(spec=AgentClient)
        mock_client.get_status = AsyncMock(
            return_value=SessionReference(
                session_id="ses_123",
                agent_type=AgentType.JULES,
                task_id="t-1",
                status="running",
            )
        )

        mock_config = MagicMock()
        mock_config.github_token = "test-token"
        mock_config.julius_api_key = "test-key"
        mock_config.julius_base_url = "https://test.com"

        with (
            patch("overlord.cli.JulesClient", return_value=mock_client),
            patch("overlord.cli.OrchestratorConfig", return_value=mock_config),
        ):
            result = await main(args)
            assert result == 0
            mock_client.get_status.assert_called_once()


class TestMainMergeOrder:
    """Tests for main function with merge-order command."""

    @pytest.mark.asyncio
    async def test_main_merge_order_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test merge-order command returns 0 on success."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(["merge-order", "--repo", "owner/repo"])

        with patch("overlord.cli.OrchestratorConfig") as mock_config_class:
            mock_config = MagicMock()
            mock_config.github_token = "test-token"
            mock_config.jules_api_key = None
            mock_config.jules_base_url = "https://test.com"
            mock_config_class.return_value = mock_config

            result = await main(args)
            assert result == 0


class TestMainEnqueue:
    """Tests for main function with enqueue command."""

    @pytest.mark.asyncio
    async def test_main_enqueue_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test enqueue command returns 0 on success."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(["enqueue", "--repo", "owner/repo", "--pr", "42"])

        with patch("overlord.cli.OrchestratorConfig") as mock_config_class:
            mock_config = MagicMock()
            mock_config.github_token = "test-token"
            mock_config.jules_api_key = None
            mock_config.julius_base_url = "https://test.com"
            mock_config_class.return_value = mock_config

            with patch("overlord.cli.AgentOrchestrator.enqueue_for_merge") as mock_enqueue:
                mock_enqueue.return_value = MergeQueueEntry(
                    entry_id="entry-1",
                    pr_ref=PRReference(owner="owner", repo="repo", number=42),
                    position=1,
                )

                result = await main(args)
                assert result == 0


class TestMainErrorHandling:
    """Tests for error handling in main function."""

    @pytest.mark.asyncio
    async def test_main_overlord_error_returns_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that OverlordError returns exit code 1."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(
            ["dispatch", "--agent", "jules", "--repo", "owner/repo", "--task", "fix bug"]
        )

        mock_client = MagicMock(spec=AgentClient)
        mock_client.dispatch_task = AsyncMock(side_effect=OverlordError("Test error"))

        mock_config = MagicMock()
        mock_config.github_token = "test-token"
        mock_config.julius_api_key = "test-key"
        mock_config.julius_base_url = "https://test.com"

        with (
            patch("overlord.cli.JulesClient", return_value=mock_client),
            patch("overlord.cli.OrchestratorConfig", return_value=mock_config),
        ):
            result = await main(args)
            assert result == 1

    @pytest.mark.asyncio
    async def test_main_unexpected_error_returns_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that unexpected exceptions return exit code 1."""
        monkeypatch.setenv("OVERLORD_GITHUB_TOKEN", "test-token")

        args = parse_args(
            ["dispatch", "--agent", "jules", "--repo", "owner/repo", "--task", "fix bug"]
        )

        mock_client = MagicMock(spec=AgentClient)
        mock_client.dispatch_task = AsyncMock(side_effect=ValueError("Unexpected error"))

        mock_config = MagicMock()
        mock_config.github_token = "test-token"
        mock_config.julius_api_key = "test-key"
        mock_config.julius_base_url = "https://test.com"

        with (
            patch("overlord.cli.JulesClient", return_value=mock_client),
            patch("overlord.cli.OrchestratorConfig", return_value=mock_config),
        ):
            result = await main(args)
            assert result == 1
