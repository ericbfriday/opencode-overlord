---
name: jules-sdk-operations
description: Implement and maintain integrations with the official Jules TypeScript SDK ecosystem from `google-labs-code/jules-sdk`, including `@google/jules-sdk` plus companion packages (`@google/jules-mcp`, `@google/jules-merge`, `@google/jules-fleet`). Use when requests involve SDK-native session orchestration, stream monitoring, cache/query features, or package-based automation; use REST wrappers only when TypeScript SDK use is not possible.
---

# Jules SDK Operations

## Prefer Official SDK Packages

1. Use `@google/jules-sdk` as the primary integration surface.
2. Use companion packages when relevant:
   - `@google/jules-mcp` for MCP tool exposure.
   - `@google/jules-merge` for conflict detection workflows.
   - `@google/jules-fleet` for scheduled analyze/dispatch/merge orchestration.
3. Use `scripts/jules_sdk.py` only for non-TypeScript or REST-compatibility fallback paths.

## Execute a TypeScript SDK Workflow

1. Install package(s): `npm i @google/jules-sdk`.
2. Configure `JULES_API_KEY` in environment.
3. Pick session mode:
   - Automated: `jules.run(config)` for fire-and-forget runs.
   - Interactive: `await jules.session(config)` for guided workflows.
   - Rehydrate existing session: `jules.session(sessionId)`.
4. Observe progress via `session.stream()` and state gates via `session.waitFor(...)`.
5. Approve plan when needed: `session.approve()`.
6. Finalize with `session.result()` and inspect `generatedFiles()`, `changeSet()`, and PR outputs.

## Use Higher-Level SDK Features

- Use `jules.all(items, mapper, options)` for controlled parallel dispatch.
- Use `jules.sessions(options)` for paginated session cursors.
- Use `jules.sources(...)` and `jules.sources.get({ github: 'owner/repo' })` for source resolution.
- Use `jules.select(query)` to query local session/activity cache.
- Use `jules.with(options)` to create scoped clients (API key, polling, timeout, base URL).

## Load References on Demand

- Load `references/sdk-status.md` for repository verification and versions.
- Load `references/typescript-sdk-api.md` for method-level behavior and defaults.
- Load `references/sdk-design-pattern.md` for implementation policy.
- Load `references/companion-packages.md` for MCP/merge/fleet package usage boundaries.
