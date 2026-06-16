---
name: fix-issue
description: Clone a repository, diagnose a bug from a GitHub issue, fix it, and open a pull request.
---

# Skill: Fix GitHub Issue

## Trigger
Called with a GitHub issue URL and an authenticated repository clone URL.

## Tools available
- bash: git, pytest, pip, and standard Unix tools are pre-installed.
- GitHub MCP server: use it for all GitHub API operations (read issue, create PR, post comment).

## Workflow

1. Read the issue using the GitHub MCP server to get the title, body, and number. Understand the reported behavior and the expected behavior.

2. Clone the repository and read its structure:
   ```bash
   git clone <auth_repo_url> /workspace/repo
   cd /workspace/repo
   ls -la
   ```
   Check for a README. Understand the language, framework, and layout before opening any files.

3. Install dependencies (check for `requirements.txt`, `package.json`, `pyproject.toml`, `Pipfile`, `Makefile` - use whatever the project has).

4. Run the existing tests to see the current failure baseline:
   - Look for a test runner (`pytest`, `npm test`, `make test`, etc.)
   - Run all tests and record which ones fail.

5. Diagnose the issue using the playbook below.

6. Write the fix. Change only the code that causes the reported behavior.

7. Run the tests again. If any fail, read the output carefully and iterate. **Do not open a PR until all tests pass.**

8. Commit and push:
   ```bash
   git config user.email "agent@managed-agents.dev"
   git config user.name "Issue Resolver Agent"
   git checkout -b fix/issue-<ISSUE_NUMBER>
   git add -A
   git commit -m "fix: <concise description> (closes #<ISSUE_NUMBER>)"
   git push origin fix/issue-<ISSUE_NUMBER>
   ```

9. Open a pull request using the GitHub MCP server:
   - Title: `fix: <description> (closes #<ISSUE_NUMBER>)`
   - Body: what was broken, what you changed, confirmation that all tests pass, `Closes #<ISSUE_NUMBER>`
   - Base: `main`, Head: `fix/issue-<ISSUE_NUMBER>`

10. Post a comment on the original issue using the GitHub MCP server: "PR opened: <PR_URL>"

## Diagnosis Playbook

| Symptom in issue | Where to look first |
|---|---|
| Endpoint returns wrong status code | Route handler and input validation logic |
| Wrong calculation or value returned | Helper / utility functions called by the route |
| Crash or 500 on specific input | Validate input before it reaches business logic |
| Results missing or incomplete | Pagination, filtering, or query logic |
| Works for some inputs but not others | Edge cases in conditionals or math operations |

## Idempotency - check before you change

Before editing any file, read it. Confirm the bug exists where you expect. If the current code already looks correct, re-read the failing test output - the bug may be elsewhere.

## Critical rules

- **MANDATORY: run the full test suite before opening a PR.** Never skip this.
- **Do NOT create new files to apply a fix.** Edit the file that contains the bug.
- **Do NOT open a PR if any tests fail.** Fix the failures first.
- If the same test still fails after your fix, you fixed the wrong thing - re-read the issue and the test.
