"""OpenCode stub client — placeholder for future integration.

OpenCode does not currently have a public programmatic API.
This stub implements the AgentClient protocol and raises NotImplementedError
for all methods until a proper API is available.
"""

from overlord.models import SessionReference, TaskDefinition


class OpenCodeClient:
    """Stub client for OpenCode agent.

    OpenCode programmatic API is not yet available.
    All methods raise NotImplementedError.
    """

    def __init__(self) -> None:
        pass

    async def dispatch_task(self, task: TaskDefinition) -> SessionReference:
        """Not implemented — OpenCode has no programmatic API."""
        raise NotImplementedError("OpenCode programmatic API not yet available")

    async def get_status(self, session_ref: SessionReference) -> SessionReference:
        """Not implemented — OpenCode has no programmatic API."""
        raise NotImplementedError("OpenCode programmatic API not yet available")

    async def cancel(self, session_ref: SessionReference) -> None:
        """Not implemented — OpenCode has no programmatic API."""
        raise NotImplementedError("OpenCode programmatic API not yet available")
