import asyncio

from github import Github
from github.GithubException import UnknownObjectException

from overlord.exceptions import CopilotError
from overlord.models import AgentType, SessionReference, TaskDefinition


class CopilotClient:
    def __init__(self, github_token: str) -> None:
        self._github = Github(github_token)

    async def dispatch_task(self, task: TaskDefinition) -> SessionReference:
        def _create_issue() -> int:
            try:
                repo = self._github.get_repo(task.target_repo)
            except UnknownObjectException as e:
                raise CopilotError(f"Repository not found: {task.target_repo}") from e

            issue = repo.create_issue(
                title=f"[Copilot] {task.description[:100]}",
                body=f"@copilot {task.description}",
            )
            return int(issue.number)

        issue_number = await asyncio.to_thread(_create_issue)
        session_id = f"{task.target_repo}#{issue_number}"
        return SessionReference(
            session_id=session_id,
            agent_type=AgentType.COPILOT,
            task_id=task.task_id,
            status="pending",
        )

    async def get_status(self, session_ref: SessionReference) -> SessionReference:
        repo_name, issue_str = session_ref.session_id.rsplit("#", 1)
        issue_number = int(issue_str)

        def _check() -> str:
            repo = self._github.get_repo(repo_name)
            open_prs = list(repo.get_pulls(state="open"))
            copilot_prs = [pr for pr in open_prs if pr.head.ref.startswith("copilot/")]
            if copilot_prs:
                return "in_progress"
            issue = repo.get_issue(issue_number)
            if issue.state == "closed":
                return "completed"
            return "pending"

        status = await asyncio.to_thread(_check)
        return SessionReference(
            session_id=session_ref.session_id,
            agent_type=AgentType.COPILOT,
            task_id=session_ref.task_id,
            status=status,
        )

    async def cancel(self, session_ref: SessionReference) -> None:
        repo_name, issue_str = session_ref.session_id.rsplit("#", 1)
        issue_number = int(issue_str)

        def _close_issue() -> None:
            repo = self._github.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            issue.edit(state="closed")

        await asyncio.to_thread(_close_issue)
