#!/usr/bin/env bash
# Tear down all cloud resources created during the managed-issue-resolver workshop.
# Run from the repo root: bash setup/teardown.sh

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "ERROR: $ROOT/.env not found. Fill in .env.example first." >&2
  exit 1
fi

set -a; source "$ROOT/.env"; set +a

PROJECT_ID="$GOOGLE_CLOUD_PROJECT"
BUCKET="$GCS_SKILLS_BUCKET"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_SERVICE:-target-app}"
REPO="$(gh api user --jq '.login')/github-issue-resolver"

echo "=== Teardown: github-issue-resolver ==="
echo "  Project : $PROJECT_ID"
echo "  Bucket  : gs://$BUCKET"
echo "  Service : $SERVICE ($REGION)"
echo "  GH repo : $REPO"
echo ""

# Named agents
echo "Deleting named agents..."
uv run python "$ROOT/setup/delete_agents.py"

# GCS bucket
echo "Deleting GCS bucket..."
gcloud storage rm --recursive "gs://$BUCKET" --project "$PROJECT_ID" 2>/dev/null \
  && echo "  Deleted gs://$BUCKET" \
  || echo "  gs://$BUCKET not found (skipped)"

# Cloud Run service
echo "Deleting Cloud Run service..."
gcloud run services delete "$SERVICE" \
  --region "$REGION" --project "$PROJECT_ID" --quiet 2>/dev/null \
  && echo "  Deleted Cloud Run service: $SERVICE" \
  || echo "  Cloud Run service $SERVICE not found (skipped)"

# Artifact Registry repository
echo "Deleting Artifact Registry repository..."
gcloud artifacts repositories delete managed-issue-resolver \
  --location "$REGION" --project "$PROJECT_ID" --quiet 2>/dev/null \
  && echo "  Deleted Artifact Registry repository" \
  || echo "  Artifact Registry repository not found (skipped)"

# Service account
echo "Deleting service account..."
SA="managed-issue-resolver@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts delete "$SA" \
  --project "$PROJECT_ID" --quiet 2>/dev/null \
  && echo "  Deleted service account: $SA" \
  || echo "  Service account not found (skipped)"

# GitHub secrets
echo "Removing GitHub secrets..."
for SECRET in GCP_SA_KEY GCP_PROJECT_ID CLOUD_RUN_REGION GCS_SKILLS_BUCKET RESOLVER_AGENT_ID CD_AGENT_ID; do
  gh secret delete "$SECRET" --repo "$REPO" 2>/dev/null \
    && echo "  Deleted secret: $SECRET" \
    || echo "  Secret $SECRET not found (skipped)"
done

# GitHub label
echo "Removing GitHub label..."
gh label delete ai-resolve --repo "$REPO" 2>/dev/null \
  && echo "  Deleted label: ai-resolve" \
  || echo "  Label ai-resolve not found (skipped)"

echo ""
echo "=== Teardown complete ==="
echo "The GitHub repo github.com/$REPO still exists. Delete it manually if needed:"
echo "  gh repo delete $REPO --yes"
