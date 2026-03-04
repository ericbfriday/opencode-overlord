# Learnings — opencode-overlord-implementation

## Project Conventions
- Python 3.12+ strict mypy, pydantic v2, httpx, pygithub, structlog
- uv for package management (`uv run`, `uv sync --extra dev`)
- pytest-asyncio with `asyncio_mode = "auto"` 
- ruff for lint+format (line-length=100, py312 target)
- Env prefix: `OVERLORD_` for all config vars
- All files in `src/overlord/` package

## Working Directory
/Users/ericfriday/dev/opencode-overlord

## Key Paths
- src/overlord/__init__.py
- src/overlord/orchestrator.py (42 lines — to be rewritten)
- src/overlord/jules.py, copilot.py, opencode.py (stubs — to be DELETED in Task 11)
- tests/test_orchestrator.py (2 tests — must keep passing)
- pyproject.toml (41 lines — add deps in Task 1)
- .github/workflows/orchestrate.yml (83 lines — to be rewritten)

## Task 1: Update Dependencies (pyproject.toml)

### Completed Actions
- Added `pydantic-settings>=2.0.0` to `[project].dependencies` (main deps)
- Added `respx>=0.21.0` to `[project.optional-dependencies].dev`
- Added `pyyaml>=6.0` to `[project.optional-dependencies].dev`
- Ran `uv sync --extra dev` successfully
- All three packages installed and verified:
  - pydantic-settings==2.13.1
  - respx==0.22.0
  - pyyaml==6.0.3

### Key Findings
- uv resolves and installs dependencies cleanly
- pydantic-settings brings python-dotenv as transitive dependency
- All imports work correctly in the venv
- Evidence saved to `.sisyphus/evidence/task-1-deps-install.txt`

### Next Steps
- Task 2: Create config module with pydantic-settings

## Task 3: Configuration via pydantic-settings

### Completed Actions
- Created `src/overlord/config.py` with `OrchestratorConfig(BaseSettings)`
  - All 11 fields with correct types and defaults
  - `github_token` is required (no default)
  - `env_prefix="OVERLORD_"` for environment variable mapping
  - Passed `uv run mypy src/overlord/config.py --strict` with 0 errors

- Created `tests/test_config.py` with 5 comprehensive tests:
  1. test_load_from_environment_variables — verifies env var loading
  2. test_validation_error_missing_required_field — validates required field enforcement
  3. test_default_values_are_correct — checks all 9 default values
  4. test_overlord_jules_api_key_sets_field — tests optional field mapping
  5. test_overlord_max_concurrent_sessions_parses_as_int — tests int parsing

- All 5 tests pass: `uv run pytest tests/test_config.py -v`

### Key Findings
- pydantic-settings 2.13.1 handles env var loading seamlessly
- `env_prefix="OVERLORD_"` correctly maps OVERLORD_GITHUB_TOKEN → github_token
- Required fields (no default) raise ValidationError when missing
- Type annotations work correctly with Python 3.12+ union syntax (str | None)
- mypy strict mode passes with proper type hints

### Evidence Captured
- `.sisyphus/evidence/task-3-config-env.txt` — env var loading verification
- `.sisyphus/evidence/task-3-config-validation.txt` — validation error verification

### Next Steps
- Task 4: Create orchestrator module with async methods

## Task 2: Pydantic Models, Protocols, and Exceptions

### Completed Actions
- Created `src/overlord/models.py` with 9 Pydantic models: AgentType, AgentConfig, TaskDefinition, SessionReference, PRReference (frozen=True), MergeQueueEntry, JulesSession, JulesActivity, CopilotStatus
- Created `src/overlord/exceptions.py` with typed hierarchy: OverlordError → AgentError → JulesAPIError (with status_code/response_body attrs), CopilotError; OverlordError → DependencyCycleError, MergeQueueError, ConfigurationError
- Created `src/overlord/protocols.py` with AgentClient Protocol (dispatch_task, get_status, cancel)
- Updated `src/overlord/orchestrator.py`: removed plain AgentConfig class, imported from models, added __all__
- Updated `src/overlord/__init__.py`: exports AgentConfig, AgentOrchestrator, AgentType
- Updated `tests/test_orchestrator.py`: imports AgentConfig from overlord.models, uses AgentType.JULES enum value

### Key Findings
- Tests originally used `agent_type="test_type"` (plain string) — must update to `AgentType.JULES` since Pydantic validates enum fields
- `PRReference(frozen=True)` makes it hashable for use as dict keys and in sets (DAG nodes)
- `JulesAPIError.__init__` uses keyword-only args (`*, status_code, response_body`) for clarity
- Protocol methods use `...` as body — valid Python Protocol syntax, passes mypy strict
- `__all__` in orchestrator.py re-exports AgentConfig/AgentType so existing `from overlord.orchestrator import AgentConfig` still works
- mypy strict: 0 errors on all 3 new files
- ruff: 0 errors on entire src/overlord/ package
- Evidence saved to `.sisyphus/evidence/task-2-*.txt`

## Task 6: OpenCode Stub Client

### Completed Actions
- Created `src/overlord/clients/opencode.py` with `OpenCodeClient` stub
  - Implements AgentClient protocol (dispatch_task, get_status, cancel)
  - All 3 methods raise NotImplementedError with clear message
  - Module docstring explains why: OpenCode has no public programmatic API
  - Passed `uv run mypy src/overlord/clients/opencode.py --strict` with 0 errors

- Created `tests/test_opencode_client.py` with 3 comprehensive tests:
  1. test_dispatch_task_raises_not_implemented — verifies dispatch_task raises
  2. test_get_status_raises_not_implemented — verifies get_status raises
  3. test_cancel_raises_not_implemented — verifies cancel raises
  - All 3 tests pass: `uv run pytest tests/test_opencode_client.py -v`
  - asyncio_mode="auto" in pyproject.toml — no @pytest.mark.asyncio needed

### Key Findings
- OpenCodeClient is intentionally a stub — no real API exists yet
- Protocol methods use async/await signature matching AgentClient Protocol
- TaskDefinition and SessionReference models work correctly with AgentType.OPENCODE enum
- Test fixtures create valid model instances with required fields
- Evidence saved to `.sisyphus/evidence/task-6-opencode-stub.txt`

### Next Steps
- Task 4: Create JulesClient with real API integration
- Task 5: Create CopilotClient with real API integration

## Task 5: CopilotClient (GitHub API Wrapper)

### Completed Actions
- Created `src/overlord/clients/__init__.py` (empty package marker)
- Created `src/overlord/clients/copilot.py` with `CopilotClient` implementing AgentClient Protocol
- Created `tests/test_copilot_client.py` with 7 tests (all pass)

### Key Design Decisions
- session_id format: `"owner/repo#issue_number"` — encodes repo context for stateless get_status/cancel
- PyGithub is SYNCHRONOUS — all calls wrapped with `asyncio.to_thread()` for async compatibility
- `dispatch_task`: creates GitHub issue with `[Copilot]` title prefix and `@copilot` body mention
- `get_status`: checks for open PRs with `copilot/` branch prefix → "in_progress"; closed issue → "completed"; else "pending"
- `cancel`: closes the GitHub issue via `issue.edit(state="closed")`
- `UnknownObjectException` from PyGithub is caught and re-raised as `CopilotError`

### Mypy Strict Notes
- `asyncio.to_thread()` infers return type from the callable — no explicit annotation needed
- Inner functions (`_create_issue`, `_check`, `_close_issue`) need explicit return type annotations
- `int(issue.number)` cast needed since PyGithub returns `int` but mypy may not infer it

### Test Patterns
- `unittest.mock.MagicMock` for PyGithub objects (Github, repo, issue, PR)
- `patch("overlord.clients.copilot.Github", return_value=mock_github)` — patch at import site
- `UnknownObjectException(status=404, data={"message": "Not Found"}, headers={})` constructor signature
- asyncio_mode = "auto" — no `@pytest.mark.asyncio` needed, async test functions work directly

### Evidence
- `.sisyphus/evidence/task-5-copilot-dispatch.txt` — dispatch test
- `.sisyphus/evidence/task-5-copilot-status.txt` — status tests (3 scenarios)

## Task 7: PR Dependency DAG

### Completed Actions
- Created `src/overlord/dag.py` with `PRDependencyGraph` class
  - Uses `graphlib.TopologicalSorter` from stdlib (Python 3.9+)
  - 5 public methods: add_pr, get_merge_order, parse_dependencies_from_body, has_cycle, get_ready
  - Catches `graphlib.CycleError` and re-raises as `DependencyCycleError`
  - Passed `uv run mypy src/overlord/dag.py --strict` with 0 errors

- Created `tests/test_dag.py` with 15 tests across 4 test classes:
  - TestGetMergeOrder: empty_graph, single_pr, linear_chain, diamond, isolated_nodes
  - TestCycleDetection: cycle_raises, has_cycle_true, has_cycle_false
  - TestParseDependencies: depends_on_hash, depends_on_url, requires_shorthand, no_deps, multiple_mixed
  - TestGetReady: returns_no_dep_prs, all_have_deps
  - All 15 tests pass: `uv run pytest tests/test_dag.py -v`

### Key Findings
- `graphlib.TopologicalSorter[PRReference]` is generic — mypy strict requires the type parameter
- `ts.static_order()` returns `Iterator[T]` — must wrap in `list()` for return type `list[PRReference]`
- `PRReference(frozen=True)` works seamlessly as dict keys and set members for the graph
- Regex patterns for dependency parsing:
  - `r"Depends-On:\s+#(\d+)"` — same-repo shorthand
  - `r"Depends-On:\s+https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"` — full URL
  - `r"Requires:\s+([^/\s]+)/([^#\s]+)#(\d+)"` — owner/repo#N shorthand
- TopologicalSorter.static_order() gives deterministic order for linear chains
- CycleError message includes the cycle path — useful for debugging

### Evidence
- `.sisyphus/evidence/task-7-dag-linear.txt` — linear chain merge order
- `.sisyphus/evidence/task-7-dag-cycle.txt` — cycle detection + DependencyCycleError
- `.sisyphus/evidence/task-7-dag-parse.txt` — dependency parsing (3 formats)
- `.sisyphus/evidence/task-7-dag-full.txt` — full test suite (15/15 pass)

## Task 4: Jules Async httpx Client

### Completed Actions
- Created `src/overlord/clients/__init__.py` as package marker
- Created `src/overlord/clients/jules.py` with `JulesClient` implementing `AgentClient`
  - Implemented: `dispatch_task`, `get_status`, `cancel`, `approve_plan`, `get_activities`, `send_message`, `list_sources`, `__aenter__`, `__aexit__`
  - Uses `httpx.AsyncClient` with `X-Goog-Api-Key` header and Jules base URL
  - Raises `JulesAPIError` with `status_code` and `response_body` on non-2xx responses
- Created `tests/test_jules_client.py` with 10 async tests using `respx.mock` (9 required + context manager test)

### Key Findings
- `response.json()` from httpx is dynamically typed; `cast(...)` keeps strict typing clean in client implementation
- For `basedpyright` diagnostics in this environment, severity `error` is clean on changed files while import-stub warnings can still appear at warning level for `src/` package imports
- `asyncio_mode = "auto"` works as expected; async tests run without `@pytest.mark.asyncio`

### Evidence
- `.sisyphus/evidence/task-4-jules-dispatch.txt` — `test_dispatch_task` pass
- `.sisyphus/evidence/task-4-jules-401.txt` — `test_401_unauthorized` pass
- `.sisyphus/evidence/task-4-jules-full.txt` — full Jules tests + strict mypy pass

## Task 8: MergeQueueClient (GraphQL)

### mypy strict + `dict[str, object]` JSON parsing
- Cannot use `.get()` chains directly on `object` — must isinstance-check each level
- Pattern: `data_field = data.get("data"); if isinstance(data_field, dict): ...`
- `cast()` from jules.py works too but isinstance is safer for strict mode without `Any`

### respx 0.22.0 patterns
- `with respx.mock:` context manager — works cleanly with async tests
- `route = respx.post(url).mock(...)` then `route.calls.last.request.content` to inspect sent body
- `json.loads(route.calls.last.request.content)` to verify GraphQL variables

### GraphQL response structure
- Always check `"errors"` key first before accessing `"data"`
- `check_merge_queue_enabled` returns `False` on HTTP error or GraphQL errors (non-raising)
- `enqueue_pr` and `get_pr_node_id` raise `MergeQueueError` on errors

### asyncio_mode = "auto"
- No `@pytest.mark.asyncio` needed — all `async def test_*` auto-detected
- Python 3.14 + anyio 4.12.1 + asyncio-1.3.0 confirmed working

### Context manager pattern
- `__aenter__` returns `self`, `__aexit__` calls `await self._client.aclose()`
- `del exc_type, exc, tb` pattern from JulesClient to suppress unused-arg warnings

## Task 9: Orchestrator Core Rewrite

### Completed Actions
- Rewrote `src/overlord/orchestrator.py` to a new `AgentOrchestrator(config: OrchestratorConfig)` API
  - Added client registry via `register_client(name, client)`
  - Added async methods: `dispatch_task`, `get_task_status`, `compute_merge_order`, `enqueue_for_merge`, `orchestrate_merge`
  - Removed legacy `register_agent` / `trigger_agent` flow
- Rewrote `tests/test_orchestrator.py` with 7 async tests covering routing, unknown agents, status delegation, merge ordering, enqueue behavior, and orchestration ordering
- Added `tests/conftest.py` shared fixtures for config and protocol-based mock clients
- Updated legacy config helper modules (`src/overlord/jules.py`, `src/overlord/copilot.py`, `src/overlord/opencode.py`) to import `AgentConfig`/`AgentType` from `overlord.models` (not `overlord.orchestrator`)

### Key Findings
- `OrchestratorConfig` is a `BaseSettings` with required `github_token`; static analyzers in strict mode need explicit constructor args even when env vars are set at runtime
- `AgentClient` protocol mocking works reliably with `MagicMock(spec=AgentClient)` + `AsyncMock` methods and explicit `isinstance(..., AsyncMock)` checks in tests for typed assertion helpers
- `PRReference` immutability (`frozen=True`) keeps set comparisons and DAG graph-node behavior deterministic and simple in tests
- `structlog.get_logger()` benefits from explicit `FilteringBoundLogger` annotations to keep LSP diagnostics clean in strict environments

### Evidence
- `.sisyphus/evidence/task-9-dispatch-routing.txt`
- `.sisyphus/evidence/task-9-merge-order.txt`
- `.sisyphus/evidence/task-9-full-suite.txt`

## Task 11: Workflow rewrite + stub cleanup

- Old stubs (jules.py, copilot.py, opencode.py) were safe to delete — confirmed not imported anywhere
- `main.py` updated to import `AgentOrchestrator` from `overlord.orchestrator`
- New workflow uses two jobs: `dispatch` (workflow_dispatch/repository_dispatch) and `merge-order` (pull_request)
- `concurrency` group uses `||` fallback chain for target_repo across event types
- `cancel-in-progress: false` — important for merge operations to not cancel in-flight work
- YAML validated with `uv run python -c "import yaml; yaml.safe_load(...)"` (system `python` not in PATH)
- mypy strict: 23 source files, 0 errors after stub deletion
- All 69 tests still pass after cleanup
