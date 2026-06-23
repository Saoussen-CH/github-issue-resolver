"""
Patches the resolver agent's MCP tool config with the current GitHub token.
Must run after gcloud auth so ADC is available.
"""
import json
import os
import time
import urllib.request
import urllib.error
import subprocess

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
AGENT_ID = os.environ["RESOLVER_AGENT_ID"]
GH_TOKEN = os.environ["GH_TOKEN"]

# Get GCP access token via gcloud (available after google-github-actions/auth)
token = subprocess.run(
    ["gcloud", "auth", "print-access-token"],
    capture_output=True, text=True, check=True
).stdout.strip()

body = {
    "name": AGENT_ID,
    "tools": [
        {"type": "code_execution"},
        {"type": "google_search"},
        {"type": "url_context"},
        {
            "type": "mcp_server",
            "name": "github",
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {
                "Authorization": f"Bearer {GH_TOKEN}",
                "X-MCP-Exclude-Tools": "delete_file",
            },
        },
    ],
}

url = (
    f"https://aiplatform.googleapis.com/v1beta1"
    f"/projects/{PROJECT_ID}/locations/global/agents/{AGENT_ID}"
    f"?update_mask=tools"
)
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}",
}

req = urllib.request.Request(
    url, data=json.dumps(body).encode(), headers=headers, method="PATCH"
)
with urllib.request.urlopen(req) as resp:
    op = json.loads(resp.read())
    op_name = op.get("name", "")
    print(f"PATCH submitted: {op_name}")

# Poll LRO until done (max 30s)
op_url = f"https://aiplatform.googleapis.com/v1beta1/{op_name}"
for attempt in range(10):
    time.sleep(3)
    poll_req = urllib.request.Request(
        op_url, headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(poll_req) as resp:
        status = json.loads(resp.read())
    if status.get("done"):
        print("Agent tools updated with current GitHub token.")
        break
    print(f"Waiting for update... ({attempt + 1}/10)")
else:
    print("Warning: update may still be in progress — proceeding anyway.")
