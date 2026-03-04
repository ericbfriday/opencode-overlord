# Decisions — opencode-overlord-implementation

## Architecture Decisions (from plan)
- graphlib.TopologicalSorter (stdlib) for DAG — NO custom DFS
- httpx for both Jules REST and GitHub GraphQL (NOT PyGithub for GraphQL)
- pydantic-settings with OVERLORD_ env prefix
- respx for httpx mocking in tests
- AgentClient Protocol (NOT ABC)
- PRReference must use frozen=True (hashable for DAG node keys)
- asyncio.to_thread() to wrap synchronous PyGithub calls in CopilotClient
- NO multi-agent review (v0.2 scope)
- NO OpenCode integration beyond stub
- NO database/external state — workflow artifacts for state

## Wave Execution Order
1. Task 1 (pyproject.toml deps) → THEN
2. Tasks 2+3 in parallel → THEN
3. Tasks 4+5+6+7 in parallel → THEN
4. Task 8 then Task 9 (sequential, Wave 3) → THEN
5. Tasks 10+11 in parallel (Wave 4) → THEN
6. F1+F2+F3+F4 in parallel (Final)
