"""Shared domain Pydantic models for the overlord package."""

from enum import Enum

from pydantic import BaseModel


class AgentType(Enum):
    """Supported AI agent types."""

    JULES = "jules"
    COPILOT = "copilot"
    OPENCODE = "opencode"


class AgentConfig(BaseModel):
    """Configuration for an AI agent."""

    name: str
    agent_type: AgentType
    endpoint: str | None = None
    api_key: str | None = None


class TaskDefinition(BaseModel):
    """Definition of a task to be dispatched to an agent."""

    task_id: str
    description: str
    target_repo: str
    target_branch: str = "main"
    agent_type: AgentType


class SessionReference(BaseModel):
    """Reference to an active agent session."""

    session_id: str
    agent_type: AgentType
    task_id: str
    status: str


class PRReference(BaseModel, frozen=True):
    """Reference to a GitHub Pull Request (frozen for hashability as DAG nodes)."""

    owner: str
    repo: str
    number: int
    node_id: str | None = None
    title: str | None = None
    body: str | None = None


class MergeQueueEntry(BaseModel):
    """Entry in the merge queue."""

    entry_id: str
    pr_ref: PRReference
    position: int | None = None


class JulesSession(BaseModel):
    """Represents a Jules agent session."""

    session_id: str
    status: str
    title: str | None = None
    plan: str | None = None
    pr_url: str | None = None


class JulesActivity(BaseModel):
    """An activity event from a Jules session."""

    activity_id: str
    type: str
    content: str
    timestamp: str


class CopilotStatus(BaseModel):
    """Status of a Copilot agent task."""

    issue_number: int
    pr_number: int | None = None
    status: str
