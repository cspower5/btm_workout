#!/usr/bin/env bash
set -euo pipefail

# This script prepares an isolated clone and runs git-filter-repo to remove
# the `my_jupyter_env/` (or other) directories from history. It DOES NOT
# run on your current repo; it creates a temporary clone and shows commands.

TMPDIR=$(mktemp -d)
echo "Creating a temporary clone in $TMPDIR"
git clone --mirror "$(git rev-parse --show-origin)" "$TMPDIR/repo.git" || true
echo "Mirror clone created at $TMPDIR/repo.git"

cat <<'EOF'
To finish the purge, run the following commands locally (review first):

cd $TMPDIR/repo.git
# Install git-filter-repo (pip install git-filter-repo) and run:
# git filter-repo --path my_jupyter_env/ --invert-paths
# After inspection, push the rewritten history to a new remote (requires force push):
# git remote add cleaned <your-cleaned-remote-url>
# git push cleaned --all --force
EOF

echo "Note: This script is only a helper. Read HISTORY_REWRITE.md before running any destructive commands."