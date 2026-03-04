#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  jules_api.sh --path <path> [--method <METHOD>] [--query key=value]... [--data <json>] [--dry-run]

Examples:
  jules_api.sh --path /sessions --query pageSize=10
  jules_api.sh --method POST --path /sessions --data '{"prompt":"Add tests"}' --dry-run
USAGE
}

method="GET"
path=""
data=""
dry_run=0
queries=()
base_url="${JULES_API_BASE:-https://jules.googleapis.com/v1alpha}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method)
      method="${2:-}"
      shift 2
      ;;
    --path)
      path="${2:-}"
      shift 2
      ;;
    --query)
      queries+=("${2:-}")
      shift 2
      ;;
    --data)
      data="${2:-}"
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

if [[ -z "$path" ]]; then
  echo "--path is required." >&2
  usage
  exit 2
fi

if [[ "$path" != /* ]]; then
  path="/$path"
fi

query_string=""
if [[ ${#queries[@]} -gt 0 ]]; then
  query_string="?"
  for pair in "${queries[@]}"; do
    if [[ "$query_string" != "?" ]]; then
      query_string+="&"
    fi
    query_string+="$pair"
  done
fi

url="${base_url}${path}${query_string}"

cmd=(curl -sS -X "$method" -H "x-goog-api-key: ${JULES_API_KEY:-}" "$url")
if [[ -n "$data" ]]; then
  cmd+=( -H "Content-Type: application/json" -d "$data" )
fi

if [[ "$dry_run" -eq 1 ]]; then
  printf 'DRY RUN: '
  printf '%q ' "${cmd[@]}"
  printf '\n'
  exit 0
fi

if [[ -z "${JULES_API_KEY:-}" ]]; then
  echo "JULES_API_KEY is required unless --dry-run is used." >&2
  exit 2
fi

"${cmd[@]}"
