---
name: jules-cli-operations
description: "Operate Jules through the official Jules Tools CLI (`@google/jules`) for terminal-first workflows: install and authenticate the CLI, create/list/pull remote sessions, run shell-composed automation, and review TUI output. Use for requests to run or automate Jules tasks from a terminal, local scripts, or CI-style command chains."
---

# Jules CLI Operations

## Run the Core Workflow

1. Confirm the CLI is available.
2. Authenticate with `jules login` if needed.
3. Translate the user request into one specific, testable session prompt.
4. Start a remote session with `jules remote new`.
5. Monitor with `jules remote list --session`.
6. Pull results from completed sessions with `jules remote pull --session <id>`.

## Keep Task Prompts Scoped

- Convert vague requests into bounded outcomes before launching sessions.
- Prefer prompts that define one feature, bug, or documentation change at a time.
- Reject broad prompts such as `fix everything`, `optimize code`, or `make this better` and rewrite them.
- Avoid long-running setup scripts such as `npm run dev`; prefer finite install/test/build commands.

## Use Bundled Automation

- Use `scripts/jules_remote_new_safe.sh` to enforce required CLI inputs and support dry runs.
- Use `--dry-run` first when composing shell pipelines.

## Load References on Demand

- Load `references/cli-reference.md` for command syntax and scripting patterns.
- Load `references/task-scoping.md` for prompt quality and task-shaping rules.
