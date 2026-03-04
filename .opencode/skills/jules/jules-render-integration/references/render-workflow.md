# Render Integration Workflow

Sources:
- https://jules.google/docs/integrations/
- https://jules.google/docs/integrations/render

## What It Does

The Render integration enables Jules to monitor failed Render deployments for pull requests created by Jules, analyze logs, and push follow-up fixes.

## Prerequisites

- Enable Pull Request Previews in Render.
- Verify GitHub installation permissions for Google Labs Jules.
  - Accept any pending "Review Request" permission update.

## Setup Steps

1. Open Render dashboard.
2. Go to Help menu and open Coding Agents (or open `dashboard.render.com/jules`).
3. Create API key and copy it immediately (shown once).
4. In Jules, open `Settings > Integrations`.
5. Paste Render key and submit.

## Automated Fix Cycle

1. Jules creates a PR from an accepted plan.
2. Render preview build fails.
3. Jules receives failure context and analyzes logs.
4. Jules pushes a fix commit to the same PR branch.
5. You review and merge.

## Explicit Limitation

Jules currently auto-monitors and auto-fixes build failures only for PRs created by Jules.

