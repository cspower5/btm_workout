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
