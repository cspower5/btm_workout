#!/usr/bin/env bash
# Rotate ADMIN_PREVIEW_TOKEN in local .env and print the new token.
# Usage: ./scripts/rotate_admin_token.sh [--update-dotenv]
# If --update-dotenv is present, the script will replace ADMIN_PREVIEW_TOKEN in .env (creating .env from .env.example if needed).

set -euo pipefail

UPDATE_DOTENV=0
if [ "${1:-}" = "--update-dotenv" ]; then
  UPDATE_DOTENV=1
fi

NEW_TOKEN=$(openssl rand -hex 32)

echo "New ADMIN_PREVIEW_TOKEN: $NEW_TOKEN"

if [ "$UPDATE_DOTENV" -eq 1 ]; then
  if [ ! -f .env ]; then
    if [ -f .env.example ]; then
      cp .env.example .env
    else
      echo ".env.example not found; cannot create .env" >&2
      exit 1
    fi
  fi

  # Use awk to replace or add ADMIN_PREVIEW_TOKEN in .env
  if grep -q '^ADMIN_PREVIEW_TOKEN=' .env; then
    sed -i"" -e "s/^ADMIN_PREVIEW_TOKEN=.*/ADMIN_PREVIEW_TOKEN=$NEW_TOKEN/" .env 2>/dev/null || sed -i -e "s/^ADMIN_PREVIEW_TOKEN=.*/ADMIN_PREVIEW_TOKEN=$NEW_TOKEN/" .env
  else
    echo "ADMIN_PREVIEW_TOKEN=$NEW_TOKEN" >> .env
  fi

  echo ".env updated with new ADMIN_PREVIEW_TOKEN"
  echo "Remember to update the value in Render's environment variables and redeploy the service."
fi

exit 0
