## Quick orientation for AI coding agents

This repo is a small full-stack app: a Flask backend (Python) plus a React/Vite frontend in `client/`.
The backend uses MongoDB (pymongo) and environment variables for connection/config. Frontend is a static site deployed to GitHub Pages; backend is run as a WSGI app (Procfile uses gunicorn).

Key files to read first
- `flask_server.py` — main Flask app and all HTTP routes (API v1). Good for understanding available endpoints and response shapes.
- `btm_workout_db_connect.py` — database connection logic, uses `MONGO_URI` if present or builds a local URI from `MONGO_USER`, `MONGO_PASS`, `MONGO_HOST`.
- `database_refresh.py` — logic that fetches exercises from the RapidAPI `exercisedb` API and maps fields into the DB schema. Shows pagination, index handling, and insert logic.
- `database_setup.py` / `database_seeder.py` — create indexes and seed sample data. Useful when running locally.
- `client/` — React app produced with Vite. `client/package.json` contains dev/build/deploy scripts (deploy uses `gh-pages`).

Big-picture architecture and data flow
- Frontend (client/) calls REST endpoints under `/api/v1/*` exposed by `flask_server.py`.
- Backend persists exercises, body parts, and equipment in MongoDB (`exercises`, `body_parts`, `equipment` collections).
- `database_refresh.py` is the canonical source-of-truth for importing/updating exercises from the external API. It maps external fields into the app schema (e.g. `name` -> `exercise_name`, `bodyPart` -> `body_part`).
- `btm_workout_db_connect.py` centralizes connection behavior and should be used for reconnect logic (call `get_db()` rather than constructing new clients).

Important conventions and patterns (repo-specific)
- CORS: `flask_server.py` uses `@cross_origin(origins=['https://cspower5.github.io'])` on each route rather than a global `CORS(app)` call — preserve this when adding routes.
- Database field naming: the app uses both old-style and mapped field names in different places. Prefer the mapped schema used by `database_refresh.py` (exercise_name, body_part, equipment, target, difficulty, instructions).
- Index management: `database_setup.py` and `database_refresh.py` both create or drop indexes. Index names in this repo include `unique_exercise_index` and `unique_app_index` — be careful when modifying indexes and keep names consistent.
- Error handling: routes return JSON error objects + HTTP codes (e.g., 400, 404, 409, 500). Follow those shapes for new endpoints and tests.

Developer workflows and commands
- Backend (local): create a venv, install `requirements.txt`, set env vars (MONGO_URI or MONGO_USER/MONGO_PASS/MONGO_HOST, RAPIDAPI_KEY for refresh), then run:

```bash
python flask_server.py
```

- Run DB setup and seed (after DB connection env is available):

```bash
python database_setup.py
python database_seeder.py
```

- Refresh exercises from external API (requires `RAPIDAPI_KEY` in env):

```bash
python -c "from database_refresh import insert_exercises_if_not_exist; print(insert_exercises_if_not_exist())"
```

- Frontend (dev & deploy):

```bash
cd client
npm install
npm run dev          # local development
npm run build        # build for production
npm run deploy       # uses gh-pages to publish dist to GitHub Pages
```

- Production server (Heroku-like via Procfile): the app expects to be served with gunicorn:

```text
web: gunicorn --bind 0.0.0.0:$PORT flask_server:app
```

Integration points and external dependencies
- MongoDB: connection via `MONGO_URI` (Atlas) or local user/pass/host. `btm_workout_db_connect.py` performs a ping on startup.
- RapidAPI ExerciseDB: `database_refresh.py` requires `RAPIDAPI_KEY` and calls `https://exercisedb.p.rapidapi.com/exercises` (paginated). The refresh maps and inserts documents with `insert_many(..., ordered=False)` to tolerate duplicates.
- Frontend uses `https://cspower5.github.io` as an allowed origin; tests or local dev may need adjusted CORS allowed origins.

What to watch for when editing code
- Keep route-level CORS decorators on new endpoints so GitHub Pages front-end can talk to the local/prod backend.
- Prefer `get_db()` from `btm_workout_db_connect.py` to obtain the DB instance (handles reconnects). Avoid creating new MongoClient instances directly.
- When changing DB schema/field names, update `database_refresh.py` mapping and index definitions in `database_setup.py` and any code referencing those fields (search for `bodyPart`, `exercise_name`, `body_part`).
- Avoid assuming `_id` is returned — many endpoints use projection to remove `_id` (e.g., `{'_id': 0}`). Mirror that behavior for public API responses.

Examples (copy/paste snippets for common tasks)
- Get DB and insert a document safely:

```python
from btm_workout_db_connect import get_db
db = get_db()
db.exercises.insert_one({"exercise_name": "Push Up", "body_part": "Chest", "equipment": "Body Weight"})
```

- Call the refresh function and print result:

```python
from database_refresh import insert_exercises_if_not_exist
print(insert_exercises_if_not_exist())
```

Files and symbols to reference in code navigation
- `flask_server.py` (API route handlers)
- `btm_workout_db_connect.py` (connect_db, get_db)
- `database_refresh.py` (insert_exercises_if_not_exist)
- `database_setup.py`, `database_seeder.py` (indexes, sample data)
- `client/package.json` (frontend scripts & deploy)

If you edit this file
- Keep entries concise (20-50 lines). Update the bullet points above if you change how the DB connects, the deploy target, or CORS policy.

Questions for the repo owner
- Which MongoDB deployment should be considered canonical for CI / tests (Atlas MONGO_URI or local dev)?
- Do you want new API routes to use the mapped field names (exercise_name/body_part) exclusively, or keep backward-compatible aliases?

If anything in this doc is wrong or missing, tell me what to clarify and I will update it.
