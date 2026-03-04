#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  jules_remote_new_safe.sh --repo <repo> --prompt <text> [--parallel <n>] [--dry-run]

Examples:
  jules_remote_new_safe.sh --repo . --prompt "Add unit tests for parser"
  jules_remote_new_safe.sh --repo owner/repo --prompt "Fix flaky auth test" --parallel 2 --dry-run
USAGE
}

repo=""
prompt=""
parallel=""
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --prompt)
      prompt="${2:-}"
      shift 2
      ;;
    --parallel)
      parallel="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$repo" || -z "$prompt" ]]; then
  echo "Both --repo and --prompt are required." >&2
  usage
  exit 2
fi

lower_prompt="$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')"
case "$lower_prompt" in
  "fix everything"|"optimize code"|"make this better")
    echo "Prompt is too broad. Rewrite with a specific, testable outcome." >&2
    exit 2
    ;;
esac

cmd=(jules remote new --repo "$repo" --session "$prompt")
if [[ -n "$parallel" ]]; then
  cmd+=(--parallel "$parallel")
fi

if [[ "$dry_run" -eq 1 ]]; then
  printf 'DRY RUN: '
  printf '%q ' "${cmd[@]}"
  printf '\n'
  exit 0
fi

if ! command -v jules >/dev/null 2>&1; then
  echo "jules CLI is not installed. Install with: npm install -g @google/jules" >&2
  exit 127
fi

"${cmd[@]}"
