#!/bin/bash
# Reset the demo to its broken state so it can be run again from scratch.
#
# What this does:
#   1. Closes any open PRs
#   2. Restores the 4 seeded bugs in target-app/utils.py (from setup/utils_broken.py)
#   3. Commits and pushes the reset
#   4. Redeploys the broken app to Cloud Run
#
# Usage:
#   bash setup/reset_demo.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT/.env" ] && set -a && source "$ROOT/.env" && set +a

PROJECT="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT in .env}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE="${CLOUD_RUN_SERVICE:-target-app}"

echo "Resetting demo..."
echo ""

# 1. Close any open PRs
echo "  Closing open PRs..."
gh pr list --state open --json number,headRefName \
  | python3 -c "
import json, sys, subprocess
prs = json.load(sys.stdin)
for pr in prs:
    subprocess.run(['gh', 'pr', 'close', str(pr['number']), '--delete-branch'], check=False)
    print(f'    Closed PR #{pr[\"number\"]} ({pr[\"headRefName\"]})')
if not prs:
    print('    No open PRs to close')
"

# 2. Restore bugs from the canonical broken file (agent never touches setup/)
echo ""
cp "$ROOT/setup/utils_broken.py" "$ROOT/target-app/utils.py"
echo "  utils.py restored to buggy state"

# 3. Commit and push
echo ""
cd "$ROOT"
git add target-app/utils.py
if git diff --cached --quiet; then
  echo "  utils.py already at buggy state, nothing to commit"
else
  git commit -m "chore: reset demo - restore seeded bugs in utils.py"
  echo "  Pushing reset commit..."
  git push origin master
fi

# 4. Redeploy broken app to Cloud Run (after push so CD agent can't race us)
echo ""
echo "  Redeploying broken app to Cloud Run..."
gcloud run deploy "$SERVICE" \
  --source "$ROOT/target-app/" \
  --region "$REGION" \
  --allow-unauthenticated \
  --project "$PROJECT" \
  --quiet

echo ""
echo "Done. Demo is reset and ready."
echo "Open a new issue with the 'ai-resolve' label to trigger the agent."
