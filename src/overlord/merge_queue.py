"""GitHub merge queue client using GraphQL API."""

from types import TracebackType

import httpx

from overlord.exceptions import MergeQueueError
from overlord.models import MergeQueueEntry, PRReference


class MergeQueueClient:
    """Client for GitHub's merge queue using GraphQL API.

    Note: PyGithub lacks native merge queue support.
    This client uses httpx directly for GraphQL.
    """

    def __init__(
        self,
        github_token: str,
        base_url: str = "https://api.github.com/graphql",
    ) -> None:
        self._token = github_token
        self._base_url = base_url
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {github_token}",
                "Content-Type": "application/json",
            }
        )

    async def __aenter__(self) -> "MergeQueueClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        del exc_type, exc, tb
        await self._client.aclose()

    def _check_graphql_response(self, data: dict[str, object]) -> None:
        """Raise MergeQueueError if GraphQL response contains errors."""
        if "errors" in data:
            errors = data["errors"]
            raise MergeQueueError(f"GraphQL errors: {errors}")

    async def enqueue_pr(self, pr_ref: PRReference, jump: bool = False) -> MergeQueueEntry:
        """Enqueue a PR in the merge queue.

        Requires pr_ref.node_id to be set (use get_pr_node_id() first).
        """
        if pr_ref.node_id is None:
            raise MergeQueueError(
                f"PR {pr_ref.owner}/{pr_ref.repo}#{pr_ref.number} has no node_id. "
                "Call get_pr_node_id() first."
            )

        mutation = """
        mutation EnqueuePR($pullRequestId: ID!, $jump: Boolean) {
          enqueuePullRequest(input: {pullRequestId: $pullRequestId, jump: $jump}) {
            mergeQueueEntry {
              id
              position
            }
          }
        }
        """
        payload: dict[str, object] = {
            "query": mutation,
            "variables": {"pullRequestId": pr_ref.node_id, "jump": jump},
        }
        response = await self._client.post(self._base_url, json=payload)
        if not response.is_success:
            raise MergeQueueError(f"GraphQL request failed: {response.status_code}")

        data: dict[str, object] = response.json()
        self._check_graphql_response(data)

        data_field = data.get("data")
        enqueue_field: object = None
        entry_data_field: object = None
        if isinstance(data_field, dict):
            enqueue_field = data_field.get("enqueuePullRequest")
        if isinstance(enqueue_field, dict):
            entry_data_field = enqueue_field.get("mergeQueueEntry")

        entry_id = ""
        position: int | None = None
        if isinstance(entry_data_field, dict):
            raw_id = entry_data_field.get("id", "")
            entry_id = str(raw_id) if raw_id is not None else ""
            raw_pos = entry_data_field.get("position")
            position = int(raw_pos) if isinstance(raw_pos, int) else None

        return MergeQueueEntry(
            entry_id=entry_id,
            pr_ref=pr_ref,
            position=position,
        )

    async def get_pr_node_id(self, pr_ref: PRReference) -> str:
        """Get the GraphQL node_id for a PR."""
        query = """
        query GetPRNodeId($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              id
            }
          }
        }
        """
        payload: dict[str, object] = {
            "query": query,
            "variables": {
                "owner": pr_ref.owner,
                "repo": pr_ref.repo,
                "number": pr_ref.number,
            },
        }
        response = await self._client.post(self._base_url, json=payload)
        if not response.is_success:
            raise MergeQueueError(f"GraphQL request failed: {response.status_code}")

        data: dict[str, object] = response.json()
        self._check_graphql_response(data)

        data_field = data.get("data")
        repo_field: object = None
        pr_field: object = None
        if isinstance(data_field, dict):
            repo_field = data_field.get("repository")
        if isinstance(repo_field, dict):
            pr_field = repo_field.get("pullRequest")

        node_id: object = None
        if isinstance(pr_field, dict):
            node_id = pr_field.get("id")

        if node_id is None:
            raise MergeQueueError(f"PR {pr_ref.owner}/{pr_ref.repo}#{pr_ref.number} not found")
        return str(node_id)

    async def check_merge_queue_enabled(self, owner: str, repo: str, branch: str = "main") -> bool:
        """Check if merge queue is enabled for a branch."""
        query = """
        query CheckMergeQueue($owner: String!, $repo: String!, $branch: String!) {
          repository(owner: $owner, name: $repo) {
            branchProtectionRules(first: 10) {
              nodes {
                pattern
                requiresLinearHistory
                requiresMergeQueue
              }
            }
          }
        }
        """
        payload: dict[str, object] = {
            "query": query,
            "variables": {"owner": owner, "repo": repo, "branch": branch},
        }
        response = await self._client.post(self._base_url, json=payload)
        if not response.is_success:
            return False

        data: dict[str, object] = response.json()
        if "errors" in data:
            return False

        data_field = data.get("data")
        repo_field: object = None
        rules_field: object = None
        nodes: object = None
        if isinstance(data_field, dict):
            repo_field = data_field.get("repository")
        if isinstance(repo_field, dict):
            rules_field = repo_field.get("branchProtectionRules")
        if isinstance(rules_field, dict):
            nodes = rules_field.get("nodes")

        if not isinstance(nodes, list):
            return False

        return any(
            isinstance(rule, dict) and rule.get("requiresMergeQueue", False) is True
            for rule in nodes
        )
