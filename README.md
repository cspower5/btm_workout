# Break The Monotony Workout (btm_workout)

Small full-stack app: Flask backend + React/Vite frontend. This README covers quick local setup, migration, tests, and CI.

Quick start (backend)

1. Copy `.env.example` to `.env` and fill values (either `MONGO_URI` or `MONGO_USER`/`MONGO_PASS`/`MONGO_HOST`).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the server locally:

```bash
python flask_server.py
```

Database setup & seeding

```bash
python database_setup.py
python database_seeder.py
```

Canonical schema migration

If your DB contains legacy documents (fields `name` and `bodyPart`) run the migration script to rename to the canonical fields (`exercise_name`, `body_part`). Always backup your DB before running migrations.

Dry run:

```bash
python migrations/rename_legacy_fields.py --dry-run
```

Apply migration:

```bash
python migrations/rename_legacy_fields.py
```

Refreshing exercises from external API

Requires `RAPIDAPI_KEY` in env:

```bash
python -c "from database_refresh import insert_exercises_if_not_exist; print(insert_exercises_if_not_exist())"
```

Tests

Tests use `pytest` + `mongomock` to avoid touching a real database. To run tests:

```bash
pytest -q
```

CI

This repo includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs lint/tests on pushes and pull requests.

If anything is unclear or you want me to expand the migration (e.g., add backups, transactional behavior for MongoDB clusters), tell me which direction you prefer.

Environment variables
---------------------

The server reads configuration from environment variables. Create a local `.env` file (copy `.env.example`) for development and configure your deployment (Render, Heroku, etc.) with the same vars.

Important variables used by the app:

- `MONGO_URI` OR `MONGO_USER`, `MONGO_PASS`, `MONGO_HOST` - MongoDB connection. Either provide a full `MONGO_URI` or the user/pass/host triple.
- `RAPIDAPI_KEY` - required for `database_refresh.py` when fetching exercises from the external API.
- `FLASK_ALLOW_DEV_ORIGINS` - set to `1` to allow `http://localhost:5173` and `http://localhost:5174` as CORS origins for local development. In the repository `.env.example` and CI we default this to `0` (recommended for production). Set to `0` in CI/production to enforce production-only origins.
- `FLASK_CORS_DEBUG` - set to `1` to include a truncated request body preview in CORS-warning logs (useful for debugging unexpected client payloads).
- `ADMIN_PREVIEW_TOKEN` - a strong opaque token used to protect the management endpoint `/api/v1/admin/allowed_origins` which returns the currently configured allowed origins. Example usage:

	- To call the endpoint:

		Authorization: Bearer <ADMIN_PREVIEW_TOKEN>

	- This endpoint is intentionally readonly and only reveals the `ALLOWED_ORIGINS` list; do not store a weak token in production.

Security note: this token grants visibility into the server configuration only; keep it secret (treat it like a password) and rotate if it leaks.

Local development
-----------------

1. Copy `.env.example` to `.env` and fill in values.
2. Ensure `FLASK_ALLOW_DEV_ORIGINS=1` while running the frontend dev server (Vite) so the browser can call the local backend. For production deploys (Render), use `FLASK_ALLOW_DEV_ORIGINS=0`.

Run the local proxy and E2E smoke test
-------------------------------------

If you build the frontend and want to run the Puppeteer smoke test locally, use the repo-tracked WSGI proxy which serves the built `client/dist` at `/btm_workout` and proxies `/api/*` to the remote API (adds permissive CORS headers).

1. Build the frontend:

```bash
cd client
npm ci
npm run build
cd ..
```

2. Start the proxy (defaults to 127.0.0.1:5174):

```bash
python3 scripts/proxy_btm_server.py --host 127.0.0.1 --port 5174
```

3. Run the E2E smoke test (from repo root):

```bash
node scripts/e2e_check.js --base http://127.0.0.1:5174/btm_workout --headless --save-artifacts --timeout 30000
```

Artifacts (screenshot and HTML snapshot) will be saved to `/tmp/e2e_page_snapshot.png` and `/tmp/e2e_page_snapshot.html` by the script.

Deployments
-----------

When deploying to Render (or another host) set `FLASK_ALLOW_DEV_ORIGINS=0` in the environment to restrict allowed origins to the production static site. Also add `ADMIN_PREVIEW_TOKEN` to the service environment to enable the protected preview endpoint.
