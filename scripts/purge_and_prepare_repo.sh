#!/usr/bin/env bash
set -euo pipefail

# purge_and_prepare_repo.sh
# Fully automated mirror-based purge using git-filter-repo. Runs only locally and does NOT push.
# Usage: ./scripts/purge_and_prepare_repo.sh <path-to-remove> [author-map.csv] [mirror-dir]

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <path-to-remove> [author-map.csv] [mirror-dir]"
  exit 1
fi

REMOVE_PATH="$1"
AUTHOR_MAP_FILE="${2:-}"
MIRROR_DIR="${3:-./tmp-repo-mirror}"

echo "Preparing to purge path: $REMOVE_PATH"

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "ERROR: git-filter-repo is required. Install: pip install git-filter-repo"
  exit 1
fi

if [ -d "${MIRROR_DIR}.git" ]; then
  echo "ERROR: mirror dir ${MIRROR_DIR}.git already exists. Choose another directory or remove it." >&2
  exit 1
fi

ROOT_DIR=$(git rev-parse --show-toplevel)
echo "Creating bare mirror of $ROOT_DIR at ${MIRROR_DIR}.git"
git clone --mirror "$ROOT_DIR" "${MIRROR_DIR}.git"

cd "${MIRROR_DIR}.git"

ARGV=(--force --invert-paths --path "$REMOVE_PATH")

if [ -n "$AUTHOR_MAP_FILE" ] && [ -f "$AUTHOR_MAP_FILE" ]; then
  echo "Author map detected: $AUTHOR_MAP_FILE"
  # Build python commit-callback file
  CB_FILE="$(mktemp /tmp/callback.XXXX.py)"
  echo "def commit_callback(commit):" > "$CB_FILE"
  while IFS=',' read -r OLD_EMAIL NEW_NAME NEW_EMAIL; do
    OLD_EMAIL="$(echo "$OLD_EMAIL" | xargs)"
    NEW_NAME="$(echo "$NEW_NAME" | xargs)"
    NEW_EMAIL="$(echo "$NEW_EMAIL" | xargs)"
    if [ -z "$OLD_EMAIL" ] || [ -z "$NEW_EMAIL" ]; then
      continue
    fi
    printf "    if commit.author_email == b'%s':\n" "$OLD_EMAIL" >> "$CB_FILE"
    printf "        commit.author_email = b'%s'\n" "$NEW_EMAIL" >> "$CB_FILE"
    printf "        commit.committer_email = b'%s'\n" "$NEW_EMAIL" >> "$CB_FILE"
    if [ -n "$NEW_NAME" ]; then
      printf "        commit.author_name = b'%s'\n" "$NEW_NAME" >> "$CB_FILE"
      printf "        commit.committer_name = b'%s'\n" "$NEW_NAME" >> "$CB_FILE"
    fi
  done < "$AUTHOR_MAP_FILE"
  ARGV+=(--commit-callback "$CB_FILE")
fi

echo "Running git-filter-repo with args: ${ARGV[*]}"
git filter-repo "${ARGV[@]}"

echo "Filtering complete. Cleaned mirror at: $(pwd)"
echo "Clone it to inspect: git clone $(pwd) ../${MIRROR_DIR}-cleaned"
echo "When satisfied, push to a new remote for review or force-push to origin after coordination."
