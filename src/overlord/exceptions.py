"""Typed exception hierarchy for the overlord package."""


class OverlordError(Exception):
    pass


class AgentError(OverlordError):
    pass


class JulesAPIError(AgentError):
    def __init__(self, message: str, *, status_code: int, response_body: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CopilotError(AgentError):
    pass


class DependencyCycleError(OverlordError):
    pass


class MergeQueueError(OverlordError):
    pass


class ConfigurationError(OverlordError):
    pass
