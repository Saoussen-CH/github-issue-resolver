#!/bin/bash
# Upload skill files to GCS so named agents can mount them at creation time.
# Run this once, and again whenever SKILL.md files change (then recreate agents).
#
# Prerequisites:
#   - gcloud CLI authenticated
#   - GCS_SKILLS_BUCKET set in .env (repo root)
#
# Usage:
#   bash setup/upload_skills.sh

set -euo pipefail

# Load .env from repo root if present
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT/.env" ] && set -a && source "$ROOT/.env" && set +a

BUCKET="${GCS_SKILLS_BUCKET:?Set GCS_SKILLS_BUCKET in .env}"

echo "Uploading skills to gs://$BUCKET ..."

# Resolver agent skill - mounted at /.agent/skills/fix-issue/
gsutil cp target-app/.agents/skills/fix-issue/SKILL.md \
  "gs://$BUCKET/resolver/skills/fix-issue/SKILL.md"

# CD agent skill - mounted at /.agent/skills/deploy/
gsutil cp cd-agent/SKILL.md \
  "gs://$BUCKET/cd-agent/skills/deploy/SKILL.md"

echo ""
echo "Skills uploaded:"
gsutil ls -r "gs://$BUCKET"
echo ""
echo "Note: recreate agents after changing SKILL.md files:"
echo "  uv run python setup/create_agents.py"
