#!/usr/bin/env bash
set -euo pipefail

# Simple backup script.
# Prefer mongodump if available; otherwise fall back to export_db_json.py (JSON dumps).

OUTDIR=${1:-./db_backups}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEST="$OUTDIR/backup_$TIMESTAMP"
mkdir -p "$DEST"

if command -v mongodump >/dev/null 2>&1; then
  echo "Using mongodump to backup database to $DEST"
  # mongodump will pick up MONGO_URI from env if set
  mongodump --archive="$DEST/dump.archive" --gzip
  echo "mongodump finished: $DEST/dump.archive.gz"
else
  echo "mongodump not found; falling back to export_db_json.py"
  PYTHONPATH=. /home/cspower/Python/projects/btm_workout/.venv/bin/python scripts/export_db_json.py --outdir "$DEST"
  echo "JSON export finished in $DEST"
fi

echo "Backup complete: $DEST"
