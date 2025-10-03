#!/usr/bin/env bash
set -euo pipefail

# Lightweight helper to create a project venv and install dev tooling
# Usage: ./scripts/setup-dev.sh

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

# Find a Python executable (prefer python3)
PYTHON=$(command -v python3 || command -v python || command -v py || true)
if [ -z "$PYTHON" ]; then
  echo "Error: no Python executable found (tried python3, python, py). Install Python 3 and retry." >&2
  exit 2
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv in .venv using $PYTHON"
  "$PYTHON" -m venv .venv
fi

# Activate and install
. .venv/bin/activate
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  echo "Installing requirements.txt"
  pip install -r requirements.txt
fi

# Ensure pre-commit is available for hooks
pip install pre-commit
pre-commit install || true

echo "Dev environment ready (.venv). Activate with: . .venv/bin/activate"
