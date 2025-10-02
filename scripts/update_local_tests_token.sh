#!/usr/bin/env bash
# Update local .env and common test files with a new ADMIN_PREVIEW_TOKEN.
# Usage: ./scripts/update_local_tests_token.sh <new-token> [--update-dotenv]

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <new-token> [--update-dotenv]"
  exit 1
fi

NEW_TOKEN=$1
UPDATE_DOTENV=0
if [ "${2:-}" = "--update-dotenv" ]; then
  UPDATE_DOTENV=1
fi

# Files to update (add more if you have other local test scripts)
FILES=(
  "scripts/e2e_check.js"
  "scripts/insert_missing_body_parts_from_api.py"
)

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "Updating token in $f"
    # Replace any literal token-like strings if present (careful; this is best-effort)
    sed -i.bak -E "s/(Authorization:\s*Bearer\s*)[0-9a-fA-F]{32,}/\1$NEW_TOKEN/g" "$f" || true
    # cleanup backup
    rm -f "$f.bak"
  fi
done

if [ "$UPDATE_DOTENV" -eq 1 ]; then
  if [ ! -f .env ]; then
    if [ -f .env.example ]; then
      cp .env.example .env
    else
      echo ".env.example missing; cannot create .env" >&2
      exit 1
    fi
  fi

  if grep -q '^ADMIN_PREVIEW_TOKEN=' .env; then
    sed -i.bak -E "s/^ADMIN_PREVIEW_TOKEN=.*/ADMIN_PREVIEW_TOKEN=$NEW_TOKEN/" .env || true
  else
    echo "ADMIN_PREVIEW_TOKEN=$NEW_TOKEN" >> .env
  fi
  rm -f .env.bak
  echo ".env updated"
fi

echo "Done. Remember to update the value in Render and GitHub Secrets if used by CI."
