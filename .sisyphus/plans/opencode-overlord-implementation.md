# OpenCode Overlord — MVP v0.1 Implementation Plan

## TL;DR

> **Quick Summary**: Build the core orchestration system that programmatically dispatches tasks to Google Jules (via REST API) and GitHub Copilot (via @mention), manages PR dependency ordering via topological sort, and enqueues PRs for merge via GitHub GraphQL API.
> 
> **Deliverables**:
> - Jules async httpx client with full session lifecycle (create, poll, approve, message)
> - Copilot GitHub Issue/PR trigger wrapper
> - PR dependency DAG with topological merge ordering
> - Merge queue GraphQL integration
> - Orchestrator core wiring all components together
> - CLI entry point and GitHub Actions workflow
> - Full test suite with mocked external APIs
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES — 4 waves
> **Critical Path**: Task 1 → Task 4 → Task 8 → Task 9

---

## Context

### Original Request
Build out the opencode-overlord application — an orchestration system that coordinates AI coding agents (Google Jules, GitHub Copilot, OpenCode) across GitHub repositories. A ralph loop will be used to implement it.

### Interview Summary
**Key Discussions**:
- Jules has a confirmed REST API at `https://jules.googleapis.com/v1alpha/` with API key auth
- Copilot has NO direct API — must use indirect @mention on GitHub Issues/PRs
- OpenCode agent has no clear programmatic API — stubbed for future work
- Merge queue uses GitHub GraphQL (`enqueuePullRequest` mutation), not REST
- PyGithub lacks native merge queue support — must use httpx for GraphQL
- Project uses Python 3.12+, strict mypy, pydantic, httpx, pygithub, structlog

**Research Findings**:
- Jules API confirmed with 6 endpoints: sources, sessions CRUD, approvePlan, activities, sendMessage
- Copilot limited to one PR at a time, branches must start with `copilot/`
- Merge queue GraphQL input: pullRequestId (required), jump (optional priority), expectedHeadOid (optional)
- `graphlib.TopologicalSorter` in Python stdlib handles DAG + cycle detection
- GitHub Actions `GITHUB_TOKEN` is scoped to current repo only — cross-repo needs GitHub App or PAT

### Metis Review
**Identified Gaps** (addressed):
- **Cross-repo auth**: GITHUB_TOKEN insufficient for target repos — plan uses configurable auth (PAT or App token) via pydantic-settings
- **Orchestration state**: Ephemeral GitHub Actions runs lose state — plan uses lightweight state tracking via workflow artifacts
- **OpenCode integration**: No programmatic API — plan stubs it behind AgentClient protocol
- **Multi-agent review**: Too ambitious for MVP — explicitly excluded, trust CI checks
- **Python version**: .python-version 3.14 vs CI 3.12 — plan keeps intentional pattern (dev on latest, CI tests minimum)
- **AgentConfig is plain class**: Must become Pydantic BaseModel — done in Wave 1
- **Missing test mocking**: Need respx or pytest-httpx for HTTP mocking — added to dev dependencies

---

## Work Objectives

### Core Objective
Build a working MVP orchestration system that can dispatch coding tasks to Jules and Copilot, track their progress, compute PR merge ordering from dependency declarations, and enqueue PRs into GitHub's merge queue.

### Concrete Deliverables
- `src/overlord/models.py` — Pydantic models for all domain types
- `src/overlord/config.py` — pydantic-settings configuration
- `src/overlord/exceptions.py` — Typed exception hierarchy
- `src/overlord/protocols.py` — AgentClient Protocol/ABC
- `src/overlord/clients/jules.py` — Jules async httpx client
- `src/overlord/clients/copilot.py` — Copilot GitHub API wrapper
- `src/overlord/clients/opencode.py` — OpenCode stub implementing protocol
- `src/overlord/dag.py` — PR dependency graph with topological sort
- `src/overlord/merge_queue.py` — GitHub GraphQL merge queue client
- `src/overlord/orchestrator.py` — Rewritten orchestrator core
- `src/overlord/cli.py` — CLI entry point (argparse)
- `.github/workflows/orchestrate.yml` — Rewritten workflow
- Full test suite in `tests/` with mocked external APIs

### Definition of Done
- [ ] `uv run pytest tests/ -v` — all tests pass
- [ ] `uv run mypy src/ tests/ --strict` — 0 errors
- [ ] `uv run ruff check src/ tests/` — 0 errors
- [ ] `uv run ruff format --check src/ tests/` — 0 errors
- [ ] Jules client can create session, poll status, approve plan (mocked)
- [ ] Copilot client can create @copilot issue and check for PR (mocked)
- [ ] DAG correctly sorts linear, diamond, and isolated dependency graphs
- [ ] DAG raises on circular dependencies
- [ ] Merge queue client sends well-formed GraphQL mutation (mocked)
- [ ] Orchestrator dispatches tasks and computes merge order end-to-end (mocked)

### Must Have
- All data models use Pydantic BaseModel with strict typing
- All HTTP clients use httpx.AsyncClient with configurable timeout and retry
- All external API calls mocked in tests (zero real HTTP in test suite)
- `graphlib.TopologicalSorter` for DAG (stdlib, not custom)
- pydantic-settings for configuration from environment variables
- Structured error hierarchy (not bare ValueError/RuntimeError)
- structlog for all logging
- Every module passes `mypy --strict` individually
- AgentClient Protocol that Jules, Copilot, and OpenCode all implement

### Must NOT Have (Guardrails)
- **No multi-agent review system** — v0.2 scope. MVP trusts CI status checks.
- **No OpenCode integration beyond stub** — no clear API exists
- **No TypeScript/OpenCode plugin work** — separate workstream
- **No custom webhook/event server** — use GitHub Actions triggers only
- **No dashboard/TUI/UI** — structlog output only
- **No `Any` type in signatures** — strict mypy means no escape hatches
- **No hardcoded URLs/endpoints** — all configurable via pydantic-settings
- **No database or external state store** — use workflow artifacts for MVP state
- **No AI slop**: no excessive comments, no over-abstraction, no generic variable names (data/result/item/temp), no empty try/except blocks
- **No dependencies beyond pyproject.toml** except: `pydantic-settings` (config), `respx` (test mocking), `pyyaml` (dev, YAML validation)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES — pytest + pytest-asyncio configured
- **Automated tests**: YES (tests-after) — each task includes test writing alongside implementation
- **Framework**: pytest + pytest-asyncio + respx (httpx mocking)
- **Every task**: Must pass `uv run pytest -v && uv run mypy src/ tests/ --strict && uv run ruff check src/ tests/`

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Backend/Library**: Use Bash — `uv run pytest`, `uv run mypy`, `uv run ruff`, `uv run python -c "..."`
- **API mocking**: Use `respx` for httpx mocking, `unittest.mock` for PyGithub

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — foundation, no dependencies):
├── Task 1: Dependencies + pyproject.toml update [quick]
├── Task 2: Pydantic models + domain types [unspecified-low]
├── Task 3: Configuration via pydantic-settings [quick]

Wave 2 (After Wave 1 — independent modules, MAX PARALLEL):
├── Task 4: Jules async httpx client [deep]
├── Task 5: Copilot GitHub API wrapper [unspecified-low]
├── Task 6: OpenCode stub client [quick]
├── Task 7: PR Dependency DAG [unspecified-high]

Wave 3 (After Wave 2 — integration):
├── Task 8: Merge queue GraphQL client [unspecified-low]
├── Task 9: Orchestrator core rewrite [deep]

Wave 4 (After Wave 3 — workflow + CLI):
├── Task 10: CLI entry point [quick]
├── Task 11: GitHub Actions workflow rewrite [unspecified-low]

Wave FINAL (After ALL tasks — independent review, 4 parallel):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real QA — full test suite + type check (unspecified-high)
├── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 4 → Task 9 → Task 11 → F1-F4
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 4 (Waves 2)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 2, 3, 4, 5, 6, 7, 8 | 1 |
| 2 | 1 | 4, 5, 6, 7, 8, 9 | 1 |
| 3 | 1 | 9, 10 | 1 |
| 4 | 1, 2 | 9 | 2 |
| 5 | 1, 2 | 9 | 2 |
| 6 | 1, 2 | 9 | 2 |
| 7 | 1, 2 | 9 | 2 |
| 8 | 1, 2 | 9 | 3 |
| 9 | 4, 5, 6, 7, 8 | 10, 11 | 3 |
| 10 | 3, 9 | 11 | 4 |
| 11 | 9, 10 | F1-F4 | 4 |
| F1-F4 | 11 | — | FINAL |

### Agent Dispatch Summary

- **Wave 1**: **3 tasks** — T1 → `quick`, T2 → `unspecified-low`, T3 → `quick`
- **Wave 2**: **4 tasks** — T4 → `deep`, T5 → `unspecified-low`, T6 → `quick`, T7 → `unspecified-high`
- **Wave 3**: **2 tasks** — T8 → `unspecified-low`, T9 → `deep`
- **Wave 4**: **2 tasks** — T10 → `quick`, T11 → `unspecified-low`
- **FINAL**: **4 tasks** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [x] 1. Update Dependencies (pyproject.toml)

  **What to do**:
  - Add `pydantic-settings>=2.0.0` to main dependencies in `pyproject.toml`
  - Add `respx>=0.21.0` to dev dependencies in `pyproject.toml`
  - Add `pyyaml>=6.0` to dev dependencies in `pyproject.toml` (for workflow YAML validation in tests)
  - Run `uv sync --extra dev` to update lockfile
  - Verify all dependencies install cleanly

  **Must NOT do**:
  - Do not add any other dependencies beyond these two
  - Do not change existing dependency version constraints
  - Do not modify build-system or tool configurations

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file edit + lockfile update, trivial task
  - **Skills**: []
    - No specialized skills needed
  - **Skills Evaluated but Omitted**:
    - `git-master`: No git operations needed within this task

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2, 3 in Wave 1)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 2, 3, 4, 5, 6, 7, 8
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - `pyproject.toml:1-41` — Current project config showing existing dependencies list and dev dependencies structure

  **External References**:
  - pydantic-settings: `https://docs.pydantic.dev/latest/concepts/pydantic_settings/`
  - respx: `https://github.com/lundberg/respx` — httpx mock library

  **WHY Each Reference Matters**:
  - `pyproject.toml` — Shows exact format for adding dependencies (lines 7-11 for main, lines 15-19 for dev)

  **Acceptance Criteria**:
  - [ ] `pydantic-settings>=2.0.0` appears in `[project].dependencies`
  - [ ] `respx>=0.21.0` appears in `[project.optional-dependencies].dev`
  - [ ] `pyyaml>=6.0` appears in `[project.optional-dependencies].dev`
  - [ ] `uv sync --extra dev` completes without errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Dependencies install successfully
    Tool: Bash
    Preconditions: pyproject.toml updated with new deps
    Steps:
      1. Run `uv sync --extra dev`
      2. Run `uv run python -c "import pydantic_settings; print(pydantic_settings.__version__)"`
      3. Run `uv run python -c "import respx; print(respx.__version__)"`
      4. Run `uv run python -c "import yaml; print(yaml.__version__)"`
    Expected Result: Both imports succeed and print version numbers
    Failure Indicators: ImportError or ModuleNotFoundError
    Evidence: .sisyphus/evidence/task-1-deps-install.txt
  ```

  **Evidence to Capture:**
  - [ ] task-1-deps-install.txt — output of uv sync and import verification

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(core): add foundation models, config, and exception hierarchy`
  - Files: `pyproject.toml`, `uv.lock`
  - Pre-commit: `uv sync --extra dev`

- [x] 2. Foundation: Pydantic Models, Protocols, and Exceptions

  **What to do**:
  - Create `src/overlord/models.py` with ALL shared domain types:
    - `AgentType` enum: `JULES`, `COPILOT`, `OPENCODE`
    - `AgentConfig(BaseModel)`: name, agent_type (AgentType), endpoint (str | None), api_key (str | None)
    - `TaskDefinition(BaseModel)`: task_id (str), description (str), target_repo (str), target_branch (str = "main"), agent_type (AgentType)
    - `SessionReference(BaseModel)`: session_id (str), agent_type (AgentType), task_id (str), status (str)
    - `PRReference(BaseModel)`: owner (str), repo (str), number (int), node_id (str | None = None), title (str | None = None)
    - `MergeQueueEntry(BaseModel)`: entry_id (str), pr_ref (PRReference), position (int | None = None)
    - `JulesSession(BaseModel)`: session_id (str), status (str), title (str | None = None), plan (str | None = None), pr_url (str | None = None)
    - `JulesActivity(BaseModel)`: activity_id (str), type (str), content (str, timestamp (str)
    - `CopilotStatus(BaseModel)`: issue_number (int), pr_number (int | None = None), status (str)
  - Create `src/overlord/exceptions.py`:
    - `OverlordError(Exception)` — base
    - `AgentError(OverlordError)` — agent-level failures
    - `JulesAPIError(AgentError)` — Jules-specific HTTP errors, with status_code and response_body
    - `CopilotError(AgentError)` — Copilot-specific failures
    - `DependencyCycleError(OverlordError)` — circular PR deps
    - `MergeQueueError(OverlordError)` — merge queue failures
    - `ConfigurationError(OverlordError)` — missing config/secrets
  - Create `src/overlord/protocols.py`:
    - `AgentClient(Protocol)` with methods:
      - `async def dispatch_task(self, task: TaskDefinition) -> SessionReference`
      - `async def get_status(self, session_ref: SessionReference) -> SessionReference`
      - `async def cancel(self, session_ref: SessionReference) -> None`
  - Update `src/overlord/orchestrator.py`:
    - Replace plain `AgentConfig` class with import from `models.py`
    - Remove the old `AgentConfig` class definition
    - Keep `AgentOrchestrator` class but update type hints to use new `AgentConfig`
  - Update `tests/test_orchestrator.py`:
    - Fix imports to use new `AgentConfig` from `models`
    - Ensure existing 2 tests still pass with Pydantic AgentConfig
  - Update `src/overlord/__init__.py`:
    - Export key types: `AgentOrchestrator`, `AgentConfig`, `AgentType`

  **Must NOT do**:
  - Do not use `Any` type anywhere
  - Do not add fields beyond what's listed — MVP scope
  - Do not create abstract base classes (use Protocol instead)
  - Do not add validation beyond Pydantic's built-in

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Multiple files but straightforward Pydantic model definitions
  - **Skills**: []
    - No specialized skills needed
  - **Skills Evaluated but Omitted**:
    - `git-master`: No git operations in this task

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1, 3 in Wave 1 — but needs Task 1 deps first)
  - **Parallel Group**: Wave 1 (after Task 1 completes)
  - **Blocks**: Tasks 4, 5, 6, 7, 8, 9
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - `src/overlord/orchestrator.py:29-42` — Current plain AgentConfig class that must be replaced by Pydantic BaseModel
  - `src/overlord/orchestrator.py:8-27` — AgentOrchestrator class that needs updated imports
  - `src/overlord/__init__.py` — Current exports to update

  **API/Type References**:
  - Jules API creates sessions returning: session_id, status, title, plan fields
  - Copilot creates issues with: issue number, optional PR number
  - `graphlib.TopologicalSorter` needs hashable node types — PRReference must be hashable (use `frozen=True` on Pydantic model)

  **Test References**:
  - `tests/test_orchestrator.py` — Current 2 tests that import AgentConfig and must continue to pass

  **External References**:
  - Pydantic v2: `https://docs.pydantic.dev/latest/concepts/models/`
  - Python Protocol: `https://docs.python.org/3/library/typing.html#typing.Protocol`

  **WHY Each Reference Matters**:
  - `orchestrator.py:29-42` — The old AgentConfig class that must be deleted and replaced with Pydantic version
  - `tests/test_orchestrator.py` — These tests instantiate AgentConfig directly — they WILL BREAK if the constructor signature changes, so verify compatibility
  - PRReference needs `frozen=True` because it'll be used as a dict key and in sets for the DAG

  **Acceptance Criteria**:
  - [ ] `src/overlord/models.py` exists with all listed models
  - [ ] `src/overlord/exceptions.py` exists with all listed exceptions
  - [ ] `src/overlord/protocols.py` exists with AgentClient Protocol
  - [ ] `src/overlord/orchestrator.py` uses imported AgentConfig from models
  - [ ] Old AgentConfig class removed from orchestrator.py
  - [ ] `uv run pytest tests/test_orchestrator.py -v` — 2 tests pass
  - [ ] `uv run mypy src/overlord/models.py src/overlord/exceptions.py src/overlord/protocols.py --strict` — 0 errors
  - [ ] `uv run ruff check src/overlord/` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: All models validate and serialize correctly
    Tool: Bash
    Preconditions: models.py created with all Pydantic models
    Steps:
      1. Run `uv run python -c "
         from overlord.models import AgentConfig, AgentType, TaskDefinition, PRReference
         c = AgentConfig(name='test', agent_type=AgentType.JULES)
         t = TaskDefinition(task_id='t1', description='fix bug', target_repo='owner/repo', agent_type=AgentType.JULES)
         p = PRReference(owner='me', repo='proj', number=42)
         print(c.model_dump_json())
         print(t.model_dump_json())
         print(p.model_dump_json())
         print('ALL OK')
         "`
    Expected Result: Three JSON strings printed followed by "ALL OK"
    Failure Indicators: ImportError, ValidationError, or AttributeError
    Evidence: .sisyphus/evidence/task-2-models-validate.txt

  Scenario: Exception hierarchy is correct
    Tool: Bash
    Preconditions: exceptions.py created
    Steps:
      1. Run `uv run python -c "
         from overlord.exceptions import OverlordError, AgentError, JulesAPIError, DependencyCycleError
         assert issubclass(JulesAPIError, AgentError)
         assert issubclass(AgentError, OverlordError)
         assert issubclass(DependencyCycleError, OverlordError)
         e = JulesAPIError('fail', status_code=401, response_body='unauthorized')
         print(f'status={e.status_code}, body={e.response_body}')
         print('HIERARCHY OK')
         "`
    Expected Result: "status=401, body=unauthorized" then "HIERARCHY OK"
    Failure Indicators: AssertionError or AttributeError
    Evidence: .sisyphus/evidence/task-2-exceptions.txt

  Scenario: Existing tests still pass after AgentConfig migration
    Tool: Bash
    Preconditions: orchestrator.py updated to import from models
    Steps:
      1. Run `uv run pytest tests/test_orchestrator.py -v`
    Expected Result: 2 tests pass, 0 failures
    Failure Indicators: Any test failure or import error
    Evidence: .sisyphus/evidence/task-2-existing-tests.txt
  ```

  **Evidence to Capture:**
  - [ ] task-2-models-validate.txt
  - [ ] task-2-exceptions.txt
  - [ ] task-2-existing-tests.txt

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(core): add foundation models, config, and exception hierarchy`
  - Files: `src/overlord/models.py`, `src/overlord/exceptions.py`, `src/overlord/protocols.py`, `src/overlord/orchestrator.py`, `src/overlord/__init__.py`, `tests/test_orchestrator.py`
  - Pre-commit: `uv run pytest -v && uv run mypy src/ --strict`

- [x] 3. Configuration via pydantic-settings

  **What to do**:
  - Create `src/overlord/config.py` with `OrchestratorConfig(BaseSettings)`:
    - `jules_api_key: str | None = None`
    - `jules_base_url: str = "https://jules.googleapis.com/v1alpha"`
    - `github_token: str` (required — no default)
    - `github_app_token: str | None = None` (for cross-repo access)
    - `default_target_branch: str = "main"`
    - `jules_session_timeout: int = 3600` (seconds)
    - `jules_poll_interval: int = 30` (seconds)
    - `max_concurrent_sessions: int = 5`
    - `merge_queue_enabled: bool = True`
    - `log_level: str = "INFO"`
    - Use `model_config = SettingsConfigDict(env_prefix="OVERLORD_")` for env var prefix
  - Create `tests/test_config.py`:
    - Test loading from environment variables (use `monkeypatch`)
    - Test validation errors for missing required fields
    - Test default values are correct

  **Must NOT do**:
  - Do not hardcode any secrets or tokens
  - Do not read from config files — environment variables only
  - Do not add fields beyond what's listed

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single model definition + basic tests
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2 in Wave 1)
  - **Parallel Group**: Wave 1 (after Task 1 completes)
  - **Blocks**: Tasks 9, 10
  - **Blocked By**: Task 1

  **References**:

  **External References**:
  - pydantic-settings docs: `https://docs.pydantic.dev/latest/concepts/pydantic_settings/`
  - Jules API base URL confirmed: `https://jules.googleapis.com/v1alpha`

  **Pattern References**:
  - `pyproject.toml:7-11` — Shows existing dependencies confirming pydantic is available

  **WHY Each Reference Matters**:
  - pydantic-settings docs — Needed for `BaseSettings`, `SettingsConfigDict`, env_prefix pattern
  - Jules base URL — Hardcoded default for jules_base_url field

  **Acceptance Criteria**:
  - [ ] `src/overlord/config.py` exists with OrchestratorConfig
  - [ ] `uv run python -c "import os; os.environ['OVERLORD_GITHUB_TOKEN']='test'; from overlord.config import OrchestratorConfig; c = OrchestratorConfig(); print(c.github_token)"` prints "test"
  - [ ] `tests/test_config.py` exists with 3+ tests
  - [ ] `uv run pytest tests/test_config.py -v` — all pass
  - [ ] `uv run mypy src/overlord/config.py --strict` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Config loads from environment variables
    Tool: Bash
    Preconditions: config.py created
    Steps:
      1. Run `OVERLORD_GITHUB_TOKEN=ghp_test123 OVERLORD_JULES_API_KEY=key456 uv run python -c "
         from overlord.config import OrchestratorConfig
         c = OrchestratorConfig()
         assert c.github_token == 'ghp_test123'
         assert c.jules_api_key == 'key456'
         assert c.jules_base_url == 'https://jules.googleapis.com/v1alpha'
         assert c.max_concurrent_sessions == 5
         print('CONFIG OK')
         "`
    Expected Result: "CONFIG OK" printed
    Failure Indicators: AssertionError or ValidationError
    Evidence: .sisyphus/evidence/task-3-config-env.txt

  Scenario: Missing required field raises error
    Tool: Bash
    Preconditions: config.py created
    Steps:
      1. Run `uv run python -c "
         try:
             from overlord.config import OrchestratorConfig
             c = OrchestratorConfig()
             print('FAIL: should have raised')
         except Exception as e:
             print(f'CORRECTLY RAISED: {type(e).__name__}')
         "` (without OVERLORD_GITHUB_TOKEN set)
    Expected Result: "CORRECTLY RAISED: ValidationError" printed
    Failure Indicators: "FAIL: should have raised"
    Evidence: .sisyphus/evidence/task-3-config-validation.txt
  ```

  **Evidence to Capture:**
  - [ ] task-3-config-env.txt
  - [ ] task-3-config-validation.txt

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(core): add foundation models, config, and exception hierarchy`
  - Files: `src/overlord/config.py`, `tests/test_config.py`
  - Pre-commit: `uv run pytest tests/test_config.py -v && uv run mypy src/overlord/config.py --strict`

- [x] 4. Jules Async httpx Client

  **What to do**:
  - Create `src/overlord/clients/__init__.py` (empty, makes it a package)
  - Create `src/overlord/clients/jules.py` with `JulesClient` class:
    - Implements `AgentClient` protocol from `protocols.py`
    - Constructor takes `api_key: str`, `base_url: str = "https://jules.googleapis.com/v1alpha"`, `timeout: float = 30.0`
    - Uses `httpx.AsyncClient` internally
    - Implements `async def dispatch_task(self, task: TaskDefinition) -> SessionReference`:
      - POST `/sessions` with body: `{"prompt": task.description, "sourceContext": {"repository": task.target_repo}, "automationMode": "AUTO_CREATE_PR", "title": task.description[:100]}`
      - Header: `X-Goog-Api-Key: {api_key}`
      - Returns `SessionReference` parsed from response
    - Implements `async def get_status(self, session_ref: SessionReference) -> SessionReference`:
      - GET `/sessions/{session_id}`
      - Returns updated `SessionReference` with current status
    - Implements `async def cancel(self, session_ref: SessionReference) -> None`:
      - Placeholder — Jules API may not support cancel; log warning and no-op
    - Additional Jules-specific methods (not in Protocol):
      - `async def approve_plan(self, session_id: str) -> None` — POST `/sessions/{session_id}:approvePlan`
      - `async def get_activities(self, session_id: str) -> list[JulesActivity]` — GET `/sessions/{session_id}/activities`
      - `async def send_message(self, session_id: str, message: str) -> None` — POST `/sessions/{session_id}:sendMessage`
      - `async def list_sources(self) -> list[dict[str, str]]` — GET `/sources`
    - All methods raise `JulesAPIError` with status_code and response_body on non-2xx responses
    - Implement `async def __aenter__` and `__aexit__` for context manager pattern
  - Create `tests/test_jules_client.py`:
    - Use `respx` to mock all httpx calls
    - Test `dispatch_task` happy path — mock POST /sessions returns session_id
    - Test `get_status` — mock GET /sessions/{id} returns status
    - Test `approve_plan` — mock POST /sessions/{id}:approvePlan returns 200
    - Test `get_activities` — mock returns list of activities
    - Test `send_message` — mock returns 200
    - Test 401 error — mock returns 401, assert JulesAPIError raised with status_code=401
    - Test 429 rate limit — mock returns 429, assert JulesAPIError raised
    - Test 500 server error — mock returns 500
    - Test timeout — mock with side_effect=httpx.TimeoutException

  **Must NOT do**:
  - Do not make real HTTP calls — all mocked in tests
  - Do not implement retry/backoff logic (v0.2)
  - Do not add caching
  - Do not use `Any` type

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex async client with multiple methods, error handling, and comprehensive test suite
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: No browser automation needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 5, 6, 7 in Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `src/overlord/protocols.py` (from Task 2) — AgentClient Protocol that JulesClient must implement
  - `src/overlord/models.py` (from Task 2) — JulesSession, JulesActivity, SessionReference, TaskDefinition models
  - `src/overlord/exceptions.py` (from Task 2) — JulesAPIError exception class

  **API/Type References**:
  - Jules REST API base: `https://jules.googleapis.com/v1alpha/`
  - Auth: `X-Goog-Api-Key` header
  - POST `/sessions` — body: `{prompt, sourceContext: {repository}, automationMode, title, requirePlanApproval}`
  - GET `/sessions` — list sessions, supports pageSize param
  - GET `/sessions/{id}` — get session details
  - POST `/sessions/{id}:approvePlan` — approve execution plan
  - GET `/sessions/{id}/activities` — list progress activities
  - POST `/sessions/{id}:sendMessage` — send instruction to agent

  **External References**:
  - httpx async docs: `https://www.python-httpx.org/async/`
  - respx mock library: `https://github.com/lundberg/respx`
  - Jules API reference: `https://developers.google.com/jules/api/reference/rest`

  **WHY Each Reference Matters**:
  - protocols.py — JulesClient MUST implement the 3 Protocol methods exactly (dispatch_task, get_status, cancel)
  - Jules API endpoints — Exact URL paths and request/response formats the client must produce
  - respx — Test mocking library for httpx; examples of route().mock() pattern needed for tests

  **Acceptance Criteria**:
  - [ ] `src/overlord/clients/__init__.py` exists
  - [ ] `src/overlord/clients/jules.py` exists with JulesClient class
  - [ ] JulesClient implements AgentClient protocol (all 3 methods)
  - [ ] 5 Jules-specific methods implemented (approve_plan, get_activities, send_message, list_sources, context manager)
  - [ ] `tests/test_jules_client.py` exists with 9+ tests
  - [ ] `uv run pytest tests/test_jules_client.py -v` — all pass
  - [ ] `uv run mypy src/overlord/clients/ --strict` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Jules client creates session successfully
    Tool: Bash
    Preconditions: jules.py and test file created, respx installed
    Steps:
      1. Run `uv run pytest tests/test_jules_client.py::test_dispatch_task -v`
    Expected Result: PASSED — mock POST /sessions returns valid session, client returns SessionReference
    Failure Indicators: FAILED, respx route not matched, response parse error
    Evidence: .sisyphus/evidence/task-4-jules-dispatch.txt

  Scenario: Jules client handles 401 auth error
    Tool: Bash
    Preconditions: jules.py created with error handling
    Steps:
      1. Run `uv run pytest tests/test_jules_client.py::test_401_unauthorized -v`
    Expected Result: PASSED — JulesAPIError raised with status_code=401
    Failure Indicators: Wrong exception type or missing status_code attribute
    Evidence: .sisyphus/evidence/task-4-jules-401.txt

  Scenario: Full Jules client test suite passes
    Tool: Bash
    Preconditions: All tests written
    Steps:
      1. Run `uv run pytest tests/test_jules_client.py -v --tb=short`
      2. Run `uv run mypy src/overlord/clients/ --strict`
    Expected Result: 9+ tests pass, mypy reports 0 errors
    Failure Indicators: Any test failure or mypy error
    Evidence: .sisyphus/evidence/task-4-jules-full.txt
  ```

  **Evidence to Capture:**
  - [ ] task-4-jules-dispatch.txt
  - [ ] task-4-jules-401.txt
  - [ ] task-4-jules-full.txt

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(clients): add Jules, Copilot, OpenCode clients and PR DAG`
  - Files: `src/overlord/clients/__init__.py`, `src/overlord/clients/jules.py`, `tests/test_jules_client.py`
  - Pre-commit: `uv run pytest tests/test_jules_client.py -v && uv run mypy src/overlord/clients/ --strict`

- [x] 5. Copilot GitHub API Wrapper

  **What to do**:
  - Create `src/overlord/clients/copilot.py` with `CopilotClient` class:
    - Implements `AgentClient` protocol
    - Constructor takes `github_token: str`
    - Uses `PyGithub` (`Github` class) internally
    - Implements `async def dispatch_task(self, task: TaskDefinition) -> SessionReference`:
      - Create a GitHub Issue on `task.target_repo` with title prefixed `[Copilot]`
      - Body includes task description
      - Assign to `copilot` user (GitHub's @copilot bot)
      - Return SessionReference with issue number as session_id
    - Implements `async def get_status(self, session_ref: SessionReference) -> SessionReference`:
      - Check if Copilot opened a PR by searching for PRs from branches starting with `copilot/`
      - Check if the dispatching Issue was closed (indicates completion)
      - Update status: "pending" (issue open, no PR), "in_progress" (PR opened), "completed" (PR merged or issue closed)
    - Implements `async def cancel(self, session_ref: SessionReference) -> None`:
      - Close the GitHub Issue
    - Note: PyGithub is synchronous — wrap calls in `asyncio.to_thread()` for async compatibility
  - Create `tests/test_copilot_client.py`:
    - Mock PyGithub objects using `unittest.mock.MagicMock`
    - Test dispatch creates issue with correct title and assignee
    - Test get_status detects "pending" (no PR)
    - Test get_status detects "in_progress" (copilot/ branch PR exists)
    - Test cancel closes issue
    - Test error when repo not found

  **Must NOT do**:
  - Do not make real GitHub API calls
  - Do not implement review/approval logic
  - Do not handle multiple concurrent Copilot PRs (Copilot only supports one at a time)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Straightforward wrapper around PyGithub with mock tests
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 6, 7 in Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `src/overlord/protocols.py` (from Task 2) — AgentClient Protocol
  - `src/overlord/models.py` (from Task 2) — SessionReference, TaskDefinition, CopilotStatus

  **API/Type References**:
  - PyGithub: `Github.get_repo(full_name).create_issue(title, body, assignee)`
  - PyGithub: `repo.get_pulls(state='open')` to find Copilot PRs
  - Copilot branches always start with `copilot/`

  **External References**:
  - PyGithub docs: `https://pygithub.readthedocs.io/en/stable/`
  - Copilot coding agent: `https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent`

  **WHY Each Reference Matters**:
  - PyGithub API — Exact method signatures for creating issues and searching PRs
  - Copilot coding agent docs — Confirms `copilot/` branch prefix and single-PR limitation

  **Acceptance Criteria**:
  - [ ] `src/overlord/clients/copilot.py` exists with CopilotClient
  - [ ] Implements all 3 AgentClient Protocol methods
  - [ ] `tests/test_copilot_client.py` exists with 5+ tests
  - [ ] `uv run pytest tests/test_copilot_client.py -v` — all pass
  - [ ] `uv run mypy src/overlord/clients/copilot.py --strict` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Copilot dispatch creates GitHub issue
    Tool: Bash
    Preconditions: copilot.py created, PyGithub mocked
    Steps:
      1. Run `uv run pytest tests/test_copilot_client.py::test_dispatch_task -v`
    Expected Result: PASSED — mock issue created with "[Copilot]" title prefix and copilot assignee
    Failure Indicators: Mock assertions fail or wrong issue format
    Evidence: .sisyphus/evidence/task-5-copilot-dispatch.txt

  Scenario: Copilot status detection works
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_copilot_client.py -k "status" -v`
    Expected Result: PASSED — correctly detects pending/in_progress states
    Failure Indicators: Wrong status returned
    Evidence: .sisyphus/evidence/task-5-copilot-status.txt
  ```

  **Evidence to Capture:**
  - [ ] task-5-copilot-dispatch.txt
  - [ ] task-5-copilot-status.txt

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(clients): add Jules, Copilot, OpenCode clients and PR DAG`
  - Files: `src/overlord/clients/copilot.py`, `tests/test_copilot_client.py`
  - Pre-commit: `uv run pytest tests/test_copilot_client.py -v && uv run mypy src/overlord/clients/copilot.py --strict`

- [x] 6. OpenCode Stub Client

  **What to do**:
  - Create `src/overlord/clients/opencode.py` with `OpenCodeClient` class:
    - Implements `AgentClient` protocol
    - All methods raise `NotImplementedError("OpenCode programmatic API not yet available")`
    - Constructor takes no required arguments
    - Include docstring explaining this is a placeholder for future integration
  - Create `tests/test_opencode_client.py`:
    - Test that dispatch_task raises NotImplementedError
    - Test that get_status raises NotImplementedError
    - Test that cancel raises NotImplementedError

  **Must NOT do**:
  - Do not implement any real logic — this is explicitly a stub
  - Do not add CLI invocation or shell-out logic

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 3 methods that all raise NotImplementedError + 3 trivial tests
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 5, 7 in Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `src/overlord/protocols.py` (from Task 2) — AgentClient Protocol to implement
  - `src/overlord/opencode.py` — Current stub file to be replaced by clients/opencode.py

  **WHY Each Reference Matters**:
  - protocols.py — Must implement the exact 3 methods with correct signatures
  - Current opencode.py — Will be superseded; the old file should be removed or repurposed

  **Acceptance Criteria**:
  - [ ] `src/overlord/clients/opencode.py` exists
  - [ ] All 3 Protocol methods raise NotImplementedError
  - [ ] `tests/test_opencode_client.py` exists with 3 tests
  - [ ] `uv run pytest tests/test_opencode_client.py -v` — all pass
  - [ ] `uv run mypy src/overlord/clients/opencode.py --strict` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: OpenCode client correctly raises NotImplementedError
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_opencode_client.py -v`
    Expected Result: 3 tests pass, all confirming NotImplementedError
    Failure Indicators: Any test failure
    Evidence: .sisyphus/evidence/task-6-opencode-stub.txt
  ```

  **Evidence to Capture:**
  - [ ] task-6-opencode-stub.txt

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(clients): add Jules, Copilot, OpenCode clients and PR DAG`
  - Files: `src/overlord/clients/opencode.py`, `tests/test_opencode_client.py`
  - Pre-commit: `uv run pytest tests/test_opencode_client.py -v`

- [x] 7. PR Dependency DAG

  **What to do**:
  - Create `src/overlord/dag.py` with `PRDependencyGraph` class:
    - Uses `graphlib.TopologicalSorter` from Python stdlib
    - `add_pr(pr: PRReference, depends_on: list[PRReference] | None = None) -> None` — add a PR and its dependencies
    - `get_merge_order() -> list[PRReference]` — returns topologically sorted list (merge in this order)
    - `parse_dependencies_from_body(body: str) -> list[PRReference]` — regex parse PR body text for:
      - `Depends-On: #N` — same-repo PR number reference
      - `Depends-On: https://github.com/{owner}/{repo}/pull/{N}` — full URL reference
      - `Requires: {owner}/{repo}#{N}` — shorthand reference
    - `has_cycle() -> bool` — check for circular dependencies
    - `get_ready() -> list[PRReference]` — get PRs with all deps satisfied (ready to merge)
    - Handle cycle detection: catch `graphlib.CycleError` and raise `DependencyCycleError` with the cycle details
  - Create `tests/test_dag.py`:
    - Test empty graph — returns empty list
    - Test single PR, no deps — returns [PR]
    - Test linear chain A→B→C — returns [A, B, C] order
    - Test diamond: A→B, A→C, B→D, C→D — D comes after B and C
    - Test isolated nodes — all returned in some valid order
    - Test cycle detection — A→B, B→A raises DependencyCycleError
    - Test `parse_dependencies_from_body` with each format:
      - `"Depends-On: #42"` → PRReference(number=42)
      - `"Depends-On: https://github.com/owner/repo/pull/42"` → PRReference(owner="owner", repo="repo", number=42)
      - `"Requires: owner/repo#42"` → PRReference(owner="owner", repo="repo", number=42)
    - Test body with no dependencies returns empty list
    - Test body with multiple dependencies returns all
    - Test `get_ready()` returns only PRs whose deps are satisfied

  **Must NOT do**:
  - Do not implement custom DFS — use `graphlib.TopologicalSorter`
  - Do not make GitHub API calls — DAG operates on in-memory data
  - Do not add persistence

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Algorithm + regex parsing + comprehensive test matrix
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 5, 6 in Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `src/overlord/models.py` (from Task 2) — PRReference model (must be hashable/frozen for use as graph node)
  - `src/overlord/exceptions.py` (from Task 2) — DependencyCycleError to raise on cycles

  **External References**:
  - `graphlib.TopologicalSorter`: `https://docs.python.org/3/library/graphlib.html`
  - PR dependency convention from research doc: `docs/research/initial-research.md:73-85` — Depends-On parsing logic

  **WHY Each Reference Matters**:
  - `graphlib` docs — TopologicalSorter API: `add(node, *predecessors)`, `static_order()`, `prepare()`, `get_ready()`, `done(node)`
  - Research doc lines 73-85 — Defines the exact `Depends-On:` and `Requires:` syntax conventions to parse

  **Acceptance Criteria**:
  - [ ] `src/overlord/dag.py` exists with PRDependencyGraph
  - [ ] Uses `graphlib.TopologicalSorter` (not custom DFS)
  - [ ] `tests/test_dag.py` exists with 10+ tests
  - [ ] `uv run pytest tests/test_dag.py -v` — all pass
  - [ ] `uv run mypy src/overlord/dag.py --strict` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Linear dependency chain sorts correctly
    Tool: Bash
    Steps:
      1. Run `uv run python -c "
         from overlord.dag import PRDependencyGraph
         from overlord.models import PRReference
         g = PRDependencyGraph()
         a = PRReference(owner='me', repo='proj', number=1)
         b = PRReference(owner='me', repo='proj', number=2)
         c = PRReference(owner='me', repo='proj', number=3)
         g.add_pr(a)
         g.add_pr(b, depends_on=[a])
         g.add_pr(c, depends_on=[b])
         order = g.get_merge_order()
         nums = [p.number for p in order]
         assert nums == [1, 2, 3], f'Expected [1,2,3] got {nums}'
         print('LINEAR OK')
         "`
    Expected Result: "LINEAR OK"
    Failure Indicators: AssertionError or wrong ordering
    Evidence: .sisyphus/evidence/task-7-dag-linear.txt

  Scenario: Cycle detection raises error
    Tool: Bash
    Steps:
      1. Run `uv run python -c "
         from overlord.dag import PRDependencyGraph
         from overlord.models import PRReference
         from overlord.exceptions import DependencyCycleError
         g = PRDependencyGraph()
         a = PRReference(owner='me', repo='proj', number=1)
         b = PRReference(owner='me', repo='proj', number=2)
         g.add_pr(a, depends_on=[b])
         g.add_pr(b, depends_on=[a])
         try:
             g.get_merge_order()
             print('FAIL: no cycle detected')
         except DependencyCycleError:
             print('CYCLE DETECTED OK')
         "`
    Expected Result: "CYCLE DETECTED OK"
    Failure Indicators: "FAIL: no cycle detected" or wrong exception type
    Evidence: .sisyphus/evidence/task-7-dag-cycle.txt

  Scenario: Parse Depends-On from PR body
    Tool: Bash
    Steps:
      1. Run `uv run python -c "
         from overlord.dag import PRDependencyGraph
         g = PRDependencyGraph()
         body = 'This PR adds auth.\n\nDepends-On: #42\nDepends-On: https://github.com/owner/repo/pull/99'
         deps = g.parse_dependencies_from_body(body)
         assert len(deps) == 2, f'Expected 2 deps, got {len(deps)}'
         assert deps[0].number == 42
         assert deps[1].number == 99
         print('PARSE OK')
         "`
    Expected Result: "PARSE OK"
    Failure Indicators: Wrong count or wrong PR numbers
    Evidence: .sisyphus/evidence/task-7-dag-parse.txt

  Scenario: Full DAG test suite
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_dag.py -v --tb=short`
    Expected Result: 10+ tests pass
    Failure Indicators: Any failure
    Evidence: .sisyphus/evidence/task-7-dag-full.txt
  ```

  **Evidence to Capture:**
  - [ ] task-7-dag-linear.txt
  - [ ] task-7-dag-cycle.txt
  - [ ] task-7-dag-parse.txt
  - [ ] task-7-dag-full.txt

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(clients): add Jules, Copilot, OpenCode clients and PR DAG`
  - Files: `src/overlord/dag.py`, `tests/test_dag.py`
  - Pre-commit: `uv run pytest tests/test_dag.py -v && uv run mypy src/overlord/dag.py --strict`

- [x] 8. Merge Queue GraphQL Client

  **What to do**:
  - Create `src/overlord/merge_queue.py` with `MergeQueueClient` class:
    - Constructor takes `github_token: str`, `base_url: str = "https://api.github.com/graphql"`
    - Uses `httpx.AsyncClient` for GraphQL requests
    - `async def enqueue_pr(self, pr_ref: PRReference, jump: bool = False) -> MergeQueueEntry`:
      - Sends GraphQL mutation `enqueuePullRequest` with input `{pullRequestId: pr_ref.node_id, jump: jump}`
      - Auth header: `Authorization: Bearer {github_token}`
      - Returns `MergeQueueEntry` from response
      - Raises `MergeQueueError` if pr_ref.node_id is None (node_id required for GraphQL)
      - Raises `MergeQueueError` on GraphQL errors
    - `async def get_pr_node_id(self, pr_ref: PRReference) -> str`:
      - GraphQL query to get the node_id from owner/repo/number
      - Query: `{ repository(owner: "{owner}", name: "{repo}") { pullRequest(number: {number}) { id } } }`
      - Returns the node_id string
    - `async def check_merge_queue_enabled(self, owner: str, repo: str, branch: str = "main") -> bool`:
      - Query repository branch protection settings to check if merge queue is configured
      - Returns True/False
    - Implement context manager (`__aenter__`, `__aexit__`)
  - Create `tests/test_merge_queue.py`:
    - Use `respx` to mock GraphQL endpoint
    - Test enqueue_pr happy path — mock returns MergeQueueEntry
    - Test enqueue_pr with jump=True — verify mutation input includes jump
    - Test enqueue_pr with missing node_id — raises MergeQueueError
    - Test get_pr_node_id — mock returns node ID
    - Test GraphQL error response — raises MergeQueueError
    - Test check_merge_queue_enabled — True and False cases

  **Must NOT do**:
  - Do not use REST API for merge queue — GraphQL only
  - Do not implement merge queue monitoring/polling (v0.2)
  - Do not use PyGithub for GraphQL — use httpx directly

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: GraphQL client with typed responses, moderate complexity
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 9 — but Task 9 depends on this, so sequential within Wave 3)
  - **Parallel Group**: Wave 3 (can start as soon as Wave 2 models are ready)
  - **Blocks**: Task 9
  - **Blocked By**: Tasks 1, 2

  **References**:

  **Pattern References**:
  - `src/overlord/clients/jules.py` (from Task 4) — httpx.AsyncClient usage pattern, context manager, error handling
  - `src/overlord/models.py` (from Task 2) — PRReference (needs node_id field), MergeQueueEntry model
  - `src/overlord/exceptions.py` (from Task 2) — MergeQueueError

  **API/Type References**:
  - GraphQL mutation: `enqueuePullRequest(input: {pullRequestId: ID!, jump: Boolean})`
  - Returns: `EnqueuePullRequestPayload` with `mergeQueueEntry` field
  - Auth: `Authorization: Bearer {token}` header
  - Endpoint: `https://api.github.com/graphql`

  **External References**:
  - GitHub GraphQL mutations: `https://docs.github.com/en/graphql/reference/mutations#enqueuepullrequest`
  - EnqueuePullRequestInput: `https://docs.github.com/en/graphql/reference/input-objects#enqueuepullrequestinput`

  **WHY Each Reference Matters**:
  - Jules client pattern — Reuse same httpx setup, error handling, and context manager pattern
  - EnqueuePullRequestInput docs — Confirms exact field names: pullRequestId (required), jump (optional), expectedHeadOid (optional)

  **Acceptance Criteria**:
  - [ ] `src/overlord/merge_queue.py` exists with MergeQueueClient
  - [ ] enqueue_pr sends well-formed GraphQL mutation
  - [ ] `tests/test_merge_queue.py` exists with 6+ tests
  - [ ] `uv run pytest tests/test_merge_queue.py -v` — all pass
  - [ ] `uv run mypy src/overlord/merge_queue.py --strict` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Merge queue enqueue sends correct GraphQL
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_merge_queue.py::test_enqueue_pr -v`
    Expected Result: PASSED — mock GraphQL endpoint receives enqueuePullRequest mutation with correct pullRequestId
    Failure Indicators: respx route not matched or wrong mutation structure
    Evidence: .sisyphus/evidence/task-8-merge-enqueue.txt

  Scenario: Missing node_id raises error
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_merge_queue.py::test_enqueue_missing_node_id -v`
    Expected Result: PASSED — MergeQueueError raised when pr_ref.node_id is None
    Failure Indicators: No error raised
    Evidence: .sisyphus/evidence/task-8-merge-no-nodeid.txt

  Scenario: Full merge queue test suite
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_merge_queue.py -v --tb=short`
      2. Run `uv run mypy src/overlord/merge_queue.py --strict`
    Expected Result: 6+ tests pass, mypy 0 errors
    Evidence: .sisyphus/evidence/task-8-merge-full.txt
  ```

  **Evidence to Capture:**
  - [ ] task-8-merge-enqueue.txt
  - [ ] task-8-merge-no-nodeid.txt
  - [ ] task-8-merge-full.txt

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(orchestrator): add merge queue client and orchestrator core`
  - Files: `src/overlord/merge_queue.py`, `tests/test_merge_queue.py`
  - Pre-commit: `uv run pytest tests/test_merge_queue.py -v && uv run mypy src/overlord/merge_queue.py --strict`

- [ ] 9. Orchestrator Core Rewrite

  **What to do**:
  - Rewrite `src/overlord/orchestrator.py` completely:
    - `AgentOrchestrator` class:
      - Constructor takes `config: OrchestratorConfig`
      - Stores registered agent clients in `dict[str, AgentClient]`
      - `register_client(name: str, client: AgentClient) -> None` — register an agent client
      - `async def dispatch_task(self, task: TaskDefinition) -> SessionReference`:
        - Look up client by `task.agent_type`
        - Call `client.dispatch_task(task)`
        - Log with structlog: task dispatched, agent name, session_id
        - Return SessionReference
      - `async def get_task_status(self, session_ref: SessionReference) -> SessionReference`:
        - Look up client by session_ref.agent_type
        - Call `client.get_status(session_ref)`
        - Return updated SessionReference
      - `async def compute_merge_order(self, owner: str, repo: str, open_prs: list[PRReference]) -> list[PRReference]`:
        - For each PR, parse dependencies from PR body (using DAG's parse method)
        - Build dependency graph
        - Return topological merge order
        - If cycle detected, log error and raise DependencyCycleError
      - `async def enqueue_for_merge(self, pr_ref: PRReference, jump: bool = False) -> MergeQueueEntry`:
        - Use MergeQueueClient to enqueue PR
        - Log the enqueue action
        - Return MergeQueueEntry
      - `async def orchestrate_merge(self, owner: str, repo: str, open_prs: list[PRReference]) -> list[MergeQueueEntry]`:
        - Compute merge order
        - Enqueue each PR in order
        - Return list of MergeQueueEntry results
    - Remove old AgentConfig class (already moved to models.py in Task 2)
    - Remove old stub `trigger_agent` method
  - Update `tests/test_orchestrator.py`:
    - Replace old tests with new ones matching rewritten orchestrator
    - Test dispatch_task routes to correct client (mock clients)
    - Test compute_merge_order with known PR bodies (mock PR body text)
    - Test orchestrate_merge calls enqueue in correct order
    - Test unknown agent type raises AgentError
    - Test DependencyCycleError propagation
  - Create `tests/conftest.py`:
    - Shared fixtures: mock_config (OrchestratorConfig with test values), mock_jules_client, mock_copilot_client
    - Environment setup for OVERLORD_GITHUB_TOKEN etc.

  **Must NOT do**:
  - Do not implement multi-agent review consensus
  - Do not add persistent state management
  - Do not make real API calls — all clients mocked in tests
  - Do not build retry/recovery logic (v0.2)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integration of all previous components, complex async orchestration logic, comprehensive test rewrite
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO — depends on all Wave 2 tasks
  - **Parallel Group**: Wave 3 (after Tasks 4-8 complete)
  - **Blocks**: Tasks 10, 11
  - **Blocked By**: Tasks 4, 5, 6, 7, 8

  **References**:

  **Pattern References**:
  - `src/overlord/orchestrator.py:1-42` — Current orchestrator code to be completely rewritten
  - `src/overlord/protocols.py` (Task 2) — AgentClient Protocol — orchestrator dispatches via this interface
  - `src/overlord/clients/jules.py` (Task 4) — JulesClient implementation
  - `src/overlord/clients/copilot.py` (Task 5) — CopilotClient implementation
  - `src/overlord/dag.py` (Task 7) — PRDependencyGraph for merge ordering
  - `src/overlord/merge_queue.py` (Task 8) — MergeQueueClient for enqueue operations

  **API/Type References**:
  - `src/overlord/config.py` (Task 3) — OrchestratorConfig for constructor
  - `src/overlord/models.py` (Task 2) — All model types used by orchestrator

  **WHY Each Reference Matters**:
  - Current orchestrator.py — The file being completely rewritten; understand what exists
  - All client modules — Orchestrator integrates ALL of these; must understand their interfaces
  - DAG module — compute_merge_order delegates to PRDependencyGraph
  - MergeQueueClient — enqueue_for_merge delegates to this

  **Acceptance Criteria**:
  - [ ] `src/overlord/orchestrator.py` completely rewritten with new AgentOrchestrator
  - [ ] Old AgentConfig class and trigger_agent method removed
  - [ ] `tests/test_orchestrator.py` rewritten with new test cases
  - [ ] `tests/conftest.py` created with shared fixtures
  - [ ] `uv run pytest tests/ -v` — ALL tests pass (entire suite, not just orchestrator)
  - [ ] `uv run mypy src/ tests/ --strict` — 0 errors
  - [ ] `uv run ruff check src/ tests/` — 0 errors

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Dispatch routes to correct agent client
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_orchestrator.py::test_dispatch_to_jules -v`
    Expected Result: PASSED — Jules mock client's dispatch_task called with correct TaskDefinition
    Failure Indicators: Wrong client called or wrong arguments
    Evidence: .sisyphus/evidence/task-9-dispatch-routing.txt

  Scenario: Merge ordering works end-to-end
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_orchestrator.py::test_compute_merge_order -v`
    Expected Result: PASSED — Given PRs with Depends-On bodies, returns correct topological order
    Failure Indicators: Wrong order or missing PRs
    Evidence: .sisyphus/evidence/task-9-merge-order.txt

  Scenario: Full test suite passes (ALL modules)
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/ -v --tb=short`
      2. Run `uv run mypy src/ tests/ --strict`
      3. Run `uv run ruff check src/ tests/`
    Expected Result: All tests pass (25+), mypy 0 errors, ruff 0 errors
    Failure Indicators: Any failure, error, or warning
    Evidence: .sisyphus/evidence/task-9-full-suite.txt
  ```

  **Evidence to Capture:**
  - [ ] task-9-dispatch-routing.txt
  - [ ] task-9-merge-order.txt
  - [ ] task-9-full-suite.txt

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(orchestrator): add merge queue client and orchestrator core`
  - Files: `src/overlord/orchestrator.py`, `tests/test_orchestrator.py`, `tests/conftest.py`
  - Pre-commit: `uv run pytest tests/ -v && uv run mypy src/ tests/ --strict && uv run ruff check src/ tests/`

- [ ] 10. CLI Entry Point

  **What to do**:
  - Create `src/overlord/cli.py`:
    - Uses `argparse` for CLI parsing
    - Subcommands:
      - `dispatch` — dispatch a task to an agent
        - `--agent` (required): jules, copilot
        - `--repo` (required): target repo (owner/repo format)
        - `--task` (required): task description string
        - `--branch` (optional, default: main): target branch
      - `status` — check status of a session
        - `--session-id` (required): session reference ID
        - `--agent` (required): agent type
      - `merge-order` — compute merge order for open PRs
        - `--repo` (required): target repo
      - `enqueue` — enqueue a PR for merge
        - `--repo` (required): target repo
        - `--pr` (required): PR number
        - `--jump` (optional flag): add to front of queue
    - `async def main(args: argparse.Namespace) -> int`:
      - Loads `OrchestratorConfig` from environment
      - Creates appropriate client(s)
      - Executes the subcommand
      - Returns 0 on success, 1 on error
      - Uses structlog for output
    - Entry point: `def cli() -> None` that calls `asyncio.run(main(parse_args()))`
  - Add `[project.scripts]` to `pyproject.toml`:
    - `overlord = "overlord.cli:cli"`
  - Create `tests/test_cli.py`:
    - Test parse_args for each subcommand
    - Test dispatch subcommand with mocked orchestrator
    - Test error handling (missing args, unknown agent)

  **Must NOT do**:
  - Do not use click or typer — use argparse (stdlib, no new deps)
  - Do not add interactive prompts
  - Do not print raw output — use structlog

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard argparse CLI, well-defined subcommands
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 11 if Task 11 doesn't depend on CLI script name)
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 11
  - **Blocked By**: Tasks 3, 9

  **References**:

  **Pattern References**:
  - `src/overlord/orchestrator.py` (Task 9) — AgentOrchestrator class the CLI instantiates
  - `src/overlord/config.py` (Task 3) — OrchestratorConfig loaded from env
  - `main.py` — Current entry point (hello world, will be superseded)

  **External References**:
  - argparse: `https://docs.python.org/3/library/argparse.html`

  **WHY Each Reference Matters**:
  - Orchestrator — CLI is a thin wrapper that creates an orchestrator and calls its methods
  - Config — CLI loads config from env vars, then passes to orchestrator

  **Acceptance Criteria**:
  - [ ] `src/overlord/cli.py` exists with 4 subcommands
  - [ ] `[project.scripts]` added to `pyproject.toml`
  - [ ] `tests/test_cli.py` exists with 4+ tests
  - [ ] `uv run pytest tests/test_cli.py -v` — all pass
  - [ ] `uv run mypy src/overlord/cli.py --strict` — 0 errors
  - [ ] `uv run python -m overlord.cli --help` prints usage

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: CLI help shows all subcommands
    Tool: Bash
    Steps:
      1. Run `uv run python -m overlord.cli --help`
    Expected Result: Output contains "dispatch", "status", "merge-order", "enqueue"
    Failure Indicators: Missing subcommands or import errors
    Evidence: .sisyphus/evidence/task-10-cli-help.txt

  Scenario: CLI arg parsing works
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/test_cli.py -v`
    Expected Result: 4+ tests pass
    Failure Indicators: Parse errors or wrong argument values
    Evidence: .sisyphus/evidence/task-10-cli-tests.txt
  ```

  **Evidence to Capture:**
  - [ ] task-10-cli-help.txt
  - [ ] task-10-cli-tests.txt

  **Commit**: YES (groups with Wave 4)
  - Message: `feat(cli): add CLI entry point and rewrite GitHub Actions workflow`
  - Files: `src/overlord/cli.py`, `tests/test_cli.py`, `pyproject.toml`
  - Pre-commit: `uv run pytest tests/test_cli.py -v && uv run mypy src/overlord/cli.py --strict`

- [ ] 11. GitHub Actions Workflow Rewrite

  **What to do**:
  - Rewrite `.github/workflows/orchestrate.yml`:
    - Add `concurrency` group: `concurrency: { group: orchestrate-${{ github.event.inputs.target_repo || github.event.client_payload.target_repo }}, cancel-in-progress: false }`
    - Keep existing triggers: `repository_dispatch` and `workflow_dispatch`
    - Add `pull_request` trigger for merge queue awareness (types: opened, synchronize, closed)
    - Add `merge_group` trigger (types: checks_requested)
    - Add proper secrets in env:
      - `OVERLORD_GITHUB_TOKEN: ${{ secrets.OVERLORD_GITHUB_TOKEN }}`
      - `OVERLORD_JULES_API_KEY: ${{ secrets.JULES_API_KEY }}`
    - Replace inline Python with `uv run python -m overlord.cli dispatch --agent $AGENT --repo $TARGET_REPO --task "$TASK"`
    - Add separate jobs:
      - `dispatch`: triggered by workflow_dispatch/repository_dispatch — runs `overlord.cli dispatch`
      - `merge-order`: triggered by pull_request — runs `overlord.cli merge-order`
    - Add permissions block: `contents: write`, `pull-requests: write`, `issues: write`
    - Keep Python 3.12, uv, checkout steps
  - Remove old stub steps that are now replaced
  - Clean up legacy files:
    - Remove `src/overlord/jules.py` (replaced by `clients/jules.py`)
    - Remove `src/overlord/copilot.py` (replaced by `clients/copilot.py`)
    - Remove `src/overlord/opencode.py` (replaced by `clients/opencode.py`)
    - Keep `main.py` but update to import from new locations

  **Must NOT do**:
  - Do not add cron/schedule triggers — keep event-driven
  - Do not hardcode secrets in workflow file
  - Do not add complex multi-step orchestration in Actions — keep simple dispatch
  - Do not remove the workflow_dispatch trigger (manual dispatch is useful)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: YAML workflow rewrite + cleanup of old stubs
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO — final implementation task
  - **Parallel Group**: Wave 4 (after Task 10)
  - **Blocks**: F1-F4 (final verification)
  - **Blocked By**: Tasks 9, 10

  **References**:

  **Pattern References**:
  - `.github/workflows/orchestrate.yml:1-83` — Current workflow to be rewritten
  - `src/overlord/cli.py` (Task 10) — CLI entry point that workflow invokes
  - `src/overlord/jules.py`, `src/overlord/copilot.py`, `src/overlord/opencode.py` — Old stub files to delete

  **External References**:
  - GitHub Actions concurrency: `https://docs.github.com/en/actions/using-jobs/using-concurrency`
  - merge_group event: `https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#merge_group`

  **WHY Each Reference Matters**:
  - Current workflow — Must understand existing trigger structure to preserve backward compat
  - CLI module — Workflow delegates to CLI, must match subcommand names
  - Old stub files — Must be cleaned up to avoid import confusion

  **Acceptance Criteria**:
  - [ ] `.github/workflows/orchestrate.yml` rewritten with concurrency, proper secrets, CLI invocation
  - [ ] Old stub files removed: `src/overlord/jules.py`, `src/overlord/copilot.py`, `src/overlord/opencode.py`
  - [ ] `main.py` updated to import from new locations
  - [ ] `uv run pytest tests/ -v` — ALL tests still pass after cleanup
  - [ ] `uv run mypy src/ tests/ --strict` — 0 errors
  - [ ] `uv run ruff check src/ tests/` — 0 errors
  - [ ] Workflow YAML is syntactically valid (check with `python -c "import yaml; yaml.safe_load(open('.github/workflows/orchestrate.yml'))"`)

  **QA Scenarios (MANDATORY):**

  ```
  Scenario: Full test suite passes after cleanup
    Tool: Bash
    Steps:
      1. Run `uv run pytest tests/ -v --tb=short`
      2. Run `uv run mypy src/ tests/ --strict`
      3. Run `uv run ruff check src/ tests/`
      4. Run `uv run ruff format --check src/ tests/`
    Expected Result: All tests pass, mypy 0 errors, ruff clean
    Failure Indicators: Import errors from old module paths
    Evidence: .sisyphus/evidence/task-11-full-suite-final.txt

  Scenario: Old stub files removed
    Tool: Bash
    Steps:
      1. Run `test ! -f src/overlord/jules.py && echo 'jules.py removed OK'`
      2. Run `test ! -f src/overlord/copilot.py && echo 'copilot.py removed OK'`
      3. Run `test ! -f src/overlord/opencode.py && echo 'opencode.py removed OK'`
    Expected Result: All three print "removed OK"
    Failure Indicators: File still exists
    Evidence: .sisyphus/evidence/task-11-cleanup.txt

  Scenario: Workflow YAML is valid
    Tool: Bash
    Steps:
      1. Run `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/orchestrate.yml')); print('YAML VALID')"`
    Expected Result: "YAML VALID"
    Failure Indicators: YAML parse error
    Evidence: .sisyphus/evidence/task-11-workflow-valid.txt
  ```

  **Evidence to Capture:**
  - [ ] task-11-full-suite-final.txt
  - [ ] task-11-cleanup.txt
  - [ ] task-11-workflow-valid.txt

  **Commit**: YES (groups with Wave 4)
  - Message: `feat(cli): add CLI entry point and rewrite GitHub Actions workflow`
  - Files: `.github/workflows/orchestrate.yml`, `main.py`, deleted: `src/overlord/jules.py`, `src/overlord/copilot.py`, `src/overlord/opencode.py`
  - Pre-commit: `uv run pytest tests/ -v && uv run mypy src/ tests/ --strict && uv run ruff check src/ tests/`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `uv run mypy src/ tests/ --strict` + `uv run ruff check src/ tests/` + `uv run pytest tests/ -v`. Review all files in `src/overlord/` for: `as any`/`# type: ignore`, empty except blocks, `print()` in prod code, commented-out code, unused imports, `Any` type annotations. Check AI slop: excessive docstrings, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real QA — Full Test Suite + Type Check** — `unspecified-high`
  Start from clean state (`uv sync`). Run EVERY QA scenario from EVERY task — execute exact commands, capture output. Run `uv run pytest tests/ -v --tb=long`. Run `uv run mypy src/ tests/ --strict`. Run `uv run ruff check src/ tests/`. Run `uv run ruff format --check src/ tests/`. Test cross-module imports work. Save all output to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | pytest [N/N] | mypy [PASS/FAIL] | ruff [PASS/FAIL] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual files created. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance: no multi-agent review, no OpenCode beyond stub, no custom webhook server, no TypeScript, no database. Detect unaccounted files. Flag any `Any` type usage.
  Output: `Tasks [N/N compliant] | Creep [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

After each wave completes successfully:
- **Wave 1**: `feat(core): add foundation models, config, and exception hierarchy`
- **Wave 2**: `feat(clients): add Jules, Copilot, OpenCode clients and PR DAG`
- **Wave 3**: `feat(orchestrator): add merge queue client and orchestrator core`
- **Wave 4**: `feat(cli): add CLI entry point and rewrite GitHub Actions workflow`
- **Final**: `chore: final QA pass and cleanup`

Pre-commit check for ALL commits: `uv run pytest tests/ -v && uv run mypy src/ tests/ --strict && uv run ruff check src/ tests/`

---

## Success Criteria

### Verification Commands
```bash
uv sync                                    # Expected: clean install
uv run pytest tests/ -v                    # Expected: all tests pass (15+ tests)
uv run mypy src/ tests/ --strict           # Expected: Success: no issues
uv run ruff check src/ tests/              # Expected: All checks passed!
uv run ruff format --check src/ tests/     # Expected: N files already formatted
uv run python -c "from overlord.orchestrator import AgentOrchestrator; print('OK')"  # Expected: OK
uv run python -c "from overlord.clients.jules import JulesClient; print('OK')"       # Expected: OK
uv run python -c "from overlord.dag import PRDependencyGraph; print('OK')"            # Expected: OK
```

### Final Checklist
- [ ] All "Must Have" items present and verified
- [ ] All "Must NOT Have" items confirmed absent
- [ ] All tests pass with zero failures
- [ ] mypy strict passes with zero errors
- [ ] ruff check and format pass cleanly
- [ ] All deliverable files exist and are properly structured
- [ ] GitHub Actions workflow is syntactically valid
