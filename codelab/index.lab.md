---
id: managed-agents-issue-resolver
summary: Build a fully autonomous GitHub issue resolver using the Google Managed Agents API. The platform provisions the sandbox, runs the model, and streams results. You bring two AGENTS.md files, two SKILL.md files, and two GitHub Actions workflows.
status: Draft
authors: Saoussen Chaabnia
categories: AI, Google Cloud, Managed Agents
tags: web
feedback link: https://github.com/googlecodelabs/feedback/issues/new?title=[managed-agents-issue-resolver]
analytics account: UA-52746336-1
keywords: docType:Codelab, category:Cloud, product:GeminiEnterpriseAgentPlatform

---

# Autonomous GitHub Issue Resolution with Google Managed Agents API

Enable_GDP_Credits_Banner: True

> aside negative
>
> If you are attending an **instructor-led workshop**: Your instructor will provide you with a credit code. Please use
> the one they provide.

## Overview

Duration: 05:00

In this codelab you will build **Managed Issue Resolver**: a system that autonomously resolves GitHub issues and
deploys fixes to Cloud Run, driven entirely by the Google Managed Agents API on Gemini Enterprise Agent Platform.

Label any issue `ai-resolve`. A managed agent reads the issue via GitHub MCP, clones the repo, reproduces the failure,
fixes the bug, runs the tests, and opens a PR. When you merge the PR, a second managed agent deploys the fix to Cloud
Run using canary traffic splitting, monitors error rates via Cloud Monitoring MCP, then promotes or rolls back
automatically.

No orchestration framework. No LLM wrappers. No custom sandboxes. The Managed Agents API provisions the sandbox,
runs the model, executes code, and streams results. You bring two AGENTS.md files, two SKILL.md files, two GitHub Actions workflows,
and three hosted MCP servers.

### What you'll build

```mermaid
flowchart TD
    A([Issue labeled ai-resolve]) --> B

    subgraph GHA1["GitHub Actions: resolve.yml"]
        B[Run resolve.py]
    end

    subgraph RA["Resolver Agent - Gemini Enterprise Agent Platform"]
        B --> C[Read issue via GitHub MCP]
        C --> D["git clone + pip install"]
        D --> E[Run pytest - record failures]
        E --> F[Fix utils.py]
        F --> G[Run pytest - all pass]
        G --> H[Push branch + open PR via GitHub MCP]
    end

    H --> I([Human reviews and merges PR])
    I --> J

    subgraph GHA2["GitHub Actions: deploy.yml"]
        J[Cloud Build: build and push image]
        J --> K[Run deploy.py]
    end

    subgraph CDA["CD Agent - Gemini Enterprise Agent Platform"]
        K --> L[Deploy canary revision at 10%]
        L --> M{Poll Cloud Monitoring MCP\nevery 60s for 5 minutes}
        M -->|error rate OK| M
        M -->|all checks pass| N[Promote via --to-latest]
        M -->|error rate too high| O[Rollback to stable revision]
        N --> P[Close issue via GitHub MCP]
        O --> Q[Comment rollback details via GitHub MCP\nusing Cloud Logging MCP for error context]
    end

    P --> R([Issue closed with live URL])
    Q --> S([Issue stays open for investigation])
```

### The app you'll fix

A conference session browser showing 12 sessions across 5 tracks (AI & ML, Cloud, Mobile, Web, Security) over 2 days.
The app has four seeded bugs, all in `utils.py`:

| Bug | Symptom |
|---|---|
| Filter by track | Clicking any track filter returns an empty list |
| Filter by day | Filtering by Day 1 or Day 2 returns nothing |
| Speaker search | "eric" does not match "Eric Schmidt" (case-sensitive) |
| Session count | The count badge shows the wrong number |

The agent reads the issue, finds the root cause, fixes the code, and opens a PR. You review and merge it. The CD
agent deploys the fix automatically.

### What you'll learn

- Distinguish the **Agents API** (control plane: create, configure, and manage named agents) from the **Interactions API** (data plane: invoke agents at runtime) and understand when each is called.
- Configure the **Antigravity harness** (`base_agent: antigravity-preview-05-2026`) with built-in tools, GCS-mounted skill files, and domain-level network access controls.
- Write **AGENTS.md** (system instruction: agent identity and constraints) and **SKILL.md** (operational playbook: step-by-step procedure) and understand why they are stored and updated differently.
- Run long-running agent tasks with the **Managed Agents API** using background execution (`background=True`), event streaming (`stream=True`), and interaction persistence (`store=True`).
- Attach **hosted MCP servers** (GitHub, Cloud Monitoring, Cloud Logging) to agent interactions at call time, with no deployment and no custom integration code.
- Implement **canary traffic splitting** on Cloud Run with automated monitoring, promotion, and rollback driven entirely by an agent.

### What you'll need

- A Google Cloud project with billing enabled
- A GitHub account and a public GitHub repository
- The `gcloud` CLI and `gh` CLI installed and authenticated
- Python 3.11+ and `uv` installed

## Set Up Your Environment

Duration: 15:00

For this codelab, you'll use Cloud Shell or your local terminal. By the end of this step you'll have the repo
cloned, your GCP project configured, all required APIs enabled, a `.env` file filled in, a service account
created, and GitHub secrets set.

### What is Cloud Shell?

Cloud Shell is a free browser-based Linux terminal with `gcloud`, `git`, `gh`, `uv`, and Python pre-installed.
You don't need to install anything locally to complete this codelab.

To open Cloud Shell, click the terminal icon in the top-right toolbar of the GCP Console. When prompted, click
**Authorize** to allow Cloud Shell to make Google Cloud API calls.

> aside negative
>
> **If Cloud Shell goes idle for 20 minutes it will disconnect.** Reconnect and `cd managed-issue-resolver` to
> return to the working directory.

> aside positive
>
> **Prefer your local terminal?** You'll need `gcloud` CLI, `gh` CLI, `uv`, and Python 3.11+ installed.
> Everything else in this codelab runs identically.

### Clone the repository

```bash
git clone https://github.com/Saoussen-CH/managed-issue-resolver.git
cd managed-issue-resolver
```

> aside positive
>
> **Using this for a demo?** The repo ships with a working target app and seeded bugs. The `setup/` directory contains
> everything you need to configure and reset the demo (no manual file editing required).

### Authenticate and configure your project

```bash
gcloud auth login
gcloud auth application-default login
```

> aside positive
>
> **Why two auth commands?** `gcloud auth login` authenticates the CLI. `gcloud auth application-default login`
> creates credentials that Python scripts (like `create_agents.py` and `deploy.py`) use to call Google Cloud APIs.
> Without the second command, the agent SDK fails with a missing credentials error at runtime.

Then set your project:

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
echo "Project: $PROJECT_ID"
```

Expected output:
```text
Project: my-project-123
```

### Enable required APIs

```bash
gcloud services enable \
    aiplatform.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    storage.googleapis.com \
    --project $PROJECT_ID
```

This takes about 1 minute. You'll see `Operation finished successfully` when done.

> aside positive
>
> **Why these APIs?** `aiplatform.googleapis.com` is the Managed Agents API. The rest support Cloud Run deployment
> (`run`, `cloudbuild`, `artifactregistry`), skill storage (`storage`), and the hosted MCP servers for monitoring
> and logging.

### Fill in .env

```bash
cp .env.example .env
```

Edit `.env` and replace the two placeholder values:

```
GOOGLE_CLOUD_PROJECT=your-project-id
GCS_SKILLS_BUCKET=managed-issue-resolver-skills-your-project-id
```

Install Python dependencies:

```bash
uv sync
```

> aside negative
>
> **Pick a globally unique bucket name.** GCS bucket names are global, so `my-bucket` will likely be taken.
> A safe pattern: `managed-issue-resolver-skills-{PROJECT_ID}`.

### Create a service account

The GitHub Actions workflows need GCP credentials to call the Managed Agents API, build Docker images, and deploy to
Cloud Run. Create a dedicated service account with the exact roles needed:

```bash
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d= -f2)
SA=managed-issue-resolver@$PROJECT_ID.iam.gserviceaccount.com

gcloud iam service-accounts create managed-issue-resolver \
  --display-name="Managed Issue Resolver" \
  --project=$PROJECT_ID
```

Assign roles:

```bash
for ROLE in \
  roles/aiplatform.user \
  roles/run.admin \
  roles/cloudbuild.builds.editor \
  roles/artifactregistry.writer \
  roles/storage.admin \
  roles/storage.objectViewer \
  roles/mcp.toolUser \
  roles/monitoring.admin \
  roles/logging.admin \
  roles/logging.viewer \
  roles/serviceusage.serviceUsageConsumer \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA" \
    --role="$ROLE" --quiet
done
```

Download the key:

```bash
gcloud iam service-accounts keys create sa-key.json \
  --iam-account=$SA --project=$PROJECT_ID
```

> aside negative
>
> **Never commit `sa-key.json`.** The `.gitignore` already excludes it. Always delete the local copy after adding it
> to GitHub Secrets in the next step.

> aside positive
>
> **Why `roles/mcp.toolUser`?** The Cloud Monitoring and Cloud Logging MCP servers require this role to accept
> authenticated requests. Without it, the CD agent gets `403 Forbidden` when querying error rates.

### Add GitHub secrets

The workflows read secrets from the repository. Add them before the first run:

```bash
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d= -f2)

gh secret set GCP_SA_KEY < sa-key.json
gh secret set GCP_PROJECT_ID --body "$PROJECT_ID"
gh secret set CLOUD_RUN_REGION --body "us-central1"
```

Then delete the local key file:

```bash
rm sa-key.json
```

`GITHUB_TOKEN` is provided automatically by GitHub Actions (no action needed).

> aside negative
>
> **Allow pull request creation.** Go to your GitHub repo: **Settings > Actions > General > Workflow permissions**.
> Check: **Allow GitHub Actions to create and approve pull requests**. Without this, the resolver agent cannot open
> a PR and the workflow will fail with a `403` error.

The secrets `GCS_SKILLS_BUCKET`, `RESOLVER_AGENT_ID`, and `CD_AGENT_ID` will be added in the next step after the
bucket and agents are created.

## Understand the Architecture

Duration: 15:00

Before writing any code, let's understand what the Managed Agents API is and the five concepts that make
this system work: the Antigravity harness, the Agents API control plane, the Interactions API data plane,
AGENTS.md vs SKILL.md, and hosted MCP servers.

### What is the Managed Agents API?

Most LLM APIs give you a text-in, text-out interface: you send a prompt, the model generates a response, done.
That's enough for summarization or Q&A. It's not enough for resolving a GitHub issue - the agent needs to clone
a repo, run tests, write files, and open a PR. For that, the model needs real compute.

The **Managed Agents API** (part of Gemini Enterprise Agent Platform) is an API that runs a Gemini model inside
a fully provisioned Ubuntu sandbox. The model and the compute environment are co-located: the model can run
`bash`, execute Python, call `git`, run `pytest`, and make HTTP requests as part of a single interaction.

```
Your code (GitHub Actions workflow)
        │
        │  POST /v1beta1/projects/.../agents/{id}/interactions
        │  { "input": "Fix issue #42", "tools": [GitHub MCP, ...] }
        ▼
  Gemini Enterprise Agent Platform
        │
        ├─ provisions sandboxed Ubuntu VM
        ├─ mounts skill files from GCS
        ├─ starts Gemini Model Runtime alongside the compute
        │
        │  agent reasons → calls bash → runs pytest → edits files → calls GitHub MCP → opens PR
        │
        └─ streams interaction events back to your workflow
```

**Key advantages over rolling your own agent:**

| | Managed Agents API | Self-hosted (e.g., LangChain + Docker) |
|---|---|---|
| Infrastructure | Zero - platform provisions sandboxes on demand | You build, deploy, and scale the execution environment |
| Sandbox security | Isolated per interaction, auto-cleaned | You manage isolation |
| Long-running tasks | Background execution with `background=True`, up to 15 min | You handle timeouts and polling |
| MCP integration | Hosted MCP servers passed at call time | You deploy or proxy MCP servers |
| Environment snapshots | Auto-snapshot on idle, retained 7 days | You manage state persistence |
| SDK | `google-genai` with `vertexai=True`, three lines to invoke | Framework-specific, more code |

The Antigravity agent is also available directly via the Gemini API (`genai.Client()`, authenticated with
`GEMINI_API_KEY`). This project uses the **Vertex AI endpoint** (`vertexai=True`) to stay within your GCP
project's IAM, billing, and audit controls - the same `google-genai` SDK, a different authentication path.

```python
from google import genai

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

# Invoke an agent - the platform does the rest
stream = client.interactions.create(
    agent="managed-issue-resolver",   # named agent ID
    input=prompt,                      # what to do
    tools=[github_mcp_server],         # external tools to connect
    stream=True,                       # stream events as they happen
    background=True,                   # don't block while agent runs
    store=True,                        # persist interaction for multi-turn
)
```

### Concept: The Antigravity Harness

Every managed agent runs on the **Antigravity harness** - the execution engine that powers Gemini Enterprise
Agent Platform. The `base_agent` field in `client.agents.create()` names the harness version:

```python
client.agents.create(
    id="managed-issue-resolver",
    base_agent="antigravity-preview-05-2026",   # harness version
    ...
)
```

The Antigravity harness is built on **Gemini 3.5 Flash** - a model designed specifically for long-horizon
agentic and coding tasks, and 4x faster than comparable frontier models in token output speed. The model and
compute environment are co-optimized: Gemini 3.5 Flash is not a general-purpose model adapted for agents, it
is a model built from the ground up to reason, execute code, and manage multi-step workflows.

The critical design detail: the Gemini model and your code run **in the same sandbox**. There are no network
round-trips between the model's reasoning and code execution. When the model decides to run `pytest`, it calls
`bash` directly inside the sandbox.

Pre-installed software in every sandbox (Vertex AI Agent Platform):

| Software | Version | Used by this project |
|---|---|---|
| Python | 3.11 | Running pytest, executing fix scripts |
| Node.js | 20 | Available for JavaScript projects |
| gcloud CLI | Latest | Cloud Run, Cloud Build, and GCS operations |
| git | Latest | Cloning repos, pushing fix branches |
| curl / wget / jq | Latest | HTTP requests, JSON processing |
| ripgrep / fd / tree | Latest | Fast file search and directory listing |
| numpy, pandas | Latest | Available for data-processing agents |
| google-genai SDK | Latest | Available inside the sandbox for agent sub-calls |

> aside positive
>
> **Version note:** The Gemini API (non-Vertex) sandbox uses Python 3.12 and Node.js 22. The Vertex AI Agent
> Platform sandbox uses Python 3.11 and Node.js 20. Both ship the same UNIX tooling and Python packages.
> The agent can install additional packages at runtime with `pip install` or `npm install`. Installed
> packages persist when you reuse the same `environment_id`.

Built-in tools are configured at agent creation via the `tools` list:

| Tool type | What the agent gains |
|---|---|
| `code_execution` | Run shell commands (bash, Python, Node.js) with stdout/stderr capture |
| `google_search` | Web search from inside the sandbox |
| `url_context` | Fetch and read web pages |

> aside positive
>
> **`{"type": "filesystem"}` is a valid tool type on the Vertex AI Agent Platform.** It grants the agent
> explicit read, write, and list access to the sandbox filesystem. This project omits it because the harness
> already allows filesystem operations via `code_execution` (bash calls like `cat`, `ls`, `cp`). Use
> `{"type": "filesystem"}` when you want the agent to use structured file-tool calls instead of bash.

**Sandbox TTL:** Each sandbox auto-snapshots after 15 minutes of idle and is retained for 7 days. For
multi-turn interactions, pass `environment=<env_id>` and `previous_interaction_id=<interaction_id>` to
resume the same sandbox in a follow-up call.

**Network access:** On the Vertex AI Agent Platform, **network access is disabled by default.** Every agent
runs in a sandbox with no outbound connectivity unless you explicitly configure an allowlist. Our project sets
`{"domain": "*"}` to permit all outbound traffic. In enterprise environments, replace `*` with specific
domains to enforce a tight egress policy:

```python
"network": {
    "allowlist": [
        {"domain": "api.github.com"},   # GitHub API only
        {"domain": "pypi.org"},          # pip installs only
    ]
}
```

You can also inject credentials per-domain via `transform`. Credentials are injected by the egress proxy
and are **never exposed inside the sandbox** as environment variables or files:

```python
"network": {
    "allowlist": [
        {
            "domain": "api.github.com",
            "transform": {"Authorization": "Bearer ghp_..."},  # injected by egress proxy
        }
    ]
}
```

> aside positive
>
> **Why pin the harness version?** Using `base_agent="antigravity-preview-05-2026"` pins your agents to a
> specific harness version. Your agents always run on the same execution environment unless you explicitly
> recreate them with a newer `base_agent`. This makes upgrade decisions explicit and predictable for
> production workloads.

### Concept: Agents API (Control Plane) and Interactions API (Data Plane)

A naive approach would configure the agent inline with every API call, re-sending the full system prompt, tool
list, and environment config each time. That works for simple tasks but creates redundancy, blocks on
environment provisioning on every run, and couples your application code to prompt content.

The two-plane design solves this. Configuration is registered once on the control plane as a **named agent**
and referenced by a stable ID on the data plane.

**Agents API - the control plane:**

The Agents API manages named agent lifecycle. These calls happen during setup, not during every workflow run:

| Operation | SDK call | When |
|---|---|---|
| Create a named agent | `client.agents.create(id=..., ...)` | Once, during initial setup |
| Read agent config | `client.agents.get(id=...)` | To inspect or verify configuration |
| List all agents | `client.agents.list()` | To audit agents in the project |
| Update config | REST PATCH with `?update_mask=system_instruction` | When changing identity or tools |
| Delete an agent | `client.agents.delete(id=...)` | During cleanup |

Most control plane calls are **long-running operations (LROs)**. `client.agents.create()` provisions a base
environment snapshot and waits for it to be ready before returning.

```python
# Control plane: runs once in setup/create_agents.py
from google import genai

client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

client.agents.create(
    id="managed-issue-resolver",
    base_agent="antigravity-preview-05-2026",
    description="Reads a GitHub issue, fixes the bug, runs tests, opens a PR.",
    system_instruction=agents_md_content,            # content of AGENTS.md
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
                # agent-home/ contains AGENTS.md and skills/ - single source
                # required: API rejects two sources sharing the same top-level dir
                "source": f"gs://{BUCKET}/resolver/agent-home",
                "target": "/.agent",  # AGENTS.md -> /.agent/AGENTS.md
                                      # skills/   -> /.agent/skills/
            }
        ],
        "network": {"allowlist": [{"domain": "*"}]},   # enable outbound HTTP
    },
)
```

**Interactions API - the data plane:**

The Interactions API invokes a named agent for a specific task. Every GitHub Actions run calls this:

```python
# Data plane: runs on every workflow trigger in resolver/resolve.py
stream = client.interactions.create(
    agent=RESOLVER_AGENT_ID,   # reference to the named agent
    input=prompt,              # the task for this interaction
    tools=[                    # MCP servers attached at call time
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
    stream=True,       # yield events as the agent works
    background=True,   # return immediately; agent runs asynchronously
    store=True,        # persist interaction for potential multi-turn follow-up
)

for event in stream:
    print(event)  # interaction.created, message.delta, tool.call, interaction.completed
```

Key interaction parameters:

| Parameter | Why this project uses it |
|---|---|
| `background=True` | Agent tasks run up to 15 minutes; this prevents the GitHub Actions step from timing out while waiting for a blocking response |
| `stream=True` | Yields live events so the workflow log shows progress in real time |
| `store=True` | Persists the interaction so a follow-up call can reference it via `previous_interaction_id` for multi-turn sessions |

The named agent ID is the bridge between planes: created once on the control plane, referenced many times on
the data plane.

### Concept: AGENTS.md and SKILL.md

Two Markdown files configure what an agent knows and how it behaves. They serve fundamentally different
purposes and follow different update paths.

| | AGENTS.md | SKILL.md |
|---|---|---|
| **What it defines** | Agent identity, role, and constraints | Step-by-step operational procedure |
| **How it's passed** | Uploaded to GCS, mounted at `/.agent/AGENTS.md`; also passed as `system_instruction` at creation | Uploaded to GCS, mounted at `/.agent/skills/{name}/` |
| **Always in scope?** | Yes - loaded before every interaction | Yes - mounted when agent is created |
| **Updated by** | Upload new GCS file then recreate the agent | Upload new GCS file then recreate the agent |
| **Enterprise ownership** | Security and compliance teams (governance layer) | Operations teams (runbook layer) |

> aside negative
>
> **On Vertex AI Agent Platform, you cannot mount two GCS sources under the same top-level directory.**
> Defining one source at `/.agent/AGENTS.md` and another at `/.agent/skills/fix-issue/` will fail with a
> 400 `INVALID_ARGUMENT` error. Both files must live in the same GCS folder prefix, mounted as a single
> source at `/.agent`. This project uses `agent-home/` as that prefix:
>
> ```
> gs://{BUCKET}/resolver/agent-home/AGENTS.md              -> /.agent/AGENTS.md
> gs://{BUCKET}/resolver/agent-home/skills/fix-issue/      -> /.agent/skills/fix-issue/
> ```
>
> The Gemini API does not have this restriction because it supports `"type": "inline"` sources, where each
> file is its own entry. On Vertex AI with GCS sources, one prefix, one source entry.

> aside positive
>
> **`system_instruction` and `/.agent/AGENTS.md` are additive.** Both apply when present. This project sets
> both: `system_instruction` carries the content at agent creation time (stored in the agent definition),
> and `/.agent/AGENTS.md` is the same content mounted as a file the harness reads at runtime. You can use
> `system_instruction` alone for quick configuration, or both together for the full pattern.

**AGENTS.md - system instruction:**

AGENTS.md defines the agent's persona, rules, and hard constraints. It is always in scope. The agent reads it
before every interaction to know what actions are acceptable and what is off-limits.

The resolver agent's `AGENTS.md` (`target-app/.agents/AGENTS.md`):

```markdown
---
name: issue-resolver
description: Diagnose and fix bugs in GitHub issues, verify with tests, open a PR.
---

# Issue Resolver Agent

You are an expert software engineer. When given a GitHub issue, your job is to
understand the reported problem, locate the relevant code, write a targeted fix,
verify it with the existing test suite, and open a pull request.

## Rules
- Never create new files to apply a fix. Edit the file that contains the bug.
- Never fix a symptom when you can fix the root cause.
- If tests pass before your change, they must all pass after it too.
- Do not refactor, rename, or clean up anything unrelated to the issue.
- If you cannot confidently locate the bug, open a PR describing what you found
  and stop - do not guess.
```

**SKILL.md - playbook:**

SKILL.md defines the workflow procedure the agent follows for a specific task type. It is stored in GCS and
mounted read-only at `/.agent/skills/{name}/` when the agent is created. The agent reads it like documentation
when executing a task - a step-by-step runbook it follows.

Updating a skill means uploading a new file to GCS and recreating the agent. GCS sources are baked into the agent's base environment snapshot at creation time - the sandbox does not re-fetch from GCS on each interaction.

The resolver agent's skill (`target-app/.agents/skills/fix-issue/SKILL.md`, excerpt):

```markdown
---
name: fix-issue
description: Clone a repo, diagnose a bug from a GitHub issue, fix it, open a PR.
---

# Skill: Fix GitHub Issue

## Workflow

1. Read the issue using the GitHub MCP server to get the title, body, and number.
2. Clone the repository and read its structure before opening any files.
3. Install dependencies and run the existing tests - record which ones fail.
4. Diagnose the root cause by reading the failing test and the source it tests.
5. Fix the root cause. Run tests again. Iterate until all tests pass.
6. Commit, push a branch fix/issue-{number}, and open a PR via GitHub MCP.
```

This project has two skills:

| Skill | Local file | Mount path in sandbox |
|---|---|---|
| `fix-issue` | `target-app/.agents/skills/fix-issue/SKILL.md` | `/.agent/skills/fix-issue/SKILL.md` |
| `deploy` | `cd-agent/SKILL.md` | `/.agent/skills/deploy/SKILL.md` |

**When to put content in AGENTS.md vs SKILL.md:**

Put in **AGENTS.md** anything that defines what the agent IS and what it MUST NOT do:
- Role and expertise ("You are a senior software engineer")
- Hard constraints ("Never modify files outside `target-app/`")
- Output format requirements ("Always link the PR to the issue")

Put in **SKILL.md** anything that defines HOW to do a specific task:
- Step-by-step workflow (clone, install, test, fix, push)
- Tool usage notes ("Use the GitHub MCP server for all GitHub API calls")
- Decision logic for the task ("If tests fail after fix, iterate before opening PR")

In enterprise environments, this separation maps naturally to change management: both files require a GCS upload and agent recreation to take effect, but they are owned by different teams and go through different review gates: AGENTS.md by security and compliance, SKILL.md by operations.

### Concept: Hosted MCP servers

A naive approach would write custom Python functions to call the GitHub API, Cloud Monitoring API, and Cloud
Logging API, then register them as tools. That works, but it means writing auth handling, request formatting,
and error handling for every external service.

**Hosted MCP servers** solve this. MCP (Model Context Protocol) is an open standard for exposing APIs as
agent-callable tools. Google and GitHub host MCP servers for their APIs - you pass the URL and auth headers at
interaction time, and the agent gets a full set of typed tools with no code required.

This project uses three hosted MCP servers (no deployment required):

| Server | URL | Used by |
|---|---|---|
| GitHub | `https://api.githubcopilot.com/mcp/` | Both agents: read issues, open PRs, post comments |
| Cloud Monitoring | `https://monitoring.googleapis.com/mcp` | CD agent: query `run.googleapis.com/request_count` |
| Cloud Logging | `https://logging.googleapis.com/mcp` | CD agent: fetch error logs on rollback |

MCP servers are passed at interaction time via the `tools` parameter:

```python
stream = client.interactions.create(
    agent=AGENT_ID,
    input=prompt,
    tools=[
        {
            "type": "mcp_server",
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {
                "Authorization": f"Bearer {GH_TOKEN}",
                "X-MCP-Exclude-Tools": "delete_file",   # avoids name conflict
            },
        },
    ],
    stream=True,
    background=True,
    store=True,
)
```

> aside positive
>
> **Why `X-MCP-Exclude-Tools: delete_file`?** The GitHub MCP server exposes a `delete_file` tool. The Managed Agents
> sandbox also provides a built-in `delete_file` tool for the local filesystem. Having two tools with the same name
> causes a conflict that crashes the interaction. Excluding the GitHub MCP's `delete_file` avoids this.

## Create Named Agents

Duration: 08:00

In this step you'll create a GCS bucket, upload AGENTS.md and SKILL.md for both agents, register the two named agents on
Gemini Enterprise Agent Platform, and verify they initialize correctly before triggering any workflow.

### Upload agent files to GCS

Both AGENTS.md and SKILL.md files are stored in GCS and mounted into the agent sandbox at `/.agent/`. Create the bucket and upload all files:

```bash
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d= -f2)
GCS_SKILLS_BUCKET=$(grep GCS_SKILLS_BUCKET .env | cut -d= -f2)

gcloud storage buckets create gs://$GCS_SKILLS_BUCKET \
  --location=us-central1 \
  --project=$PROJECT_ID
```

Add the bucket name as a GitHub secret:

```bash
gh secret set GCS_SKILLS_BUCKET --body "$GCS_SKILLS_BUCKET"
```

Upload both AGENTS.md and SKILL.md files:

```bash
bash setup/upload_skills.sh
```

Expected output:
```text
Uploading agent-home directories to gs://managed-issue-resolver-skills-my-project ...
(agent-home/ contains AGENTS.md + skills/ - single mount at /.agent)
[gsutil copy output]

Uploaded:
gs://managed-issue-resolver-skills-my-project/cd-agent/agent-home/AGENTS.md
gs://managed-issue-resolver-skills-my-project/cd-agent/agent-home/skills/deploy/SKILL.md
gs://managed-issue-resolver-skills-my-project/resolver/agent-home/AGENTS.md
gs://managed-issue-resolver-skills-my-project/resolver/agent-home/skills/fix-issue/SKILL.md

Note: recreate agents after changing SKILL.md or AGENTS.md files:
  uv run python setup/create_agents.py
```

> aside positive
>
> **Re-run `upload_skills.sh` whenever you edit AGENTS.md or SKILL.md.** Both files are read from GCS at
> agent creation time. Local edits have no effect until you upload. After uploading, recreate the agents to
> pick up the latest content.

### Register agents

Run `create_agents.py` once to register both named agents on Gemini Enterprise Agent Platform:

```bash
uv run python setup/create_agents.py
```

The script prints the `gh secret set` commands for both agent IDs. Run them:

```bash
gh secret set RESOLVER_AGENT_ID --body "managed-issue-resolver"
gh secret set CD_AGENT_ID --body "managed-issue-cd"
```

Verify the agents initialize correctly before triggering the workflow:

```bash
uv run python setup/test_agents.py
```

Expected output:
```text
Testing: managed-issue-resolver
  Prompt: Say hello and confirm you can access the GitHub MCP server.
  interaction.created
  PASS: agent initialized and completed successfully

Testing: managed-issue-cd
  Prompt: Say hello and confirm you can access the GitHub, Cloud Monitoring, and Cloud Loggi
  interaction.created
  PASS: agent initialized and completed successfully

========================================
All agents OK. Ready to trigger the workflow.
```

> aside positive
>
> **Agent IDs are permanent.** Once created, the agent ID never changes. Re-run `upload_skills.sh` and then
> `create_agents.py` only if you change AGENTS.md or SKILL.md files, or delete the agents. The GitHub secrets never need
> updating once set.

> aside negative
>
> **If you see `GOOGLE_CLOUD_PROJECT: KeyError`**, your `.env` file is not filled in or not being loaded. Check
> that `GOOGLE_CLOUD_PROJECT=your-project-id` is set correctly in `.env` and that you ran the command from the
> repo root.

### Inspect the control plane code

Before moving on, read the file that just ran:

```bash
cat setup/create_agents.py
```

Notice how it maps to the concepts from the architecture step:

```python
# 1. Initialize the client - Vertex AI endpoint, global region (required for Managed Agents)
client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

# 2. Read AGENTS.md from disk - this becomes the system_instruction
RESOLVER_AGENTS_MD = Path("target-app/.agents/AGENTS.md").read_text()

# 3. Call the Agents API control plane - this is the one-time setup call
client.agents.create(
    id="managed-issue-resolver",
    base_agent="antigravity-preview-05-2026",        # pins the Antigravity harness version
    system_instruction=RESOLVER_AGENTS_MD,           # AGENTS.md content: identity + constraints
    tools=[
        {"type": "code_execution"},                  # enables bash and Python execution
        {"type": "google_search"},
        {"type": "url_context"},
    ],
    base_environment={
        "type": "remote",
        "sources": [
            {
                "type": "gcs",
                # agent-home/ contains both AGENTS.md and skills/ subdirectory.
                # One source is required: the API rejects multiple sources that
                # share the same top-level target directory (/.agent).
                "source": f"gs://{GCS_SKILLS_BUCKET}/resolver/agent-home",
                "target": "/.agent",   # AGENTS.md -> /.agent/AGENTS.md
                                       # skills/    -> /.agent/skills/
            }
        ],
        "network": {"allowlist": [{"domain": "*"}]},   # network off by default; * allows all
    },
)
```

Also read the AGENTS.md and SKILL.md files to see their actual content:

```bash
cat target-app/.agents/AGENTS.md
cat target-app/.agents/skills/fix-issue/SKILL.md
```

Observe: AGENTS.md defines constraints ("never modify files outside target-app/"). SKILL.md defines procedure
("1. Read the issue. 2. Clone the repo. 3. Run pytest."). These are separate files that can be updated
independently and by different teams.

## Deploy the Target App

Duration: 05:00

The target app is a conference session browser with four seeded bugs. You'll deploy the broken version to Cloud
Run now so the CD agent has a live service to update when the resolver agent's fix is merged.

Create an Artifact Registry repository to store the Docker images that Cloud Build will produce:

```bash
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d= -f2)

gcloud artifacts repositories create managed-issue-resolver \
  --repository-format=docker \
  --location=us-central1 \
  --project=$PROJECT_ID
```

Deploy the initial (broken) version of the conference session browser to Cloud Run:

```bash
gcloud run deploy target-app \
  --source target-app/ \
  --region us-central1 \
  --allow-unauthenticated \
  --project=$PROJECT_ID
```

This takes 2-3 minutes. When complete, you'll see:

```text
Service URL: https://target-app-xxxx.us-central1.run.app
```

Open the URL in your browser. Click any track filter: notice the session list goes empty. That is the first of four
seeded bugs the agent will fix.

> aside negative
>
> **`--allow-unauthenticated` is intentional here.** It makes the app publicly accessible for demo purposes. In
> production, remove this flag and add IAM-based authentication.

## Trigger Issue Resolution

Duration: 10:00

The resolver workflow fires when a GitHub issue gets the `ai-resolve` label. You'll create the label, open an
issue describing the bug, watch the agent fix it, then review and merge the PR it opens.

### Create the `ai-resolve` label

The GitHub Actions `resolve.yml` workflow fires when an issue is labeled `ai-resolve`:

```bash
gh label create ai-resolve --color "0075ca" --description "Trigger AI issue resolution"
```

### Open an issue

```bash
gh issue create \
  --title "Track filter returns no sessions" \
  --body "When clicking any track filter (AI & ML, Cloud, Mobile, etc.) the session list becomes empty. All sessions disappear regardless of which track is selected.

Expected: only sessions matching the selected track should appear.

Bug is in \`target-app/utils.py\`." \
  --label "ai-resolve"
```

The `ai-resolve` label triggers the workflow immediately.

### Inspect the data plane code

Before watching the agent run, read the script the workflow calls:

```bash
cat resolver/resolve.py
```

This is the Interactions API call - the data plane complement to `create_agents.py`:

```python
# resolver/resolve.py - called on every workflow trigger
client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

stream = client.interactions.create(
    agent=RESOLVER_AGENT_ID,   # stable ID referencing the named agent created earlier
    input=prompt,              # "Resolve this GitHub issue: https://github.com/.../issues/1"
    tools=[
        {
            "type": "mcp_server",
            "url": "https://api.githubcopilot.com/mcp/",
            "name": "github",
            "headers": {
                "Authorization": f"Bearer {GH_TOKEN}",
                "X-MCP-Exclude-Tools": "delete_file",  # prevents tool name conflict
            },
        },
    ],
    stream=True,       # events stream in real time to the workflow log
    background=True,   # call returns immediately; events are polled from the stream
    store=True,        # persists this interaction for potential multi-turn follow-up
)

for event in stream:
    print(str(event)[:300], flush=True)
```

Notice what is NOT here: no system prompt, no tool list for the sandbox tools, no environment config. All of
that lives on the named agent. `resolve.py` only passes what changes per invocation: the prompt (the issue URL)
and the runtime MCP server (with the GitHub token for this specific run).

### Watch the agent work

```bash
gh run watch
```

You'll see the GitHub Actions run progress through these steps:

```text
✓ Checkout
✓ Set up Python
✓ Install dependencies
✓ Authenticate to Google Cloud
✓ Comment on issue
● Run resolver agent    <- agent is working here
```

The "Comment on issue" step posts a message to the issue: "Agent is working on this. A PR will appear here when
the fix is ready."

### What the agent does

While the workflow is running, the Managed Agent is executing inside a hosted sandbox:

1. **Reads the issue** via GitHub MCP (gets the title, body, and issue number)
2. **Clones the repo** using the authenticated URL injected via the prompt
3. **Installs dependencies** from `requirements.txt`
4. **Runs pytest** (records which tests fail: all 4 filter tests)
5. **Reads `utils.py`** and finds the root causes:
   - `filter_by_track` normalizes `"AI & ML"` to `"ai-and-ml"` but sessions store `"AI & ML"`
   - `filter_by_day` compares string `"1"` to integer `1` (never equal)
   - `search_by_speaker` uses case-sensitive `in` operator
   - `session_count` counts from the full list instead of the filtered one
6. **Writes the fix**: targeted edits to `utils.py`
7. **Runs pytest again**: all 4 tests pass
8. **Pushes a branch** `fix/issue-1` and opens a PR via GitHub MCP

> aside positive
>
> **The agent never calls your code directly.** It runs `pytest` inside the sandbox the same way a developer would
> on their laptop. If the tests fail after the fix, the agent iterates: it does not open a PR until all tests pass.

> aside negative
>
> **Run takes 3-5 minutes.** The agent reasons step by step, so it is slower than running pytest yourself. This is
> expected. If the run exceeds 15 minutes, the sandbox auto-snapshots and the interaction ends (this rarely happens
> for a single-file fix).

### Review and merge the PR

When the workflow completes, check the open PRs:

```bash
gh pr list
```

You should see one PR from `fix/issue-1`:

```text
#2  fix: track filter returns no sessions (closes #1)  fix/issue-1
```

Review the diff:

```bash
gh pr diff 2
```

The agent should have changed `utils.py` to:
- Remove the slug normalization in `filter_by_track` (compare directly without lowercasing)
- Cast `day` to `int` in `filter_by_day`
- Use `.lower()` in `search_by_speaker`
- Replace `len(SESSIONS)` with `len(sessions)` in `session_count`

Merge it:

```bash
gh pr merge 2 --squash --delete-branch
```

This triggers the CD workflow immediately.

> aside positive
>
> **Always review before merging.** The agent is autonomous but you are the last line of defense. Check that the
> fix is targeted: only the four buggy functions should change. If the agent modified unrelated files or added
> unnecessary code, close the PR and re-open the issue.

## Watch the CD Agent Deploy

Duration: 08:00

Merging the PR triggers the CD workflow. The CD agent follows a canary deployment strategy: deploy at 10%
traffic, monitor error rates for 5 minutes via Cloud Monitoring MCP, then promote or roll back automatically.

### What the CD workflow does

Merging the PR triggers `deploy.yml`, which:

1. Authenticates to GCP using the service account key
2. Runs `gcloud builds submit --async` to build the Docker image from `target-app/`
3. Polls `gcloud builds describe` every 15 seconds until the build completes
4. Calls `cd-agent/deploy.py` with the PR URL and image URL

`deploy.py` then calls `client.interactions.create(agent=CD_AGENT_ID, ...)` and streams the CD agent's output.

### What the CD agent does

The CD agent follows the `deploy` skill playbook:

1. **Records the stable revision**: saves the current revision name before deploying
2. **Deploys with `--no-traffic`**: the new image is deployed but gets zero requests
3. **Splits traffic at 10%**: `gcloud run services update-traffic --to-revisions NEW_REV=10`
4. **Monitors for 5 minutes**: queries Cloud Monitoring MCP every 60 seconds for `run.googleapis.com/request_count`
5. **Promotes or rolls back**:
   - If error rate stays below 5%: `--to-latest` (promotes new revision to 100%)
   - If error rate spikes: `--to-revisions STABLE_REV=100` (rolls back instantly)
6. **Closes the linked issue** via GitHub MCP (posts the live URL and closes the issue)

Watch the workflow:

```bash
gh run watch
```

When the CD agent completes, check the linked issue is closed:

```bash
gh issue list --state closed
```

And verify the fix is live in your browser: the track filter should now work.

> aside positive
>
> **Why `--to-latest` on promotion?** If you use `--to-revisions NEW_REV=100`, Cloud Run enters "manual traffic
> mode." Future deployments create new revisions but get no traffic until you manually update the traffic config.
> Using `--to-latest` keeps the service in automatic mode where each new deploy automatically becomes the active
> revision.

> aside negative
>
> **If the CD agent times out**: This is rare but can happen if Cloud Build takes longer than expected. Re-trigger
> by re-merging the PR or running `uv run python cd-agent/deploy.py <pr_url> <image_url>` locally.

## Clean Up

Duration: 03:00

### Reset for another run

To run the demo again without starting from scratch, use the reset script:

```bash
bash setup/reset_demo.sh
```

The script:

1. **Waits** for any in-progress CD workflows to finish (polls every 15 seconds)
2. **Closes** all open PRs (agent-opened or otherwise)
3. **Restores** `target-app/utils.py` from `setup/utils_broken.py` (the canonical broken version)
4. **Commits and pushes** the reset to master
5. **Redeploys** the broken app to Cloud Run with `gcloud run deploy --source`

When done:
```text
Done. Demo is reset and ready.
Open a new issue with the 'ai-resolve' label to trigger the agent.
```

You can now repeat from the Trigger Issue Resolution step.

> aside positive
>
> **Why `setup/utils_broken.py`?** The reset script copies from this canonical file rather than reverting with git.
> The agent never writes to `setup/` (it only clones `target-app/`), so `utils_broken.py` is never accidentally
> modified. It is always the correct broken state regardless of agent activity.

> aside negative
>
> **Push conflicts after CD workflow**: If a CD workflow was running when you started the reset, `git push` may be
> rejected with a non-fast-forward error. Run `git pull --rebase && git push` to resolve.

### Remove all resources

Remove all Google Cloud resources to avoid ongoing charges.

Delete the Cloud Run service:

```bash
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d= -f2)

gcloud run services delete target-app \
  --region=us-central1 \
  --project=$PROJECT_ID --quiet
```

Delete the Artifact Registry repository:

```bash
gcloud artifacts repositories delete managed-issue-resolver \
  --location=us-central1 \
  --project=$PROJECT_ID --quiet
```

Delete the GCS skills bucket:

```bash
GCS_SKILLS_BUCKET=$(grep GCS_SKILLS_BUCKET .env | cut -d= -f2)

gcloud storage rm -r gs://$GCS_SKILLS_BUCKET
```

Delete the named agents:

```bash
uv run python setup/delete_agents.py
```

Delete the service account:

```bash
SA=managed-issue-resolver@$PROJECT_ID.iam.gserviceaccount.com

gcloud iam service-accounts delete $SA \
  --project=$PROJECT_ID --quiet
```

### Verify everything is removed

```bash
gcloud run services list --region=us-central1 --project=$PROJECT_ID
gcloud storage buckets list --project=$PROJECT_ID
```

Expected output: empty lists or only your own pre-existing resources.

## Summary

Duration: 02:00

Congratulations! You've built an autonomous AI-driven issue resolution and deployment pipeline on Google Cloud.

### What you built

| Component | Role |
|---|---|
| **Resolver Agent** | Reads GitHub issues, clones the repo, fixes bugs, opens PRs |
| **CD Agent** | Canary-deploys fixes, monitors error rates, promotes or rolls back |
| **GitHub MCP** | Gives both agents access to the GitHub API (no custom integration code) |
| **Cloud Monitoring MCP** | Gives the CD agent live error rate data during canary monitoring |
| **Cloud Logging MCP** | Gives the CD agent error log context when a rollback happens |

### Key patterns you learned

1. **Antigravity harness**: pin the execution engine version with `base_agent="antigravity-preview-05-2026"`; Gemini 3.5 Flash runs inside the same sandbox as your code, with no round-trips between reasoning and execution
2. **Two-plane architecture**: Agents API (control plane) manages named agent lifecycle; Interactions API (data plane) invokes agents at runtime - configuration is separate from invocation
3. **AGENTS.md vs SKILL.md**: AGENTS.md is the system instruction (who the agent IS, what it MUST NOT do); SKILL.md is the playbook (what steps to follow); updated independently by different teams
4. **Hosted MCP servers**: connect GitHub, Cloud Monitoring, and Cloud Logging at interaction time, with no deployment and no custom integration code
5. **`X-MCP-Exclude-Tools`**: prevent tool name conflicts between MCP servers and the sandbox built-in tools
6. **`background=True` + `store=True`**: run long agent interactions asynchronously and stream live events
7. **Canary traffic splitting**: `--no-traffic` deploy, then `--to-revisions NEW_REV=10`, then `--to-latest` promote
8. **`setup/utils_broken.py`**: keep a canonical broken state outside the agent's working directory for reliable reset

### Next steps

- Extend the resolver SKILL.md to handle multi-file bugs or JavaScript projects
- Add a second issue type (performance regression, wrong output format) and trigger it with a different label
- Replace the canary monitoring interval: try querying every 30 seconds for 10 minutes
- Explore multi-turn interactions using `environment=<env_id>` + `previous_interaction_id=<interaction_id>`
- Add a Slack MCP server to post deployment notifications

### Resources

- [Managed Agents API Quickstart](https://ai.google.dev/gemini-api/docs/managed-agents-quickstart)
- [Gemini Enterprise Agent Platform Docs](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cloud Run Traffic Splitting](https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration)
- [google-genai Python SDK](https://github.com/googleapis/python-genai)
