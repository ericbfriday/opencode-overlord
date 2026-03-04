# Jules SDK Implementation Pattern

Primary references:
- https://github.com/google-labs-code/jules-sdk
- https://jules.google/docs/api/reference/overview
- https://jules.google/docs/api/reference/sessions
- https://jules.google/docs/api/reference/activities
- https://jules.google/docs/api/reference/sources

## Priority Order

1. Prefer official TypeScript SDK APIs from `@google/jules-sdk`.
2. Use REST endpoints directly only when SDK coverage is missing for the required environment.
3. Keep custom wrappers thin and aligned with documented REST contracts.

## Required Behaviors

- Centralize API key handling and fail fast on missing credentials.
- Preserve documented session lifecycle semantics (`awaitingPlanApproval`, `inProgress`, `completed`, `failed`, and related states).
- Treat plan approval and user feedback states as explicit orchestration points.
- Keep generated-file and change-set handling deterministic and auditable.

## Fallback Policy (Non-TypeScript)

- Use `scripts/jules_sdk.py` as a compatibility helper, not as source-of-truth SDK semantics.
- Keep fallback methods limited to documented REST operations.
- Do not invent helper behavior not represented by SDK docs or REST docs.

## Update Policy

1. Diff official SDK repo APIs and README examples.
2. Diff REST docs for endpoint/field changes.
3. Update skill references and smoke-test scripts.
4. Re-validate the skill folder.

