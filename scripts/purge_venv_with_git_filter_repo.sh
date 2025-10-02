#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/purge_venv_with_git_filter_repo.sh <path-to-remove> [mirror-dir]
# Example: ./scripts/purge_venv_with_git_filter_repo.sh my_jupyter_env

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <path-to-remove> [mirror-dir]"
  exit 1
fi

REMOVE_PATH="$1"
MIRROR_DIR="${2:-./tmp-repo-mirror}"

echo "This script will create a mirror clone, run git-filter-repo to remove '$REMOVE_PATH' from history, and write the cleaned repo to '${MIRROR_DIR}-cleaned'."
echo "It will NOT push any changes to origin. Review outputs before pushing anywhere."

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo not found. Install it with: pip install git-filter-repo"
  exit 1
fi

if [ -d "$MIRROR_DIR" ]; then
  echo "Mirror dir $MIRROR_DIR already exists. Please remove or pick another path." >&2
  exit 1
fi

echo "Creating mirror clone (bare) into $MIRROR_DIR.git ..."
git clone --mirror "$(git rev-parse --show-toplevel)" "$MIRROR_DIR.git"

cd "$MIRROR_DIR.git"

echo "Running git-filter-repo to remove path: $REMOVE_PATH"
# The --invert-paths option keeps everything except the specified path(s)
git filter-repo --path "$REMOVE_PATH" --invert-paths

echo "Filtering complete. A cleaned mirror repo is at: $(pwd)"
echo "To inspect this cleaned mirror as a normal repo, run:" 
echo "  git clone $PWD ../${MIRROR_DIR}-cleaned"
echo "Then inspect, run tests, and when satisfied, push the cleaned repo to a new remote with force (coordinate with team):"
echo "  cd ../${MIRROR_DIR}-cleaned"
echo "  git remote add cleaned <NEW_REMOTE_URL>"
echo "  git push cleaned --all --force"

echo "Important: do NOT push to your original remote until you have coordinated with collaborators and backups are taken."
