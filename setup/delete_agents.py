import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).parent.parent / ".env")

client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location="global")

for aid in ["managed-issue-resolver", "managed-issue-cd"]:
    try:
        client.agents.delete(id=aid)
        print(f"Deleted: {aid}")
    except Exception as e:
        print(f"{aid}: {e}")
