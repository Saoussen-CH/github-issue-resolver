#!/usr/bin/env bash
# Export the codelab, inject the "About this codelab" card, and copy to docs/.
#
# Local preview:
#   bash codelab/generate.sh
#   claat serve codelab/
#   open http://localhost:9090/<codelab-id>/
#
# Prerequisites: go install github.com/googlecodelabs/tools/claat@latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$REPO_ROOT/docs"

# Derive codelab ID from frontmatter so this script never needs updating
CODELAB_ID=$(grep '^id:' "$SCRIPT_DIR/index.lab.md" | head -1 | sed 's/^id:[[:space:]]*//')
CODELAB_DIR="$SCRIPT_DIR/$CODELAB_ID"

cd "$SCRIPT_DIR"

echo "Exporting codelab (id: $CODELAB_ID)..."
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
echo "  open http://localhost:9090/$CODELAB_ID/"
