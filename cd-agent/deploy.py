import os
import sys
import subprocess
from google import genai

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.environ.get("CLOUD_RUN_REGION", "us-central1")
SERVICE_NAME = os.environ.get("CLOUD_RUN_SERVICE", "target-app")
GH_TOKEN = os.environ["GH_TOKEN"]
CD_AGENT_ID = os.environ["CD_AGENT_ID"]

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

    # MCP tools are baked into the agent via update_cd_agent_token.py
    # before this script runs — no tools param needed here.
    stream = client.interactions.create(
        agent=CD_AGENT_ID,
        input=prompt,
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
