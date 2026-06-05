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
- Cloud Monitoring MCP server: query Cloud Run metrics (request counts, error rates) for the promote/rollback decision.
- Cloud Logging MCP server: read actual log entries and error messages for rollback diagnosis.

## Steps

1. Set up GCP authentication using the access token from the prompt:
   ```bash
   export CLOUDSDK_AUTH_ACCESS_TOKEN=<gcp_access_token>
   export PROJECT=<project_id>
   export REGION=<region>
   export SERVICE=<service_name>
   export IMAGE=<image_url>
   ```

2. Record the current stable revision before deploying:
   ```bash
   export STABLE_REV=$(gcloud run services describe $SERVICE \
     --region $REGION --project $PROJECT \
     --format "value(status.traffic[0].revisionName)")
   echo "Stable revision: $STABLE_REV"
   ```

3. Deploy the new image as a new revision with no traffic:
   ```bash
   gcloud run deploy $SERVICE \
     --image $IMAGE \
     --region $REGION \
     --project $PROJECT \
     --no-traffic \
     --quiet
   ```

4. Get the new revision name:
   ```bash
   export NEW_REV=$(gcloud run revisions list \
     --service $SERVICE --region $REGION --project $PROJECT \
     --sort-by "~createTime" --limit 1 --format "value(name)")
   echo "New revision: $NEW_REV"
   ```

5. Send 10% of traffic to the new revision:
   ```bash
   gcloud run services update-traffic $SERVICE \
     --region $REGION --project $PROJECT \
     --to-revisions "$NEW_REV=10" --quiet
   echo "Canary live at 10%"
   ```

6. Monitor error rate for 5 minutes (5 checks, 60 seconds apart).

   For each check, wait 60 seconds first:
   ```bash
   sleep 60
   ```

   Then query the Cloud Monitoring MCP server for `run.googleapis.com/request_count`
   for both revisions over the last 2 minutes, grouped by `response_code_class`.

   From the results, compute:
   - `canary_total` = total request count for `$NEW_REV`
   - `canary_5xx` = requests with response_code_class "5xx" for `$NEW_REV`
   - `canary_error_rate` = canary_5xx / canary_total (treat as 0 if canary_total < 5)
   - `stable_error_rate` = same calculation for `$STABLE_REV`

   Apply this verdict table after each check:

   | Condition | Verdict |
   |---|---|
   | canary_total < 5 | HOLD (not enough traffic yet) |
   | canary_error_rate > 0.05 AND canary_error_rate > stable_error_rate * 2 | ROLLBACK |
   | canary_error_rate <= 0.05 | OK |
   | Two consecutive HOLD verdicts | ROLLBACK (no traffic reaching canary) |

   On ROLLBACK: stop immediately and go to step 7b.
   On OK after all 5 checks: go to step 7a.

7. Promote or rollback based on the monitoring verdict:

   **7a. Promote (all checks OK):**
   ```bash
   gcloud run services update-traffic $SERVICE \
     --region $REGION --project $PROJECT \
     --to-latest --quiet
   echo "Promoted to latest (100%)"
   ```

   **7b. Rollback:**
   ```bash
   gcloud run services update-traffic $SERVICE \
     --region $REGION --project $PROJECT \
     --to-revisions "$STABLE_REV=100" --quiet
   echo "Rolled back to $STABLE_REV"
   ```

8. Get the service URL:
   ```bash
   SERVICE_URL=$(gcloud run services describe $SERVICE \
     --region $REGION --project $PROJECT \
     --format "value(status.url)")
   ```

9. Read the PR body using the GitHub MCP server to extract the linked issue number.
   Look for "Closes #N" or "closes #N".
   If no issue number is found, skip steps 10 and 11 entirely.

10. If promoted AND a linked issue was found:
    - Post a comment on the issue using the GitHub MCP server:
      "Fix deployed. Revision: `<NEW_REV>`. Live at: <SERVICE_URL>"
    - Close the issue using the GitHub MCP server.

11. If rolled back AND a linked issue was found:
    - Read the last 5 ERROR log entries for the canary revision using the Cloud Logging MCP server:
      filter: `resource.type="cloud_run_revision" AND resource.labels.revision_name="<NEW_REV>" AND severity>=ERROR`
      time range: last 10 minutes
    - Post a comment on the issue using the GitHub MCP server:
      "Deployment rolled back to `<STABLE_REV>`.
      Canary error rate: <canary_error_rate>% vs stable <stable_error_rate>%.
      Errors seen: <top error messages from the logs>
      PR remains open for investigation."

## Critical rules

- **NEVER use `gcloud logging read` for health checks.** Log ingestion has 30-90 second delay and gives no denominator. Always use the Cloud Monitoring MCP.
- **Always record `STABLE_REV` before deploying.** Rollback is impossible without it.
- **Do NOT close the issue on rollback.** The fix did not reach production.

## Success criteria
- New revision promoted to 100% (or safely rolled back to stable).
- Original issue closed with revision and live URL on promotion.
- Rollback leaves the issue open with a comment explaining what happened.
