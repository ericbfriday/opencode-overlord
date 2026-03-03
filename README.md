# OpenCode Overlord

Orchestration and coordination logic for GitHub Jules, Copilot, and OpenCode agents across repositories.

## Purpose

This repository houses the logic and GitHub Actions workflows to trigger and coordinate AI coding agents (Google Jules, GitHub Copilot, and OpenCode) for other repositories.

## Structure

```
opencode-overlord/
├── .github/
│   └── workflows/     # GitHub Actions for agent orchestration
├── src/
│   └── overlord/      # Core orchestration logic
├── tests/             # Test suite
└── pyproject.toml     # Project configuration
```

## Setup

```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

## Usage

This repository is designed to be triggered by GitHub Actions from other repositories to coordinate AI agent workflows.

## Agents Supported

- **Google Jules**: Autonomous coding agent
- **GitHub Copilot**: AI pair programmer
- **OpenCode**: Open-source coding assistant (with oh-my-opencode plugin)

## Configuration

See `.github/workflows/` for available workflows and their configuration options.
