"""CLI entry point for OpenCode Overlord."""

import argparse
import asyncio
import os
import sys

import structlog
from structlog.typing import FilteringBoundLogger

from overlord.clients.copilot import CopilotClient
from overlord.clients.jules import JulesClient
from overlord.config import OrchestratorConfig
from overlord.exceptions import OverlordError
from overlord.models import AgentType, PRReference, SessionReference, TaskDefinition
from overlord.orchestrator import AgentOrchestrator
from overlord.protocols import AgentClient

logger: FilteringBoundLogger = structlog.get_logger()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="overlord",
        description="OpenCode Overlord CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # dispatch subcommand
    dispatch_p = subparsers.add_parser("dispatch", help="Dispatch a task to an agent")
    dispatch_p.add_argument(
        "--agent",
        required=True,
        choices=["jules", "copilot"],
        help="Agent type",
    )
    dispatch_p.add_argument("--repo", required=True, help="Target repo (owner/repo)")
    dispatch_p.add_argument("--task", required=True, help="Task description")
    dispatch_p.add_argument(
        "--branch",
        default="main",
        help="Target branch (default: main)",
    )

    # status subcommand
    status_p = subparsers.add_parser("status", help="Check status of a session")
    status_p.add_argument("--session-id", required=True, help="Session reference ID")
    status_p.add_argument(
        "--agent",
        required=True,
        choices=["jules", "copilot"],
        help="Agent type",
    )

    # merge-order subcommand
    merge_p = subparsers.add_parser("merge-order", help="Compute merge order for open PRs")
    merge_p.add_argument("--repo", required=True, help="Target repo (owner/repo)")

    # enqueue subcommand
    enqueue_p = subparsers.add_parser("enqueue", help="Enqueue a PR for merge")
    enqueue_p.add_argument("--repo", required=True, help="Target repo (owner/repo)")
    enqueue_p.add_argument("--pr", required=True, type=int, help="PR number")
    enqueue_p.add_argument("--jump", action="store_true", help="Add to front of queue")

    return parser.parse_args(argv)


async def main(args: argparse.Namespace) -> int:
    """Execute the CLI command."""
    try:
        github_token = os.environ.get("OVERLORD_GITHUB_TOKEN", "")
        config = OrchestratorConfig(github_token=github_token)
        orchestrator = AgentOrchestrator(config)

        if args.command == "dispatch":
            # register appropriate client
            agent_type = AgentType(args.agent)
            client: AgentClient
            if agent_type == AgentType.JULES:
                client = JulesClient(
                    api_key=config.jules_api_key or "",
                    base_url=config.jules_base_url,
                )
            elif agent_type == AgentType.COPILOT:
                client = CopilotClient(github_token=config.github_token)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            orchestrator.register_client(agent_type.value, client)

            owner, repo_name = args.repo.split("/", 1)
            task = TaskDefinition(
                task_id=f"{args.agent}-{owner}-{repo_name}",
                agent_type=agent_type,
                description=args.task,
                target_repo=args.repo,
                target_branch=args.branch,
            )
            ref = await orchestrator.dispatch_task(task)
            logger.info("task_dispatched", session_id=ref.session_id, agent=args.agent)
            return 0

        elif args.command == "status":
            agent_type = AgentType(args.agent)
            client_obj: AgentClient
            if agent_type == AgentType.JULES:
                client_obj = JulesClient(
                    api_key=config.jules_api_key or "",
                    base_url=config.jules_base_url,
                )
            elif agent_type == AgentType.COPILOT:
                client_obj = CopilotClient(github_token=config.github_token)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")
            orchestrator.register_client(agent_type.value, client_obj)

            session_ref = SessionReference(
                session_id=args.session_id,
                agent_type=agent_type,
                task_id="",
                status="",
            )
            updated = await orchestrator.get_task_status(session_ref)
            logger.info("session_status", session_id=updated.session_id, status=updated.status)
            return 0

        elif args.command == "merge-order":
            owner, repo_name = args.repo.split("/", 1)
            ordered = await orchestrator.compute_merge_order(owner, repo_name, [])
            logger.info("merge_order_computed", count=len(ordered))
            return 0

        elif args.command == "enqueue":
            owner, repo_name = args.repo.split("/", 1)
            pr_ref = PRReference(owner=owner, repo=repo_name, number=args.pr)
            entry = await orchestrator.enqueue_for_merge(pr_ref, jump=args.jump)
            logger.info("pr_enqueued", entry_id=entry.entry_id)
            return 0

        return 0
    except OverlordError as exc:
        logger.error("overlord_error", error=str(exc))
        return 1
    except Exception as exc:
        logger.error("unexpected_error", error=str(exc))
        return 1


def cli() -> None:
    """Entry point for the CLI."""
    args = parse_args()
    sys.exit(asyncio.run(main(args)))
