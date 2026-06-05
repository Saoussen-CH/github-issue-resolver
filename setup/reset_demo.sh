#!/bin/bash
# Reset the demo to its broken state so it can be run again from scratch.
#
# What this does:
#   1. Restores the 4 seeded bugs in target-app/utils.py
#   2. Closes any open PRs opened by the resolver agent
#   3. Commits the reset (you push)
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

# 1. Restore the 4 bugs in utils.py
cat > "$ROOT/target-app/utils.py" << 'PYEOF'
TRACKS = ["AI & ML", "Cloud", "Mobile", "Web", "Security"]

SESSIONS = [
    {"id": 1,  "title": "Building Agents with Gemini",       "speaker": "Abi Aryan",          "track": "AI & ML", "day": 1, "time": "09:00", "room": "Hall A", "level": "Beginner"},
    {"id": 2,  "title": "Cloud Run at Scale",                "speaker": "David Goulding",      "track": "Cloud",   "day": 1, "time": "10:00", "room": "Hall B", "level": "Intermediate"},
    {"id": 3,  "title": "Flutter 4.0 Deep Dive",             "speaker": "Mariam Hassan",       "track": "Mobile",  "day": 1, "time": "11:00", "room": "Hall C", "level": "Advanced"},
    {"id": 4,  "title": "Vertex AI in Production",           "speaker": "Eric Schmidt",        "track": "AI & ML", "day": 1, "time": "14:00", "room": "Hall A", "level": "Intermediate"},
    {"id": 5,  "title": "Firebase: What's New",              "speaker": "Sara Robinson",       "track": "Cloud",   "day": 1, "time": "15:00", "room": "Hall B", "level": "Beginner"},
    {"id": 6,  "title": "Chrome DevTools Tips & Tricks",     "speaker": "Jecelyn Yeen",        "track": "Web",     "day": 1, "time": "16:00", "room": "Hall D", "level": "Beginner"},
    {"id": 7,  "title": "Compose Multiplatform",             "speaker": "Lyla Lee",            "track": "Mobile",  "day": 2, "time": "09:00", "room": "Hall C", "level": "Intermediate"},
    {"id": 8,  "title": "LLMs in Production",                "speaker": "Martin Gorner",       "track": "AI & ML", "day": 2, "time": "10:00", "room": "Hall A", "level": "Advanced"},
    {"id": 9,  "title": "Kubernetes Best Practices",         "speaker": "Kelsey Hightower",    "track": "Cloud",   "day": 2, "time": "11:00", "room": "Hall B", "level": "Advanced"},
    {"id": 10, "title": "Web Performance in 2026",           "speaker": "Addy Osmani",         "track": "Web",     "day": 2, "time": "14:00", "room": "Hall D", "level": "Intermediate"},
    {"id": 11, "title": "Security at Google Scale",          "speaker": "Ryan Rix",            "track": "Security","day": 2, "time": "15:00", "room": "Hall E", "level": "Advanced"},
    {"id": 12, "title": "Responsible AI Practices",          "speaker": "Alex Siegman",        "track": "AI & ML", "day": 2, "time": "16:00", "room": "Hall A", "level": "Beginner"},
]


def get_sessions(track=None, day=None, speaker=None):
    sessions = list(SESSIONS)
    if track:
        sessions = filter_by_track(sessions, track)
    if day:
        sessions = filter_by_day(sessions, day)
    if speaker:
        sessions = search_by_speaker(sessions, speaker)
    return sessions


def filter_by_track(sessions, track):
    # BUG 1: normalises the input but sessions store display names as-is.
    # "AI & ML" becomes "ai-and-ml" which never matches "AI & ML".
    normalized = track.lower().replace(" ", "-").replace("&", "and")
    return [s for s in sessions if s["track"] == normalized]


def filter_by_day(sessions, day):
    # BUG 2: sessions store day as int (1, 2) but the param arrives as a string.
    # "1" != 1 in Python - returns empty list for every day.
    return [s for s in sessions if s["day"] == day]


def search_by_speaker(sessions, query):
    # BUG 3: case-sensitive match - "eric" never finds "Eric Schmidt".
    return [s for s in sessions if query in s["speaker"]]


def session_count(sessions):
    # BUG 4: counts from the full SESSIONS list, not the filtered one passed in.
    return len(SESSIONS)
PYEOF

echo "  utils.py restored to buggy state"

# 2. Close any open PRs
echo ""
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

# 3. Commit (user pushes)
echo ""
cd "$ROOT"
git add target-app/utils.py
git diff --cached --quiet && echo "  utils.py already at buggy state, nothing to commit" || \
  git commit -m "chore: reset demo - restore seeded bugs in utils.py"

echo ""
echo "  Push to trigger Cloud Run redeploy:"
echo "    git push origin master"
echo ""

# 4. Redeploy broken app to Cloud Run
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
