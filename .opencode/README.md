# OpenCode Configuration for Overlord

This configuration ensures the remote OpenCode instance has the oh-my-opencode plugin installed and configured.

## Plugin: oh-my-opencode

The oh-my-opencode plugin enables this repository to orchestrate AI coding agents across your GitHub repositories.

### Installation

To install the oh-my-opencode plugin on your OpenCode instance:

1. Clone this repository
2. Copy `.opencode/config.json` to your OpenCode config directory
3. Restart OpenCode to load the plugin

### Configuration

The plugin configuration in `.opencode/config.json` defines:
- Which agents are enabled (Jules, Copilot, OpenCode)
- How to trigger each agent (GitHub Actions, GitHub API)
- The coordinator repository for orchestration

### Usage

Once configured, you can trigger agent workflows via:
- GitHub Actions (repository_dispatch events)
- Direct API calls to this repository's orchestration endpoints
