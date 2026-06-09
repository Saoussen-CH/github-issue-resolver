"""
Create named agents on Agent Platform.
Agents are created with standard tools (code_execution, google_search, url_context).
MCP tools are added at interaction time - this is the confirmed working pattern.

Usage:
    uv run python setup/create_agents.py
    (reads GOOGLE_CLOUD_PROJECT and GCS_SKILLS_BUCKET from .env)
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).parent.parent / ".env")

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
GCS_SKILLS_BUCKET = os.environ["GCS_SKILLS_BUCKET"]

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

_root = Path(__file__).parent.parent

RESOLVER_AGENTS_MD = (_root / "starter/target-app/.agents/AGENTS.md").read_text()
CD_AGENTS_MD = (_root / "starter/cd-agent/AGENTS.md").read_text()


def create_agent(
    agent_id: str,
    description: str,
    system_instruction: str,
    agent_home_gcs_prefix: str,
) -> str:
    try:
        existing = client.agents.get(id=agent_id)
        if existing.id:
            print(f"Agent already exists: {agent_id} (skipping)")
            return agent_id
    except Exception:
        pass

    print(f"Creating agent: {agent_id} ...")
    client.agents.create(
        id=agent_id,
        base_agent="antigravity-preview-05-2026",
        description=description,
        system_instruction=system_instruction,
        tools=[
            {"type": "code_execution"},
            {"type": "google_search"},
            {"type": "url_context"},
        ],
        base_environment={
            "type": "remote",
            "sources": [
                {
                    "type": "gcs",
                    "source": f"gs://{GCS_SKILLS_BUCKET}/{agent_home_gcs_prefix}",
                    "target": "/.agent",
                }
            ],
            "network": {"allowlist": [{"domain": "*"}]},
        },
    )
    for _ in range(12):
        time.sleep(5)
        try:
            agent = client.agents.get(id=agent_id)
            if agent.id:
                print(f"  Ready: {agent_id}")
                return agent_id
        except Exception:
            pass
    print(f"  Warning: {agent_id} may still be provisioning")
    return agent_id


resolver_id = create_agent(
    agent_id="managed-issue-resolver",
    description="Reads a GitHub issue, fixes the bug in the repo, runs tests, opens a PR.",
    system_instruction=RESOLVER_AGENTS_MD,
    agent_home_gcs_prefix="resolver/agent-home",
)

cd_id = create_agent(
    agent_id="managed-issue-cd",
    description="Canary-deploys a fix to Cloud Run, monitors error rate, promotes or rolls back.",
    system_instruction=CD_AGENTS_MD,
    agent_home_gcs_prefix="cd-agent/agent-home",
)

print("")
print("Add these as GitHub Actions secrets:")
print(f"  gh secret set RESOLVER_AGENT_ID --body '{resolver_id}'")
print(f"  gh secret set CD_AGENT_ID --body '{cd_id}'")
