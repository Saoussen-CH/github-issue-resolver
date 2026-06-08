---
name: canary-deploy
description: Deploy a pre-built container image to Cloud Run using canary traffic splitting, monitor error rate via the Cloud Monitoring MCP server, and promote or rollback automatically.
---

# Skill: Canary Deploy to Cloud Run

## Trigger
Called with a merged PR URL, a pre-built container image, and GCP credentials.

## Tools available
- bash: gcloud CLI is pre-installed. Authenticate using the access token from the prompt.
- GitHub MCP server: read PR details, post issue comments, close issues.
- Cloud Monitoring MCP server: query Cloud Run metrics for the promote/rollback decision.
- Cloud Logging MCP server: read error log entries for rollback diagnosis only.

## Steps

<!-- TODO: Write the canary deploy workflow. The agent needs to know:
     1. How to authenticate gcloud using the token from the prompt
     2. How to record the current stable revision (critical - rollback needs this)
     3. How to deploy the new image with --no-traffic
     4. How to get the new revision name
     5. How to split traffic: 10% to new, 90% to stable
     6. The monitoring loop: 5 checks, 60 seconds apart, using Cloud Monitoring MCP
        - What metric to query (request_count, grouped by response_code_class)
        - How to compute canary_error_rate and stable_error_rate
        - The verdict table:
            canary_total < 5           -> HOLD
            error_rate > 5% AND > 2x stable -> ROLLBACK
            error_rate <= 5%           -> OK
            two consecutive HOLDs      -> ROLLBACK
     7. Promote path: --to-latest (keeps service in automatic mode)
     8. Rollback path: --to-revisions STABLE_REV=100
     9. How to get the service URL after the decision
    10. How to find the linked issue number from the PR body (look for "Closes #N")
    11. What to post on success (revision name + live URL, then close issue)
    12. What to post on rollback (error rate + log entries from Cloud Logging MCP)
-->

## Critical rules

<!-- TODO: Add the constraints that prevent dangerous deployment patterns.
     Cover: the logging vs monitoring distinction, recording stable rev, issue state on rollback.
-->
