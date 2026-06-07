#!/usr/bin/env bash
# Regenerate the codelab HTML from index.lab.md using claat.
# Output goes to docs/ at the repo root (GitHub Pages source).
#
# Prerequisites: go install github.com/googlecodelabs/tools/claat@latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

claat export "$SCRIPT_DIR/index.lab.md"

rm -rf "$REPO_ROOT/docs"
mv "$SCRIPT_DIR/managed-agents-issue-resolver" "$REPO_ROOT/docs"
touch "$REPO_ROOT/docs/.nojekyll"

echo "Codelab generated at $REPO_ROOT/docs/index.html"
