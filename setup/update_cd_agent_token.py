"""
Patches the CD agent's MCP tool config with the current GitHub + GCP tokens.
Must run after gcloud auth so ADC is available.
"""
import json
import os
import time
import urllib.request
import subprocess

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
AGENT_ID = os.environ["CD_AGENT_ID"]
GH_TOKEN = os.environ["GH_TOKEN"]

gcp_token = subprocess.run(
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
        {
            "type": "mcp_server",
            "name": "cloudmonitoring",
            "url": "https://monitoring.googleapis.com/mcp",
            "headers": {"Authorization": f"Bearer {gcp_token}"},
        },
        {
            "type": "mcp_server",
            "name": "cloudlogging",
            "url": "https://logging.googleapis.com/mcp",
            "headers": {"Authorization": f"Bearer {gcp_token}"},
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
    "Authorization": f"Bearer {gcp_token}",
}

req = urllib.request.Request(
    url, data=json.dumps(body).encode(), headers=headers, method="PATCH"
)
with urllib.request.urlopen(req) as resp:
    op = json.loads(resp.read())
    op_name = op.get("name", "")
    print(f"PATCH submitted: {op_name}")

op_url = f"https://aiplatform.googleapis.com/v1beta1/{op_name}"
for attempt in range(10):
    time.sleep(3)
    poll_req = urllib.request.Request(
        op_url, headers={"Authorization": f"Bearer {gcp_token}"}
    )
    with urllib.request.urlopen(poll_req) as resp:
        status = json.loads(resp.read())
    if status.get("done"):
        print("CD agent tools updated with current tokens.")
        break
    print(f"Waiting for update... ({attempt + 1}/10)")
else:
    print("Warning: update may still be in progress — proceeding anyway.")
