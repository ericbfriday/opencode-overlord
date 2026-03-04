# TypeScript SDK API Guide

Primary sources:
- https://github.com/google-labs-code/jules-sdk/blob/main/README.md
- https://github.com/google-labs-code/jules-sdk/tree/main/packages/core/src

## Install and Auth

- Install: `npm i @google/jules-sdk`
- Auth: set `JULES_API_KEY`
- Import: `import { jules } from '@google/jules-sdk'`

## Client Entry Points

- `jules.run(config)`
  - Automated mode.
  - Defaults: `requireApproval=false`, `autoPr=true`.
- `await jules.session(config)`
  - Interactive mode.
  - Defaults: `requireApproval=true`.
- `jules.session(sessionId)`
  - Rehydrate an existing session client.
- `jules.with(options)`
  - Build scoped client configuration.

## Session Controls

- `session.stream()` for async activity iteration.
- `session.waitFor(state)` for lifecycle checkpoints.
- `session.approve()` for pending plan approval.
- `session.ask(prompt)` and `session.send(prompt)` for interaction.
- `session.result()` for final outcome.
- `session.info()` for latest session state.

## Batch and Discovery APIs

- `jules.all(items, mapper, { concurrency, stopOnError, delayMs })`
- `jules.sessions(options)` returns a cursor that is:
  - Promise-like for first page.
  - AsyncIterable for all pages.
- `jules.sources(options)` returns async iterable of sources.
- `jules.sources.get({ github: 'owner/repo' })` resolves one source.

## Query and Cache APIs

- `jules.select(query)` for local cache querying across sessions/activities.
- SDK includes local storage-backed sync/query tooling and schema validation utilities.

## Artifact Helpers

- Change sets, bash output, and media are represented as typed artifacts.
- Utility helpers include parsed diff support (`parsed()` / `parseUnidiff`) and artifact serialization helpers.

