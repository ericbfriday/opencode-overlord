---
name: jules-rest-api-operations
description: Automate Jules using the official Jules REST API (`https://jules.googleapis.com/v1alpha`) with API-key authentication, including creating/listing/deleting sessions, sending follow-up messages, approving plans, reading activities, and resolving source metadata. Use for API-driven orchestration, integrations, service-to-service workflows, or scripted Jules operations outside the CLI.
---

# Jules REST API Operations

## Execute the API Workflow

1. Load API key from environment (`JULES_API_KEY`).
2. Discover source repositories with `GET /v1alpha/sources`.
3. Create a scoped session with `POST /v1alpha/sessions`.
4. Poll session and activity state until terminal outcome.
5. Send follow-up instructions with `:sendMessage` when needed.
6. Approve plans with `:approvePlan` when `requirePlanApproval=true`.
7. Return links and outputs (for example PR URLs) from session results.

## Apply Safety and Reliability Rules

- Keep prompts specific and bounded before creating sessions.
- Use `pageSize` and `pageToken` for list pagination.
- Treat `FAILED` sessions as actionable diagnostics, not silent completion.
- Handle documented error codes (`400`, `401`, `403`, `404`, `429`, `500`) with retries or user-facing remediation.

## Use Bundled Automation

- Use `scripts/jules_api.sh` for consistent authenticated requests.
- Start with `--dry-run` to validate request shape before live API calls.

## Load References on Demand

- Load `references/endpoints.md` for endpoint-level semantics.
- Load `references/states-and-artifacts.md` for lifecycle and activity interpretation.
