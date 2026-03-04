"""Core orchestration logic for AI agent coordination."""

import structlog
from structlog.typing import FilteringBoundLogger

from overlord.config import OrchestratorConfig
from overlord.dag import PRDependencyGraph
from overlord.exceptions import AgentError
from overlord.merge_queue import MergeQueueClient
from overlord.models import MergeQueueEntry, PRReference, SessionReference, TaskDefinition
from overlord.protocols import AgentClient

logger: FilteringBoundLogger = structlog.get_logger()

__all__ = ["AgentOrchestrator"]


class AgentOrchestrator:
    """Core orchestrator that coordinates AI coding agents.

    Manages agent clients, dispatches tasks, computes PR merge order,
    and enqueues PRs into GitHub's merge queue.
    """

    def __init__(self, config: OrchestratorConfig) -> None:
        self._config: OrchestratorConfig = config
        self._clients: dict[str, AgentClient] = {}
        self._logger: FilteringBoundLogger = structlog.get_logger()

    def register_client(self, name: str, client: AgentClient) -> None:
        """Register an agent client by name."""
        self._clients[name] = client
        self._logger.info("agent_client_registered", name=name)

    async def dispatch_task(self, task: TaskDefinition) -> SessionReference:
        """Dispatch a task to the appropriate agent client.

        Looks up client by task.agent_type name.
        Raises AgentError if agent type is not registered.
        """
        agent_name = task.agent_type.value
        client = self._clients.get(agent_name)
        if client is None:
            raise AgentError(f"No client registered for agent type: {agent_name}")

        ref = await client.dispatch_task(task)
        self._logger.info(
            "task_dispatched",
            agent=agent_name,
            task_id=task.task_id,
            session_id=ref.session_id,
        )
        return ref

    async def get_task_status(self, session_ref: SessionReference) -> SessionReference:
        """Get current status of a session from the appropriate client."""
        agent_name = session_ref.agent_type.value
        client = self._clients.get(agent_name)
        if client is None:
            raise AgentError(f"No client registered for agent type: {agent_name}")

        return await client.get_status(session_ref)

    async def compute_merge_order(
        self,
        owner: str,
        repo: str,
        open_prs: list[PRReference],
    ) -> list[PRReference]:
        """Compute topological merge order for a list of PRs.

        Parses Depends-On/Requires directives from PR bodies to build
        the dependency graph before computing topological order.
        """
        del owner, repo
        graph = PRDependencyGraph()
        for pr in open_prs:
            graph.add_pr(pr)
            if pr.body:
                deps = graph.parse_dependencies_from_body(
                    pr.body,
                    default_owner=pr.owner,
                    default_repo=pr.repo,
                )
                if deps:
                    graph.add_pr(pr, depends_on=deps)

        return graph.get_merge_order()

    async def enqueue_for_merge(self, pr_ref: PRReference, jump: bool = False) -> MergeQueueEntry:
        """Enqueue a PR for merge using GitHub's merge queue."""
        async with MergeQueueClient(github_token=self._config.github_token) as mq_client:
            if pr_ref.node_id is None:
                node_id = await mq_client.get_pr_node_id(pr_ref)
                pr_ref = PRReference(
                    owner=pr_ref.owner,
                    repo=pr_ref.repo,
                    number=pr_ref.number,
                    node_id=node_id,
                    title=pr_ref.title,
                    body=pr_ref.body,
                )

            entry = await mq_client.enqueue_pr(pr_ref, jump=jump)
            self._logger.info(
                "pr_enqueued",
                pr=f"{pr_ref.owner}/{pr_ref.repo}#{pr_ref.number}",
                entry_id=entry.entry_id,
            )
            return entry

    async def orchestrate_merge(
        self,
        owner: str,
        repo: str,
        open_prs: list[PRReference],
    ) -> list[MergeQueueEntry]:
        """Compute merge order and enqueue all PRs."""
        ordered_prs = await self.compute_merge_order(owner, repo, open_prs)
        entries: list[MergeQueueEntry] = []
        for pr in ordered_prs:
            entry = await self.enqueue_for_merge(pr)
            entries.append(entry)
        return entries
