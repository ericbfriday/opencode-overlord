# Jules Task Scoping Rules

Sources: https://jules.google/docs/running-tasks/ and https://jules.google/docs/faq/

## Preferred Prompt Shape

Use prompts that are specific and bounded.

Good examples:

- `Add a loading spinner while fetchUserProfile runs`
- `Fix the 500 error while submitting the feedback form`
- `Document the useCache hook with JSDoc`

Avoid:

- `Fix everything`
- `Optimize code`
- `Make this better`

## Operational Limits

- Do not rely on long-lived commands in setup scripts (`npm run dev` and similar are not supported).
- Prefer finite setup actions (`npm install`, `npm test`, build/test commands with clear exit).

## Guardrail for Meandering Work

Jules is strongest at defined work items. Split discovery-heavy work into short checkpoints:

1. Ask for a plan-only pass.
2. Select one concrete change.
3. Launch one scoped session.
4. Repeat with the next concrete change.

