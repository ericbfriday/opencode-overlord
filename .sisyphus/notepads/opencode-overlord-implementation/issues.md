# Issues — opencode-overlord-implementation

## Known Gotchas (from plan research)
- Task 1: Plan says "two deps" but actually lists THREE: pydantic-settings, respx, pyyaml (non-blocking, just add all three)
- CopilotClient: PyGithub is SYNC — must wrap in asyncio.to_thread() for async compatibility
- MergeQueueClient: MUST use GraphQL, NOT REST API (PyGithub lacks native merge queue support)
- PRReference needs frozen=True for hashability as DAG dict keys
- GITHUB_TOKEN scoped to current repo only — cross-repo needs PAT or App token via OVERLORD_GITHUB_APP_TOKEN
- Python 3.14 in .python-version is INTENTIONAL — CI uses 3.12 minimum
