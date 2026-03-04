---
name: jules-render-integration
description: Configure and operate the documented Jules Render integration for deployment-failure remediation, including Render API key provisioning, Jules integration setup, and monitoring of automatic fix cycles on Jules-created pull requests. Use for requests involving Render build failures, CI/CD feedback loops, or Continuous AI deployment automation with Jules.
---

# Jules Render Integration

## Execute the Integration Workflow

1. Validate prerequisites in Render and GitHub permissions.
2. Provision a Render API key in the Render Coding Agents flow.
3. Connect that key in Jules at `Settings > Integrations`.
4. Confirm that Jules-created PRs trigger Render previews.
5. Verify automated remediation behavior for failed deployments.

## Keep Scope Aligned to Documented Behavior

- Limit automation expectations to Jules-created PRs.
- Do not claim automatic fixes for non-Jules PRs unless docs change.
- Preserve manual review and merge control after automated commits.

## Use Reference Files

- Load `references/render-workflow.md` for setup and runtime behavior.
- Load `references/continuous-ai-context.md` for how Render fits with suggested and scheduled tasks.
