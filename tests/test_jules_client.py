import httpx
import pytest
import respx

from overlord.clients.jules import JulesClient
from overlord.exceptions import JulesAPIError
from overlord.models import AgentType, SessionReference, TaskDefinition


def make_task() -> TaskDefinition:
    return TaskDefinition(
        task_id="t-1",
        description="Fix the bug",
        target_repo="owner/repo",
        agent_type=AgentType.JULES,
    )


async def test_dispatch_task() -> None:
    task = make_task()
    with respx.mock:
        route = respx.post("https://jules.googleapis.com/v1alpha/sessions").mock(
            return_value=httpx.Response(200, json={"sessionId": "sess-1", "status": "pending"})
        )
        async with JulesClient(api_key="test-key") as client:
            ref = await client.dispatch_task(task)

        assert route.called
        assert ref.session_id == "sess-1"
        assert ref.agent_type == AgentType.JULES
        assert ref.task_id == "t-1"
        assert ref.status == "pending"


async def test_get_status() -> None:
    session_ref = SessionReference(
        session_id="sess-1",
        agent_type=AgentType.JULES,
        task_id="t-1",
        status="pending",
    )
    with respx.mock:
        route = respx.get("https://jules.googleapis.com/v1alpha/sessions/sess-1").mock(
            return_value=httpx.Response(200, json={"status": "running"})
        )
        async with JulesClient(api_key="test-key") as client:
            updated = await client.get_status(session_ref)

        assert route.called
        assert updated.session_id == "sess-1"
        assert updated.task_id == "t-1"
        assert updated.status == "running"


async def test_approve_plan() -> None:
    with respx.mock:
        route = respx.post("https://jules.googleapis.com/v1alpha/sessions/sess-1:approvePlan").mock(
            return_value=httpx.Response(200)
        )
        async with JulesClient(api_key="test-key") as client:
            await client.approve_plan("sess-1")

        assert route.called


async def test_get_activities() -> None:
    with respx.mock:
        route = respx.get("https://jules.googleapis.com/v1alpha/sessions/sess-1/activities").mock(
            return_value=httpx.Response(
                200,
                json={
                    "activities": [
                        {
                            "activityId": "a-1",
                            "type": "message",
                            "content": "Started work",
                            "timestamp": "2026-03-03T00:00:00Z",
                        }
                    ]
                },
            )
        )
        async with JulesClient(api_key="test-key") as client:
            activities = await client.get_activities("sess-1")

        assert route.called
        assert len(activities) == 1
        assert activities[0].activity_id == "a-1"
        assert activities[0].type == "message"
        assert activities[0].content == "Started work"


async def test_send_message() -> None:
    with respx.mock:
        route = respx.post("https://jules.googleapis.com/v1alpha/sessions/sess-1:sendMessage").mock(
            return_value=httpx.Response(200)
        )
        async with JulesClient(api_key="test-key") as client:
            await client.send_message("sess-1", "hello")

        assert route.called


async def test_list_sources() -> None:
    with respx.mock:
        route = respx.get("https://jules.googleapis.com/v1alpha/sources").mock(
            return_value=httpx.Response(
                200,
                json={"sources": [{"name": "repo-1", "repository": "owner/repo"}]},
            )
        )
        async with JulesClient(api_key="test-key") as client:
            sources = await client.list_sources()

        assert route.called
        assert sources == [{"name": "repo-1", "repository": "owner/repo"}]


async def test_401_unauthorized() -> None:
    task = make_task()
    with respx.mock:
        _route = respx.post("https://jules.googleapis.com/v1alpha/sessions").mock(
            return_value=httpx.Response(401, text="unauthorized")
        )
        async with JulesClient(api_key="test-key") as client:
            with pytest.raises(JulesAPIError) as exc_info:
                _ = await client.dispatch_task(task)

    assert exc_info.value.status_code == 401
    assert exc_info.value.response_body == "unauthorized"


async def test_429_rate_limit() -> None:
    task = make_task()
    with respx.mock:
        _route = respx.post("https://jules.googleapis.com/v1alpha/sessions").mock(
            return_value=httpx.Response(429, text="rate limited")
        )
        async with JulesClient(api_key="test-key") as client:
            with pytest.raises(JulesAPIError) as exc_info:
                _ = await client.dispatch_task(task)

    assert exc_info.value.status_code == 429
    assert exc_info.value.response_body == "rate limited"


async def test_500_server_error() -> None:
    task = make_task()
    with respx.mock:
        _route = respx.post("https://jules.googleapis.com/v1alpha/sessions").mock(
            return_value=httpx.Response(500, text="server error")
        )
        async with JulesClient(api_key="test-key") as client:
            with pytest.raises(JulesAPIError) as exc_info:
                _ = await client.dispatch_task(task)

    assert exc_info.value.status_code == 500
    assert exc_info.value.response_body == "server error"


async def test_aenter_and_aexit() -> None:
    client = JulesClient(api_key="test-key")
    entered = await client.__aenter__()
    assert entered is client
    await client.__aexit__(None, None, None)
