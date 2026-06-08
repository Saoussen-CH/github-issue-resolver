import os
import sys
import subprocess
from google import genai

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.environ.get("CLOUD_RUN_REGION", "us-central1")
SERVICE_NAME = os.environ.get("CLOUD_RUN_SERVICE", "target-app")
GH_TOKEN = os.environ["GH_TOKEN"]
CD_AGENT_ID = os.environ["CD_AGENT_ID"]

# GCP access token - expires in 1 hour, fetched fresh on each run.
# Cannot be stored in the agent definition at creation time.
gcp_token = subprocess.check_output(
    ["gcloud", "auth", "print-access-token"]
).decode().strip()

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def deploy(pr_url: str, image_url: str):
    # TODO 1: Build the prompt
    # The CD agent needs everything it cannot know from SKILL.md at runtime:
    # - The PR URL (to read the issue number and post results)
    # - The pre-built container image URL
    # - The GCP access token (expires - cannot be in the agent definition)
    # - Project, region, and service name
    # Tell the agent to follow the canary deploy skill and close the linked issue on success.
    #
    # prompt = ...

    # TODO 2: Call the Interactions API with three MCP servers
    # Use client.interactions.create() with:
    # - agent: CD_AGENT_ID
    # - input: the prompt above
    # - tools: THREE mcp_server entries:
    #     1. GitHub MCP: "https://api.githubcopilot.com/mcp/"
    #        headers: Authorization Bearer GH_TOKEN + X-MCP-Exclude-Tools: delete_file
    #     2. Cloud Monitoring MCP: "https://monitoring.googleapis.com/mcp"
    #        headers: Authorization Bearer gcp_token
    #     3. Cloud Logging MCP: "https://logging.googleapis.com/mcp"
    #        headers: Authorization Bearer gcp_token
    # - stream=True, background=True, store=True (same pattern as resolve.py)
    #
    # Then iterate over the stream and print each event.
    pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: deploy.py <pr_url> <image_url>")
        sys.exit(1)
    deploy(sys.argv[1], sys.argv[2])
