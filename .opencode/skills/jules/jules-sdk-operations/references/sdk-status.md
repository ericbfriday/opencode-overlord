# Jules SDK Status (Official Repository)

Verification date: March 3, 2026 (America/Chicago)
Repository: https://github.com/google-labs-code/jules-sdk
Verified commit: `03df52f95fc86382b4a24ceac5b69eb8c58a68ba`

## Confirmed Official Surface

The repository contains an official TypeScript SDK monorepo with package metadata and usage docs.

Core package:

- `@google/jules-sdk` (package version in repo: `0.1.0`)

Companion packages in the same repo:

- `@google/jules-mcp` (`0.1.0`)
- `@google/jules-merge` (`0.0.3`)
- `@google/jules-fleet` (`0.0.1-experimental.27`)

## Context About Docs

- Jules docs site (`https://jules.google/docs/`) remains the source for REST API contracts.
- The SDK repository provides additional SDK-native semantics (client abstractions, stream/cursor/query APIs, helper classes, and companion tools).

## Update Rule

Before changing SDK behavior in this skill:

1. Re-check latest `google-labs-code/jules-sdk` README and package metadata.
2. Reconcile any changes with REST API docs for endpoint-level truth.
3. Update this status file with new verification date and commit hash.

