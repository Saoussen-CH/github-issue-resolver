#!/bin/bash
# Upload starter agent files to GCS so named agents can mount them at creation time.
# Uploads from starter/ - the files participants fill in during the workshop.
# Run this once after filling in the starter files, and again whenever they change.
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - GCS_SKILLS_BUCKET set in .env (repo root)
#
# Usage:
#   bash setup/upload_skills.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT/.env" ] && set -a && source "$ROOT/.env" && set +a

BUCKET="${GCS_SKILLS_BUCKET:?Set GCS_SKILLS_BUCKET in .env}"

echo "Uploading agent-home directories to gs://$BUCKET ..."
echo "(agent-home/ contains AGENTS.md + skills/ - single mount at /.agent)"
echo ""

# Resolver: AGENTS.md + fix-issue skill → gs://{bucket}/resolver/agent-home/
gsutil cp "$ROOT/starter/target-app/.agents/AGENTS.md" \
  "gs://$BUCKET/resolver/agent-home/AGENTS.md"
gsutil cp "$ROOT/starter/target-app/.agents/skills/fix-issue/SKILL.md" \
  "gs://$BUCKET/resolver/agent-home/skills/fix-issue/SKILL.md"

# CD agent: AGENTS.md + deploy skill → gs://{bucket}/cd-agent/agent-home/
gsutil cp "$ROOT/starter/cd-agent/AGENTS.md" \
  "gs://$BUCKET/cd-agent/agent-home/AGENTS.md"
gsutil cp "$ROOT/starter/cd-agent/SKILL.md" \
  "gs://$BUCKET/cd-agent/agent-home/skills/deploy/SKILL.md"

echo ""
echo "Uploaded:"
gsutil ls -r "gs://$BUCKET"
echo ""
echo "Note: recreate agents after changing SKILL.md or AGENTS.md files:"
echo "  uv run python starter/setup/create_agents.py"
