"""
Smoke-test the named agents after creation.
Verifies each agent initializes without errors before triggering the full workflow.

Usage:
    uv run python setup/test_agents.py
    (reads GOOGLE_CLOUD_PROJECT from .env)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).parent.parent / ".env")

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
RESOLVER_AGENT_ID = os.environ.get("RESOLVER_AGENT_ID", "managed-issue-resolver")
CD_AGENT_ID = os.environ.get("CD_AGENT_ID", "managed-issue-cd")

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def test_agent(agent_id: str, prompt: str) -> bool:
    print(f"\nTesting: {agent_id}")
    print(f"  Prompt: {prompt[:80]}")
    try:
        stream = client.interactions.create(
            agent=agent_id,
            input=prompt,
            stream=True,
            background=True,
            store=True,
        )
        for event in stream:
            event_type = getattr(event, "event_type", None)
            if event_type == "error":
                error = getattr(event, "error", None)
                print(f"  FAIL: {getattr(error, 'message', event)}")
                return False
            if event_type == "interaction.completed":
                print(f"  PASS: agent initialized and completed successfully")
                return True
            if event_type in ("interaction.created", "interaction.status_update"):
                print(f"  {event_type}")
        print("  PASS: stream completed")
        return True
    except Exception as exc:
        print(f"  FAIL: {exc}")
        return False


results = []

results.append(test_agent(
    RESOLVER_AGENT_ID,
    "Say hello and confirm you can access the GitHub MCP server.",
))

results.append(test_agent(
    CD_AGENT_ID,
    "Say hello and confirm you can access the GitHub, Cloud Monitoring, and Cloud Logging MCP servers.",
))

print("\n" + "="*40)
if all(results):
    print("All agents OK. Ready to trigger the workflow.")
    sys.exit(0)
else:
    print("One or more agents failed. Check the output above.")
    sys.exit(1)
