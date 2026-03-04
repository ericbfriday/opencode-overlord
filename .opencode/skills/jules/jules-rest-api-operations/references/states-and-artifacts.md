# Session States and Activity Artifacts

Sources:
- https://jules.google/docs/api/reference/sessions
- https://jules.google/docs/api/reference/activities
- https://jules.google/docs/api/reference/types

## Session State Machine

`QUEUED -> PLANNING -> (AWAITING_PLAN_APPROVAL?) -> IN_PROGRESS -> COMPLETED|FAILED`

Additional states:

- `AWAITING_USER_FEEDBACK`: Jules needs additional input.
- `PAUSED`: Session is paused.

## Automation Mode

- `AUTOMATION_MODE_UNSPECIFIED`: default behavior.
- `AUTO_CREATE_PR`: create pull request when code changes are ready.

## Activity Event Types

- `planGenerated`: includes structured plan steps.
- `planApproved`: marks explicit approval.
- `userMessaged` and `agentMessaged`: conversational coordination.
- `progressUpdated`: in-flight status updates.
- `sessionCompleted` and `sessionFailed`: terminal events.

## Artifact Types

- `changeSet` with `gitPatch` (`baseCommitId`, `unidiffPatch`, `suggestedCommitMessage`).
- `bashOutput` (`command`, `output`, `exitCode`).
- `media` (`mimeType`, binary data payload).

## Practical Polling Pattern

1. Create session.
2. Poll `GET /sessions/{id}` until state is terminal or needs input.
3. Read activities for progress and artifacts.
4. If waiting for plan approval, call `:approvePlan`.
5. Return outputs such as PR URL and title from session outputs.

