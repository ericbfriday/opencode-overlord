# Jules REST API Endpoints

Sources:
- https://jules.google/docs/api/reference/overview
- https://jules.google/docs/api/reference/authentication
- https://jules.google/docs/api/reference/sessions
- https://jules.google/docs/api/reference/activities
- https://jules.google/docs/api/reference/sources

## Base and Auth

- Base URL: `https://jules.googleapis.com/v1alpha`
- Auth header: `x-goog-api-key: $JULES_API_KEY`
- Store key in environment variable; do not commit keys.

## Sessions

- `POST /v1alpha/sessions`
  - Create a coding session.
  - Inputs include: `prompt`, `title`, `sourceContext`, `requirePlanApproval`, `automationMode`.
- `GET /v1alpha/sessions`
  - List sessions (`pageSize`, `pageToken`).
- `GET /v1alpha/sessions/{sessionId}`
  - Retrieve full session detail, including outputs when complete.
- `DELETE /v1alpha/sessions/{sessionId}`
  - Delete a session.
- `POST /v1alpha/sessions/{sessionId}:sendMessage`
  - Send mid-session feedback/instructions (`prompt`).
- `POST /v1alpha/sessions/{sessionId}:approvePlan`
  - Approve pending plans for sessions that require manual plan approval.

## Activities

- `GET /v1alpha/sessions/{sessionId}/activities`
  - List activity feed (`pageSize`, `pageToken`).
  - Docs include an example using a `createTime` query for incremental retrieval.
- `GET /v1alpha/sessions/{sessionId}/activities/{activityId}`
  - Retrieve a single activity event.

## Sources

- `GET /v1alpha/sources`
  - List connected repositories (`pageSize`, `pageToken`, `filter`).
- `GET /v1alpha/sources/{sourceId}`
  - Retrieve source details including branches.
- Use source resource names (for example `sources/github-owner-repo`) in `sourceContext` when creating sessions.

## Common Failure Codes

- `400`: invalid request data
- `401`: missing/invalid API key
- `403`: insufficient permissions
- `404`: missing resource
- `429`: rate limiting
- `500`: server-side failure

