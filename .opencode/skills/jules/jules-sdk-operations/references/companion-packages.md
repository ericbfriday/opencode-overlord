# Companion Packages in Jules SDK Monorepo

Source: https://github.com/google-labs-code/jules-sdk

## `@google/jules-mcp`

Use for exposing Jules operations as MCP tools.

Documented tool families include:

- Session management (`create_session`, `list_sessions`, `get_session_state`, `send_reply`)
- Code review context and full diffs
- Local cache querying

## `@google/jules-merge`

Use for merge-conflict detection and CI workflow generation.

Documented capabilities include:

- Session-mode proactive conflict checks
- Git-mode conflict marker extraction
- `init` command for GitHub Actions workflow generation
- MCP exposure for conflict checks/workflow init

## `@google/jules-fleet`

Use for goal-driven continuous orchestration (analyze, dispatch, merge).

Documented capabilities include:

- Goal-file driven analysis
- Scheduled pipeline orchestration
- Sequential merge handling with conflict redispatch options

## Integration Boundary Rule

Use companion packages only when the user explicitly needs those workflows. For normal session orchestration, keep the implementation on `@google/jules-sdk`.

