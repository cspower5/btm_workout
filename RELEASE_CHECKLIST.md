# Release checklist: normalize-and-smoke

This checklist supports the release that includes:

- Normalizing exercise fields (`exercise_name` display + `name` normalized)
- Unique compound index on (name, body_part, equipment)
- Frontend fixes to use `/api/v1` endpoints and absolute API base
- Smoke tests (local in-process and networked)

Pre-merge checks
---------------

1. Code review
   - Ensure all changes in `main`->`release/normalize-and-smoke` are intended.
   - Confirm `flask_server.py` normalization logic and index usage.

2. Tests
   - All pytest tests should pass locally and on CI: `PYTHONPATH=. .venv/bin/pytest -q`.
   - Confirm `tests/test_normalization_insert.py` and other tests pass.

3. Smoke tests locally
   - Run `scripts/smoke_test_api_local.py` (in-process mongomock) — should PASS.
   - Start local server and run the networked smoke test:
     - `python flask_server.py &`
     - `python3 scripts/smoke_test_api.py --base-url http://127.0.0.1:5000`

4. Staging preview
   - Deploy branch to staging/preview and set `PREVIEW_URL` secret for CI if needed.
   - Run `python3 scripts/smoke_test_api.py --base-url <STAGING_URL>`.

Deployment (production)
-----------------------

1. Final preparations
   - Ensure `FLASK_ALLOW_DEV_ORIGINS=0` in production env.
   - Ensure `ADMIN_PREVIEW_TOKEN` is set and strong.
   - Rotate any secrets that were committed in backups (rotate Mongo credentials if needed).

2. Merge & deploy
   - Merge the PR into `main`.
   - Trigger your normal deployment pipeline (Render, Heroku, etc.).

3. Post-deploy smoke test
   - Run networked smoke test against production only with explicit consent:
     - `python3 scripts/smoke_test_api.py --base-url https://btm-workout.onrender.com --allow-prod`
   - Optionally use `--no-cleanup` to keep the inserted record for manual verification.

Rollback plan
-------------

1. If the deployment shows issues, revert the merge (create revert PR) and redeploy previous release.
2. If DB index or data normalization caused incidents, restore from `db_backups/exercises_index_replace_20251002T201525Z`.

Notes & caveats
----------------
- The API now stores `exercise_name` (original) and `name` (lowercased) — integrity checks rely on the normalized fields. Update consumers if you depend on case-sensitive lookups.
- The repo contains render backup JSON files that may include secrets; rotate any exposed credentials before long-term use.
