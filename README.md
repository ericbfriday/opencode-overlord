# OpenCode Overlord

Orchestration system that coordinates AI coding agents (Google Jules, GitHub Copilot, OpenCode) across GitHub repositories. Dispatches tasks to agents, tracks session status, computes PR merge order via dependency graphs, and enqueues PRs into GitHub's merge queue.

## Setup

```bash
# Install dependencies (requires uv)
uv sync

# Run tests
uv run pytest tests/ -v

# Type check
uv run mypy src/ tests/ --strict

# Lint
uv run ruff check src/ tests/
```

## CLI

Installed as `overlord` via `[project.scripts]` in `pyproject.toml`.

```bash
# Dispatch a task to an agent
overlord dispatch --agent jules --repo owner/repo --task "fix authentication bug" --branch main

# Check session status
overlord status --session-id ses_abc123 --agent jules

# Compute merge order for open PRs (topological sort based on PR body dependencies)
overlord merge-order --repo owner/repo

# Enqueue a PR into GitHub's merge queue
overlord enqueue --repo owner/repo --pr 42 --jump
```

## Environment Variables

All configuration is loaded via `OrchestratorConfig` (pydantic-settings) with the `OVERLORD_` prefix.

| Variable | Required | Default | Description |
|---|---|---|---|
| `OVERLORD_GITHUB_TOKEN` | **Yes** | — | GitHub PAT for API access (PR operations, merge queue, issue creation) |
| `OVERLORD_JULES_API_KEY` | No | `None` | Google Jules API key for task dispatch |
| `OVERLORD_JULES_BASE_URL` | No | `https://jules.googleapis.com/v1alpha` | Jules API base URL |
| `OVERLORD_GITHUB_APP_TOKEN` | No | `None` | GitHub App installation token for cross-repo access |
| `OVERLORD_DEFAULT_TARGET_BRANCH` | No | `main` | Default branch for task dispatch |
| `OVERLORD_JULES_SESSION_TIMEOUT` | No | `3600` | Jules session timeout in seconds |
| `OVERLORD_JULES_POLL_INTERVAL` | No | `30` | Jules polling interval in seconds |
| `OVERLORD_MAX_CONCURRENT_SESSIONS` | No | `5` | Max concurrent agent sessions |
| `OVERLORD_MERGE_QUEUE_ENABLED` | No | `true` | Enable merge queue integration |
| `OVERLORD_LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Local Development

Create a `.env` file (git-ignored) in the project root:

```bash
OVERLORD_GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OVERLORD_JULES_API_KEY=your-jules-api-key
```

## GitHub Actions Secrets

The workflow at `.github/workflows/orchestrate.yml` requires these repository secrets:

| Secret | Required | Maps To |
|---|---|---|
| `OVERLORD_GITHUB_TOKEN` | **Yes** | `OVERLORD_GITHUB_TOKEN` env var (used in dispatch + merge-order jobs) |
| `JULES_API_KEY` | No | `OVERLORD_JULES_API_KEY` env var (used in dispatch job only) |

### Workflow Triggers

- **`repository_dispatch`**: External repos trigger via `trigger-jules`, `trigger-copilot`, `trigger-opencode`, or `trigger-all` event types. Payload: `{ "target_repo": "owner/repo", "task": "description" }`
- **`workflow_dispatch`**: Manual trigger with `agent`, `target_repo`, and `task` inputs
- **`pull_request`**: Runs `merge-order` job on PR open/sync/close
- **`merge_group`**: Responds to merge queue check requests

## Architecture

```
src/overlord/
├── cli.py              # argparse CLI with 4 subcommands
├── config.py           # OrchestratorConfig (pydantic-settings)
├── dag.py              # PRDependencyGraph (graphlib.TopologicalSorter)
├── exceptions.py       # Exception hierarchy (7 classes)
├── merge_queue.py      # MergeQueueClient (GitHub GraphQL API)
├── models.py           # Pydantic models (AgentType, TaskDefinition, PRReference, etc.)
├── orchestrator.py     # AgentOrchestrator (dispatch, status, merge, enqueue)
├── protocols.py        # AgentClient Protocol
├── py.typed            # PEP 561 marker
└── clients/
    ├── jules.py        # JulesClient (httpx async)
    ├── copilot.py      # CopilotClient (PyGithub + asyncio.to_thread)
    └── opencode.py     # OpenCodeClient (stub)
```

### Agent Clients

- **JulesClient**: Async HTTP client (httpx) for Google Jules API. Creates sessions, polls for completion, retrieves activities.
- **CopilotClient**: Wraps PyGithub (synchronous) with `asyncio.to_thread()` for async compatibility. Creates issues to trigger Copilot, checks PR status.
- **OpenCodeClient**: Stub implementation. All methods raise `NotImplementedError`.

### PR Dependency Graph

PRs can declare dependencies in their body using `Depends-On: owner/repo#123` syntax. The `PRDependencyGraph` builds a DAG and computes topological merge order. Cycles are detected and raised as `DependencyCycleError`.

### Merge Queue

Uses GitHub's GraphQL API (`enqueuePullRequest` mutation) — REST API does not support merge queue operations. Supports priority enqueueing via the `jump` parameter.