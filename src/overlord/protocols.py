from typing import Protocol

from overlord.models import SessionReference, TaskDefinition


class AgentClient(Protocol):
    async def dispatch_task(self, task: TaskDefinition) -> SessionReference: ...

    async def get_status(self, session_ref: SessionReference) -> SessionReference: ...

    async def cancel(self, session_ref: SessionReference) -> None: ...
