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

<!-- TODO: Write the step-by-step workflow. The agent needs to know:
     1. How to read the issue (which tool, what information to extract)
     2. How to orient itself in the codebase before touching any files
     3. How to establish a failure baseline (what to run, what to record)
     4. How to diagnose from failing tests rather than guessing
     5. How to write the fix (scope: only the root cause)
     6. The quality gate before pushing (what must be true)
     7. How to create and push the branch and open the PR (naming convention, PR body)
-->

## Critical rules

<!-- TODO: Add the hard constraints from the skill's perspective.
     Focus on what must never be skipped (test run, specific tool for GitHub ops)
     and what must never happen (pushing with failing tests, creating new files).
-->
