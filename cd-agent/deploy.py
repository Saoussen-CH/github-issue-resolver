import os
import sys
import subprocess
from google import genai

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.environ.get("CLOUD_RUN_REGION", "us-central1")
SERVICE_NAME = os.environ.get("CLOUD_RUN_SERVICE", "target-app")
GH_TOKEN = os.environ["GH_TOKEN"]
CD_AGENT_ID = os.environ["CD_AGENT_ID"]

# GCP access token for gcloud commands and Google MCP servers.
gcp_token = subprocess.check_output(
    ["gcloud", "auth", "print-access-token"]
).decode().strip()

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def deploy(pr_url: str, image_url: str):
    prompt = (
        f"Deploy this merged PR to Cloud Run: {pr_url}\n"
        f"Container image (already built): {image_url}\n"
        f"GCP access token: {gcp_token}\n"
        f"Project: {PROJECT_ID}\n"
        f"Region: {REGION}\n"
        f"Service: {SERVICE_NAME}\n\n"
        f"Follow the canary deploy skill. Monitor for 5 minutes, then promote or rollback. "
        f"Close the linked GitHub issue on success."
    )

    # X-MCP-Exclude-Tools removes delete_file from GitHub MCP to avoid
    # conflict with the sandbox's built-in delete_file tool.
    stream = client.interactions.create(
        agent=CD_AGENT_ID,
        input=prompt,
        tools=[
            {
                "type": "mcp_server",
                "url": "https://api.githubcopilot.com/mcp/",
                "name": "github",
                "headers": {
                    "Authorization": f"Bearer {GH_TOKEN}",
                    "X-MCP-Exclude-Tools": "delete_file",
                },
            },
            {
                "type": "mcp_server",
                "url": "https://monitoring.googleapis.com/mcp",
                "name": "cloudmonitoring",
                "headers": {"Authorization": f"Bearer {gcp_token}"},
            },
            {
                "type": "mcp_server",
                "url": "https://logging.googleapis.com/mcp",
                "name": "cloudlogging",
                "headers": {"Authorization": f"Bearer {gcp_token}"},
            },
        ],
        stream=True,
        background=True,
        store=True,
    )

    for event in stream:
        print(str(event)[:300], flush=True)

    print("CD agent completed.", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: deploy.py <pr_url> <image_url>")
        sys.exit(1)
    deploy(sys.argv[1], sys.argv[2])
