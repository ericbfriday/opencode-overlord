import httpx
import pytest
import respx

from overlord.exceptions import MergeQueueError
from overlord.merge_queue import MergeQueueClient
from overlord.models import PRReference

GRAPHQL_URL = "https://api.github.com/graphql"


async def test_enqueue_pr() -> None:
    pr = PRReference(owner="me", repo="proj", number=42, node_id="PR_node123")
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "enqueuePullRequest": {"mergeQueueEntry": {"id": "entry-1", "position": 3}}
                    }
                },
            )
        )
        client = MergeQueueClient(github_token="test-token")
        entry = await client.enqueue_pr(pr)
        assert entry.entry_id == "entry-1"
        assert entry.position == 3
        assert entry.pr_ref == pr


async def test_enqueue_pr_with_jump() -> None:
    pr = PRReference(owner="me", repo="proj", number=7, node_id="PR_jump_node")
    with respx.mock:
        route = respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "enqueuePullRequest": {
                            "mergeQueueEntry": {"id": "entry-jump", "position": 1}
                        }
                    }
                },
            )
        )
        client = MergeQueueClient(github_token="test-token")
        entry = await client.enqueue_pr(pr, jump=True)
        assert entry.entry_id == "entry-jump"
        assert entry.position == 1
        sent_body = route.calls.last.request.content
        import json

        payload = json.loads(sent_body)
        assert payload["variables"]["jump"] is True
        assert payload["variables"]["pullRequestId"] == "PR_jump_node"


async def test_enqueue_pr_missing_node_id() -> None:
    pr = PRReference(owner="me", repo="proj", number=99)
    client = MergeQueueClient(github_token="test-token")
    with pytest.raises(MergeQueueError, match="no node_id"):
        await client.enqueue_pr(pr)


async def test_get_pr_node_id() -> None:
    pr = PRReference(owner="acme", repo="backend", number=5)
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"repository": {"pullRequest": {"id": "PR_abc999"}}}},
            )
        )
        client = MergeQueueClient(github_token="test-token")
        node_id = await client.get_pr_node_id(pr)
        assert node_id == "PR_abc999"


async def test_graphql_error_response() -> None:
    pr = PRReference(owner="me", repo="proj", number=42, node_id="PR_node123")
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={"errors": [{"message": "Not authorized", "type": "FORBIDDEN"}]},
            )
        )
        client = MergeQueueClient(github_token="bad-token")
        with pytest.raises(MergeQueueError, match="GraphQL errors"):
            await client.enqueue_pr(pr)


async def test_check_merge_queue_enabled_true() -> None:
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "repository": {
                            "branchProtectionRules": {
                                "nodes": [
                                    {
                                        "pattern": "main",
                                        "requiresLinearHistory": True,
                                        "requiresMergeQueue": True,
                                    }
                                ]
                            }
                        }
                    }
                },
            )
        )
        client = MergeQueueClient(github_token="test-token")
        result = await client.check_merge_queue_enabled("acme", "backend", "main")
        assert result is True


async def test_check_merge_queue_enabled_false() -> None:
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "repository": {
                            "branchProtectionRules": {
                                "nodes": [
                                    {
                                        "pattern": "main",
                                        "requiresLinearHistory": False,
                                        "requiresMergeQueue": False,
                                    }
                                ]
                            }
                        }
                    }
                },
            )
        )
        client = MergeQueueClient(github_token="test-token")
        result = await client.check_merge_queue_enabled("acme", "backend", "main")
        assert result is False


async def test_get_pr_node_id_not_found() -> None:
    pr = PRReference(owner="acme", repo="backend", number=9999)
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"repository": {"pullRequest": None}}},
            )
        )
        client = MergeQueueClient(github_token="test-token")
        with pytest.raises(MergeQueueError, match="not found"):
            await client.get_pr_node_id(pr)


async def test_enqueue_pr_http_error() -> None:
    pr = PRReference(owner="me", repo="proj", number=42, node_id="PR_node123")
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(500, text="Internal Server Error"))
        client = MergeQueueClient(github_token="test-token")
        with pytest.raises(MergeQueueError, match="GraphQL request failed: 500"):
            await client.enqueue_pr(pr)


async def test_context_manager() -> None:
    with respx.mock:
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"repository": {"pullRequest": {"id": "PR_ctx_test"}}}},
            )
        )
        pr = PRReference(owner="me", repo="proj", number=1)
        async with MergeQueueClient(github_token="test-token") as client:
            node_id = await client.get_pr_node_id(pr)
            assert node_id == "PR_ctx_test"
