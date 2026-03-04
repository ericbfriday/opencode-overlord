from types import TracebackType
from typing import cast, override

import httpx
import structlog

from ..exceptions import JulesAPIError
from ..models import (
    AgentType,
    JulesActivity,
    SessionReference,
    TaskDefinition,
)
from ..protocols import AgentClient


class JulesClient(AgentClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://jules.googleapis.com/v1alpha",
        timeout: float = 30.0,
    ) -> None:
        self._api_key: str = api_key
        self._base_url: str = base_url
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-Goog-Api-Key": api_key},
            timeout=timeout,
        )

    async def __aenter__(self) -> "JulesClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        del exc_type, exc, tb
        await self._client.aclose()

    def _check_response(self, response: httpx.Response) -> None:
        if not response.is_success:
            raise JulesAPIError(
                f"Jules API error: {response.status_code}",
                status_code=response.status_code,
                response_body=response.text,
            )

    @override
    async def dispatch_task(self, task: TaskDefinition) -> SessionReference:
        payload: dict[str, object] = {
            "prompt": task.description,
            "sourceContext": {"repository": task.target_repo},
            "automationMode": "AUTO_CREATE_PR",
            "title": task.description[:100],
        }
        response = await self._client.post("/sessions", json=payload)
        self._check_response(response)
        data = cast(dict[str, object], response.json())
        session_id = cast(str, data["sessionId"])
        status = cast(str, data.get("status", "pending"))
        return SessionReference(
            session_id=session_id,
            agent_type=AgentType.JULES,
            task_id=task.task_id,
            status=status,
        )

    @override
    async def get_status(self, session_ref: SessionReference) -> SessionReference:
        response = await self._client.get(f"/sessions/{session_ref.session_id}")
        self._check_response(response)
        data = cast(dict[str, object], response.json())
        status = cast(str, data.get("status", "unknown"))
        return SessionReference(
            session_id=session_ref.session_id,
            agent_type=AgentType.JULES,
            task_id=session_ref.task_id,
            status=status,
        )

    @override
    async def cancel(self, session_ref: SessionReference) -> None:
        logger = cast(structlog.typing.FilteringBoundLogger, structlog.get_logger())
        logger.warning("jules_cancel_noop", session_id=session_ref.session_id)

    async def approve_plan(self, session_id: str) -> None:
        response = await self._client.post(f"/sessions/{session_id}:approvePlan")
        self._check_response(response)

    async def get_activities(self, session_id: str) -> list[JulesActivity]:
        response = await self._client.get(f"/sessions/{session_id}/activities")
        self._check_response(response)
        data = cast(dict[str, object], response.json())
        activities = cast(list[dict[str, object]], data.get("activities", []))
        return [
            JulesActivity(
                activity_id=cast(str, activity["activityId"]),
                type=cast(str, activity["type"]),
                content=cast(str, activity["content"]),
                timestamp=cast(str, activity["timestamp"]),
            )
            for activity in activities
        ]

    async def send_message(self, session_id: str, message: str) -> None:
        response = await self._client.post(
            f"/sessions/{session_id}:sendMessage",
            json={"message": message},
        )
        self._check_response(response)

    async def list_sources(self) -> list[dict[str, str]]:
        response = await self._client.get("/sources")
        self._check_response(response)
        data = cast(dict[str, object], response.json())
        return cast(list[dict[str, str]], data.get("sources", []))
