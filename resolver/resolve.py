import os
import sys
from google import genai

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
GH_TOKEN = os.environ["GH_TOKEN"]
REPO_URL = os.environ["REPO_URL"]
RESOLVER_AGENT_ID = os.environ["RESOLVER_AGENT_ID"]

# genai client authenticates via ADC set by google-github-actions/auth@v2
client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def resolve(issue_url: str):
    auth_repo_url = REPO_URL.replace("https://", f"https://x-access-token:{GH_TOKEN}@")

    prompt = (
        f"Resolve this GitHub issue: {issue_url}\n"
        f"Repository clone URL (authenticated): {auth_repo_url}\n\n"
        f"Use the GitHub MCP server to read the issue and open the PR. "
        f"Use the authenticated clone URL for git clone and git push."
    )

    # X-MCP-Exclude-Tools removes delete_file from GitHub MCP to avoid
    # conflict with the sandbox's built-in delete_file tool.
    stream = client.interactions.create(
        agent=RESOLVER_AGENT_ID,
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
        ],
        stream=True,
        background=True,
        store=True,
    )

    for event in stream:
        print(str(event)[:300], flush=True)

    print("Agent completed.", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: resolve.py <issue_url>")
        sys.exit(1)
    resolve(sys.argv[1])
