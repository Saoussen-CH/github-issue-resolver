#!/usr/bin/env bash
# Export the codelab, inject the "About this codelab" card, and copy to docs/.
#
# Local preview:
#   bash codelab/generate.sh
#   claat serve codelab/
#   open http://localhost:9090/managed-agents-issue-resolver/
#
# Prerequisites: go install github.com/googlecodelabs/tools/claat@latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CODELAB_DIR="$SCRIPT_DIR/managed-agents-issue-resolver"
DOCS_DIR="$REPO_ROOT/docs"

cd "$SCRIPT_DIR"

echo "Exporting codelab..."
claat export index.lab.md

echo "Injecting 'About this codelab' card..."
python3 "$SCRIPT_DIR/inject_about.py" "$CODELAB_DIR/index.html"

echo "Copying to docs/..."
rm -rf "$DOCS_DIR"
mkdir -p "$DOCS_DIR"
cp -r "$CODELAB_DIR/." "$DOCS_DIR/"
touch "$DOCS_DIR/.nojekyll"

echo ""
echo "Done. To preview locally:"
echo "  claat serve codelab/"
echo "  open http://localhost:9090/managed-agents-issue-resolver/"
