#!/usr/bin/env bash
set -euo pipefail

# purge_and_prepare.sh
# Create a mirror clone, run git-filter-repo to remove specified paths, optionally remap authors,
# and output a cleaned mirror for inspection. This script will NOT push to any remote.

usage() {
  cat <<EOF
Usage: $0 <path-to-remove> [author-map.csv] [mirror-dir]

Examples:
  # Remove a virtualenv directory from history
  $0 my_jupyter_env

  # Remove and remap authors (CSV: old_email,new_name,new_email)
  $0 my_jupyter_env ./author-map.csv tmp-repo-mirror

Notes:
 - Requires git-filter-repo: pip install git-filter-repo
 - This script creates a bare mirror at <mirror-dir>.git and runs the filter there.
 - It does NOT push any changes to origin. You must inspect and push the cleaned repo manually.
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

REMOVE_PATH="$1"
AUTHOR_MAP_FILE="${2:-}" 
MIRROR_DIR="${3:-./tmp-repo-mirror}"

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "ERROR: git-filter-repo is not installed. Install it with: pip install git-filter-repo"
  exit 1
fi

if [ -d "${MIRROR_DIR}.git" ]; then
  echo "ERROR: target mirror dir ${MIRROR_DIR}.git already exists. Remove or choose another directory." >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
echo "Creating bare mirror of $ROOT at ${MIRROR_DIR}.git"
git clone --mirror "$ROOT" "${MIRROR_DIR}.git"

cd "${MIRROR_DIR}.git"

FILTER_CMD=(git filter-repo --force --invert-paths --path "$REMOVE_PATH")

if [ -n "$AUTHOR_MAP_FILE" ] && [ -f "$AUTHOR_MAP_FILE" ]; then
  echo "Author map provided: $AUTHOR_MAP_FILE — building commit-callback"
  # Build a one-line commit-callback with semicolon-separated if-statements
  CALLBACK=""
  while IFS=',' read -r OLD_EMAIL NEW_NAME NEW_EMAIL; do
    # Trim whitespace
    OLD_EMAIL="$(echo "$OLD_EMAIL" | xargs)"
    NEW_NAME="$(echo "$NEW_NAME" | xargs)"
    NEW_EMAIL="$(echo "$NEW_EMAIL" | xargs)"
    if [ -z "$OLD_EMAIL" ] || [ -z "$NEW_EMAIL" ]; then
      echo "Skipping invalid line in author-map: $OLD_EMAIL,$NEW_NAME,$NEW_EMAIL"
      continue
    fi
    # Build conditional block
    BLOCK="if commit.author_email == b\"$OLD_EMAIL\": commit.author_email = b\"$NEW_EMAIL\"; commit.committer_email = b\"$NEW_EMAIL\""
    if [ -n "$NEW_NAME" ]; then
      BLOCK="$BLOCK; commit.author_name = b\"$NEW_NAME\"; commit.committer_name = b\"$NEW_NAME\""
    fi
    # Append
    if [ -z "$CALLBACK" ]; then
      CALLBACK="$BLOCK"
    else
      CALLBACK="$CALLBACK; $BLOCK"
    fi
  done < "$AUTHOR_MAP_FILE"

  if [ -n "$CALLBACK" ]; then
    echo "Running git-filter-repo with author remapping (commit-callback)"
    FILTER_CMD+=(--commit-callback "$CALLBACK")
  fi
fi

echo "Running: ${FILTER_CMD[*]}"
# Execute the filter command
eval "${FILTER_CMD[*]}"

echo "Filter complete. Cleaned mirror is at: $(pwd)"
echo
echo "To inspect the cleaned mirror as a normal repo, run:" 
echo "  git clone $(pwd) ../${MIRROR_DIR}-cleaned"
echo "Then inspect, run tests, and when satisfied, push the cleaned repo to a new remote with force (coordinate with team):"
echo "  cd ../${MIRROR_DIR}-cleaned"
echo "  git remote add cleaned <NEW_REMOTE_URL>"
echo "  git push cleaned --all --force"
echo "  git push cleaned --tags --force"
echo
echo "Read HISTORY_REWRITE.md for more guidance and caveats."
#!/usr/bin/env bash
set -euo pipefail

# purge_and_prepare.sh
# Create a mirror clone, run git-filter-repo to remove specified paths, optionally remap authors,
# and output a cleaned mirror for inspection. This script will NOT push to any remote.

usage() {
  cat <<EOF
Usage: $0 <path-to-remove> [author-map.csv] [mirror-dir]

Examples:
  # Remove a virtualenv directory from history
  $0 my_jupyter_env

  # Remove and remap authors (CSV: old_email,new_name,new_email)
  $0 my_jupyter_env ./author-map.csv tmp-repo-mirror

Notes:
 - Requires git-filter-repo: pip install git-filter-repo
 - This script creates a bare mirror at <mirror-dir>.git and runs the filter there.
 - It does NOT push any changes to origin. You must inspect and push the cleaned repo manually.
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

REMOVE_PATH="$1"
AUTHOR_MAP_FILE="${2:-}" 
MIRROR_DIR="${3:-./tmp-repo-mirror}"

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "ERROR: git-filter-repo is not installed. Install it with: pip install git-filter-repo"
  exit 1
fi

if [ -d "${MIRROR_DIR}.git" ]; then
  echo "ERROR: target mirror dir ${MIRROR_DIR}.git already exists. Remove or choose another directory." >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
echo "Creating bare mirror of $ROOT at ${MIRROR_DIR}.git"
git clone --mirror "$ROOT" "${MIRROR_DIR}.git"

cd "${MIRROR_DIR}.git"

FILTER_CMD=(git filter-repo --force --invert-paths --path "$REMOVE_PATH")

if [ -n "$AUTHOR_MAP_FILE" ] && [ -f "$AUTHOR_MAP_FILE" ]; then
  echo "Author map provided: $AUTHOR_MAP_FILE — building commit-callback"
  # Build a one-line commit-callback with semicolon-separated if-statements
  CALLBACK=""
  while IFS=',' read -r OLD_EMAIL NEW_NAME NEW_EMAIL; do
    # Trim whitespace
    OLD_EMAIL="$(echo "$OLD_EMAIL" | xargs)"
    NEW_NAME="$(echo "$NEW_NAME" | xargs)"
    NEW_EMAIL="$(echo "$NEW_EMAIL" | xargs)"
    if [ -z "$OLD_EMAIL" ] || [ -z "$NEW_EMAIL" ]; then
      echo "Skipping invalid line in author-map: $OLD_EMAIL,$NEW_NAME,$NEW_EMAIL"
      continue
    fi
    # Build conditional block
    BLOCK="if commit.author_email == b\"$OLD_EMAIL\": commit.author_email = b\"$NEW_EMAIL\"; commit.committer_email = b\"$NEW_EMAIL\""
    if [ -n "$NEW_NAME" ]; then
      BLOCK="$BLOCK; commit.author_name = b\"$NEW_NAME\"; commit.committer_name = b\"$NEW_NAME\""
    fi
    # Append
    if [ -z "$CALLBACK" ]; then
      CALLBACK="$BLOCK"
    else
      CALLBACK="$CALLBACK; $BLOCK"
    fi
  done < "$AUTHOR_MAP_FILE"

  if [ -n "$CALLBACK" ]; then
    echo "Running git-filter-repo with author remapping (commit-callback)"
    FILTER_CMD+=(--commit-callback "$CALLBACK")
  fi
fi

echo "Running: ${FILTER_CMD[*]}"
# Execute the filter command
eval "${FILTER_CMD[*]}"

echo "Filter complete. Cleaned mirror is at: $(pwd)"
echo
echo "To inspect the cleaned mirror as a normal repo, run:" 
echo "  git clone $(pwd) ../${MIRROR_DIR}-cleaned"
echo "Then inspect, run tests, and when satisfied, push the cleaned repo to a new remote with force (coordinate with team):"
echo "  cd ../${MIRROR_DIR}-cleaned"
echo "  git remote add cleaned <NEW_REMOTE_URL>"
echo "  git push cleaned --all --force"
echo "  git push cleaned --tags --force"
echo
echo "Read HISTORY_REWRITE.md for more guidance and caveats."
#!/usr/bin/env bash
set -euo pipefail

# purge_and_prepare.sh
# Create a mirror clone, run git-filter-repo to remove specified paths, optionally remap authors,
# and output a cleaned mirror for inspection. This script will NOT push to any remote.

usage() {
  cat <<EOF
Usage: $0 <path-to-remove> [author-map.csv] [mirror-dir]

Examples:
  # Remove a virtualenv directory from history
  $0 my_jupyter_env

  # Remove and remap authors (CSV: old_email,new_name,new_email)
  $0 my_jupyter_env ./author-map.csv tmp-repo-mirror

Notes:
 - Requires git-filter-repo: pip install git-filter-repo
 - This script creates a bare mirror at <mirror-dir>.git and runs the filter there.
 - It does NOT push any changes to origin. You must inspect and push the cleaned repo manually.
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

REMOVE_PATH="$1"
AUTHOR_MAP_FILE="${2:-}" 
MIRROR_DIR="${3:-./tmp-repo-mirror}"

if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "ERROR: git-filter-repo is not installed. Install it with: pip install git-filter-repo"
  exit 1
fi

if [ -d "${MIRROR_DIR}.git" ]; then
  echo "ERROR: target mirror dir ${MIRROR_DIR}.git already exists. Remove or choose another directory." >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
echo "Creating bare mirror of $ROOT at ${MIRROR_DIR}.git"
git clone --mirror "$ROOT" "${MIRROR_DIR}.git"

cd "${MIRROR_DIR}.git"

FILTER_CMD=(git filter-repo --force --invert-paths --path "$REMOVE_PATH")

if [ -n "$AUTHOR_MAP_FILE" ] && [ -f "$AUTHOR_MAP_FILE" ]; then
  echo "Author map provided: $AUTHOR_MAP_FILE — building commit-callback"
  # Build a one-line commit-callback with semicolon-separated if-statements
  CALLBACK=""
  while IFS=',' read -r OLD_EMAIL NEW_NAME NEW_EMAIL; do
    # Trim whitespace
    OLD_EMAIL="$(echo "$OLD_EMAIL" | xargs)"
    NEW_NAME="$(echo "$NEW_NAME" | xargs)"
    NEW_EMAIL="$(echo "$NEW_EMAIL" | xargs)"
    if [ -z "$OLD_EMAIL" ] || [ -z "$NEW_EMAIL" ]; then
      echo "Skipping invalid line in author-map: $OLD_EMAIL,$NEW_NAME,$NEW_EMAIL"
      continue
    fi
    # Build conditional block
    BLOCK="if commit.author_email == b\"$OLD_EMAIL\": commit.author_email = b\"$NEW_EMAIL\"; commit.committer_email = b\"$NEW_EMAIL\""
    if [ -n "$NEW_NAME" ]; then
      BLOCK="$BLOCK; commit.author_name = b\"$NEW_NAME\"; commit.committer_name = b\"$NEW_NAME\""
    fi
    # Append
    if [ -z "$CALLBACK" ]; then
      CALLBACK="$BLOCK"
    else
      CALLBACK="$CALLBACK; $BLOCK"
    fi
  done < "$AUTHOR_MAP_FILE"

  if [ -n "$CALLBACK" ]; then
    echo "Running git-filter-repo with author remapping (commit-callback)"
    FILTER_CMD+=(--commit-callback "$CALLBACK")
  fi
fi

echo "Running: ${FILTER_CMD[*]}"
# Execute the filter command
eval "${FILTER_CMD[*]}"

echo "Filter complete. Cleaned mirror is at: $(pwd)"
echo
echo "To inspect the cleaned mirror as a normal repo, run:" 
echo "  git clone $(pwd) ../${MIRROR_DIR}-cleaned"
echo "  cd ../${MIRROR_DIR}-cleaned"
echo "  # run tests and inspect history, tags, authors, etc."
echo
echo "When satisfied, push the cleaned repo to a new remote (do NOT push to origin without coordination):"
echo "  git remote add cleaned https://github.com/<you>/<repo>-cleaned.git"
echo "  git push cleaned --all --force"
echo "  git push cleaned --tags --force"
echo
echo "Read HISTORY_REWRITE.md for more guidance and caveats."
