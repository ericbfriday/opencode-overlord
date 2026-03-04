# Jules CLI Reference (Doc-Derived)

Source: https://jules.google/docs/cli/reference and https://jules.google/docs/cli/examples

## Install and Auth

- Install: `npm install -g @google/jules`
- Login: `jules login`
- Logout: `jules logout`

## Help and Environment

- General help: `jules help`
- Command help: `jules remote --help`
- Version: `jules version`
- TUI: `jules`
- Completion: `jules completion bash`

## Remote Session Commands

- List repositories: `jules remote list --repo`
- List sessions: `jules remote list --session`
- Create session: `jules remote new --repo <owner/repo|.> --session "<prompt>"`
- Parallel sessions: `jules remote new --repo <repo> --session "<prompt>" --parallel <n>`
- Pull session results: `jules remote pull --session <session_id>`

## Script Composition Patterns

- From TODO list:
  - `cat TODO.md | while IFS= read -r line; do jules remote new --repo . --session "$line"; done`
- From GitHub issues:
  - `gh issue list --assignee @me --limit 1 --json title | jq -r '.[0].title' | jules remote new --repo .`

