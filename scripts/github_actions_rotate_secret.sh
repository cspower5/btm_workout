#!/usr/bin/env bash
# Rotate a GitHub repo secret using the `gh` CLI.
# Usage: ./scripts/github_actions_rotate_secret.sh <repo> <secret_name> <new_value>
# Example: ./scripts/github_actions_rotate_secret.sh cspower5/btm_workout ADMIN_PREVIEW_TOKEN abcd1234

set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <owner/repo> <secret_name> <new_value>"
  exit 1
fi

REPO=$1
SECRET_NAME=$2
NEW_VALUE=$3

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI not found. Install GitHub CLI and authenticate (gh auth login)." >&2
  exit 1
fi

echo "Setting secret $SECRET_NAME in $REPO"
# Requires repo-level access and gh authenticated
gh secret set "$SECRET_NAME" --repo "$REPO" --body "$NEW_VALUE"

echo "Secret updated. If your workflow uses the secret, re-run or trigger a new workflow to pick up the change."
