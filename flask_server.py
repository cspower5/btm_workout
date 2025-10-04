from flask import Flask, jsonify, request
from flask_cors import cross_origin  # <-- Keep CORS and Import cross_origin
import btm_workout_db_connect as db_connect
from database_refresh import insert_exercises_if_not_exist
from pymongo.errors import DuplicateKeyError

import os

# Production-only allowed origin
PROD_ORIGINS = ["https://cspower5.github.io"]

# Developer: set FLASK_ALLOW_DEV_ORIGINS=1 in your local env to allow local dev origins
_allow_dev = os.getenv("FLASK_ALLOW_DEV_ORIGINS", "1").lower() in ("1", "true", "yes")

# Tightened dev origins (only exact ports used for dev Vite server)
DEV_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    # Playwright/CI often serves the built site at port 8080 during tests
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# Final allowed origins: production plus dev (if enabled)
ALLOWED_ORIGINS = PROD_ORIGINS + (DEV_ORIGINS if _allow_dev else [])


# Log CORS-origin rejections: browsers enforce CORS, but we can surface unexpected origins
def log_cors_origin_mismatch():
    origin = request.headers.get("Origin")
    if origin:
        # If origin isn't allowed, log a WARNING with request context to help debugging
        if origin not in ALLOWED_ORIGINS:
            # Include remote address and optionally a truncated request body when debugging
            remote = request.remote_addr
            body_preview = None
            if os.getenv("FLASK_CORS_DEBUG", "0").lower() in ("1", "true", "yes"):
                try:
                    raw = request.get_data(as_text=True) or ""
                    body_preview = (raw[:1000] + "...") if len(raw) > 1000 else raw
                except Exception:
                    body_preview = "<unavailable>"

            msg = f"CORS request from origin {origin} for {request.method} {request.path} - not in ALLOWED_ORIGINS; remote={remote}"
            if body_preview is not None:
                msg += f"; body_preview={body_preview}"
            app.logger.warning(msg)


# --- Initialization ---
app = Flask(__name__)
# NOTE: The global CORS(app) is REMOVED. @cross_origin is used on each route for guaranteed functionality.


# Register before_request CORS logger (helps surface CORS origin rejections in server logs)
@app.before_request
def _log_cors_wrapper():
    return log_cors_origin_mismatch()


# --- API Routes (v1) ---


@app.route("/api/v1/insert_exercise", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_insert_exercise():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500

    try:
        data = request.json
        exercises_collection = db["exercises"]

        # Accept legacy aliases and normalize to canonical payload keys:
        # - "name" -> "exercise_name"
        # - "bodyPart" -> "body_part"
        # Enforce canonical payload: expect `exercise_name`, `body_part`, `equipment`, `target`
        if data is None:
            return jsonify({"error": "Invalid or missing JSON body."}), 400

        # Normalize aliases into canonical names
        if "name" in data and "exercise_name" not in data:
            data["exercise_name"] = data.pop("name")
        if "bodyPart" in data and "body_part" not in data:
            data["body_part"] = data.pop("bodyPart")

        required = ("exercise_name", "body_part", "equipment", "target")
        if not all(k in data for k in required):
            return (
                jsonify({"error": f"Missing required fields. Required: {required}"}),
                400,
            )

        # Insert using canonical schema
        # Remove unrelated/legacy fields if present
        data.pop("category", None)
        data.pop("bodyPart", None)
        data.pop("name", None)

        # Ensure backward compatibility: include legacy `name` field so
        # the existing unique index on (name, body_part, equipment) will
        # be effective. Normalize canonical fields to lowercase to avoid
        # duplicates caused by case differences (e.g., 'Squat' vs 'squat').
        def _safe_strip(val):
            try:
                return val.strip() if isinstance(val, str) else val
            except Exception:
                return val

        # Preserve the original exercise_name for display, but maintain
        # lowercased fields used for uniqueness/indexing so case-variants
        # don't create duplicate entries.
        original_ex_name = _safe_strip(data.get("exercise_name"))
        bp = _safe_strip(data.get("body_part"))
        eq = _safe_strip(data.get("equipment"))

        # Normalized values (lowercased) used by the unique index
        norm_name = (
            original_ex_name.lower()
            if isinstance(original_ex_name, str)
            else original_ex_name
        )
        norm_bp = bp.lower() if isinstance(bp, str) else bp
        norm_eq = eq.lower() if isinstance(eq, str) else eq

        # Store both display and normalized/index fields
        data["exercise_name"] = original_ex_name
        data["name"] = norm_name
        data["body_part"] = norm_bp
        data["equipment"] = norm_eq
        existing = exercises_collection.find_one(
            {
                "$or": [
                    {
                        "name": data["name"],
                        "body_part": data["body_part"],
                        "equipment": data["equipment"],
                    },
                    {
                        "exercise_name": original_ex_name,
                        "body_part": data["body_part"],
                        "equipment": data["equipment"],
                    },
                ]
            }
        )
        if existing:
            return (
                jsonify(
                    {
                        "error": "An exercise with this name, body part, and equipment already exists."
                    }
                ),
                409,
            )

        result = exercises_collection.insert_one(data)

        return jsonify(
            {"message": "Exercise inserted successfully", "id": str(result.inserted_id)}
        )

    except DuplicateKeyError:
        return (
            jsonify(
                {
                    "error": "An exercise with this name, body part, and equipment already exists."
                }
            ),
            409,
        )

    except Exception as e:
        print(f"Error inserting exercise: {e}")
        return jsonify({"error": "Failed to insert exercise."}), 500


# API endpoint to get 3 random exercises for a selected body part
@app.route("/api/v1/get_random_exercises", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_get_random_exercises():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500

    try:
        data = request.json
        # Accept either `bodyPart` (frontend legacy) or `body_part` (canonical)
        selected_body_part = None
        if data is not None:
            selected_body_part = data.get("body_part") or data.get("bodyPart")

        # Normalize and validate number of exercises: accept numExercises (camelCase)
        # or num_exercises (snake_case). Coerce to int and enforce safe bounds.
        raw_num = None
        if data:
            raw_num = data.get("numExercises")
            if raw_num is None:
                raw_num = data.get("num_exercises")

        try:
            num_exercises = int(raw_num) if raw_num is not None else 4
        except (TypeError, ValueError):
            return (
                jsonify({"error": "Invalid 'numExercises', must be an integer."}),
                400,
            )

        # Enforce reasonable bounds to avoid huge sampling requests from clients
        num_exercises = max(1, min(num_exercises, 20))
    except Exception:
        return jsonify({"error": "Invalid request format."}), 400

    if not selected_body_part:
        return jsonify({"error": "No body part provided."}), 400

    # Use case-insensitive matching against the canonical `body_part` field
    try:
        # Match exercises where either the canonical `body_part` OR the
        # legacy `bodyPart` (some older docs) case-insensitively equals
        # the requested body part. This makes the endpoint resilient to
        # mixed document schemas in the database.
        pipeline = [
            {
                "$match": {
                    "$expr": {
                        "$or": [
                            {
                                "$eq": [
                                    {"$toLower": {"$ifNull": ["$body_part", ""]}},
                                    selected_body_part.lower(),
                                ]
                            },
                            {
                                "$eq": [
                                    {"$toLower": {"$ifNull": ["$bodyPart", ""]}},
                                    selected_body_part.lower(),
                                ]
                            },
                        ]
                    }
                }
            },
            {"$sample": {"size": int(num_exercises)}},
            {"$project": {"_id": 0}},  # Exclude MongoDB's _id field
        ]

        random_exercises = list(db.exercises.aggregate(pipeline))

        if not random_exercises:
            return (
                jsonify(
                    {
                        "error": f"No exercises found for body part: {selected_body_part}."
                    }
                ),
                404,
            )

        # Transform canonical DB fields into the legacy frontend shape so the
        # existing client UI (which expects `name`, `bodyPart`, `reps`, `sets`)
        # will display values correctly. Keep original fields where present.
        def transform(doc):
            return {
                # frontend expects `name`; canonical DB has `exercise_name`
                "name": doc.get("exercise_name") or doc.get("name"),
                # frontend expects `bodyPart`; canonical DB has `body_part`
                "bodyPart": doc.get("body_part") or doc.get("bodyPart"),
                # equipment is consistent
                "equipment": doc.get("equipment"),
                # preserve target/instructions as modern fields too
                "target": doc.get("target"),
                "instructions": doc.get("instructions"),
            }

        transformed = [transform(d) for d in random_exercises]
        return jsonify(transformed)
    except Exception as e:
        print(f"Error getting random exercises: {e}")
        return jsonify({"error": "Failed to retrieve exercises."}), 500


# API endpoint to refresh the database with new exercises
@app.route("/api/v1/refresh_db", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_refresh_db():
    try:
        # Calls the external API logic from database_refresh.py
        count = insert_exercises_if_not_exist()
        return jsonify(
            {"message": f"Database refresh complete. {count} new exercises added."}
        )
    except Exception as e:
        return jsonify({"error": f"Failed to refresh database: {e}"}), 500


# API endpoint to get a single exercise by its name
@app.route("/api/v1/exercise/<string:name>", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_get_exercise_details(name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        exercises_collection = db["exercises"]
        # Accept queries by display name or normalized name. Normalize the
        # incoming parameter to lowercase and attempt both lookups so existing
        # clients that pass the original cased name continue to work.
        try:
            norm_query = name.strip().lower()
        except Exception:
            norm_query = name

        exercise = exercises_collection.find_one(
            {"$or": [{"exercise_name": name}, {"name": norm_query}]}, {"_id": 0}
        )

        if exercise:
            return jsonify(exercise)

        return jsonify({"error": "Exercise not found."}), 404

    except Exception:
        return jsonify({"error": "Failed to retrieve exercise details."}), 500


# API endpoint to handle adding a new body part
@app.route("/api/v1/add_body_part", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_add_body_part():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        data = request.json
        name = data.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' field."}), 400
        # Normalize: strip and lowercase to avoid case-variant duplicates
        norm_name = name.strip().lower()
        # Ensure unique index on name exists for body_parts (idempotent)
        try:
            db.body_parts.create_index(
                [("name", 1)], unique=True, name="unique_body_parts_name"
            )
        except Exception:
            pass
        result = db.body_parts.insert_one({"name": norm_name})
        return jsonify(
            {"message": "Body part added successfully", "id": str(result.inserted_id)}
        )
    except DuplicateKeyError:
        return jsonify({"error": "This body part already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Failed to add body part: {str(e)}"}), 500


# API endpoint to handle adding new equipment
@app.route("/api/v1/add_equipment", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_add_equipment():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        data = request.json
        name = data.get("name")
        if not name:
            return jsonify({"error": "Missing 'name' field."}), 400
        # Normalize: strip and lowercase to avoid case-variant duplicates
        norm_name = name.strip().lower()
        # Ensure unique index on name exists for equipment (idempotent)
        try:
            db.equipment.create_index(
                [("name", 1)], unique=True, name="unique_equipment_name"
            )
        except Exception:
            pass
        result = db.equipment.insert_one({"name": norm_name})
        return jsonify(
            {"message": "Equipment added successfully", "id": str(result.inserted_id)}
        )
    except DuplicateKeyError:
        return jsonify({"error": "This equipment already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Failed to add equipment: {str(e)}"}), 500


# API endpoint to delete an exercise by its name
@app.route("/api/v1/delete_exercise/<path:name>", methods=["DELETE"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_delete_exercise(name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        # Delete by canonical field `exercise_name`
        result = db.exercises.delete_one({"exercise_name": name})
        if result.deleted_count == 1:
            return jsonify({"message": f"Exercise '{name}' deleted successfully."})
        return jsonify({"error": "Exercise not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete exercise: {str(e)}"}), 500


# API endpoint to delete a body part by its name
@app.route("/api/v1/delete_body_part/<string:name>", methods=["DELETE"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_delete_body_part(name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.body_parts.delete_one({"name": name})

        # Also delete associated exercises
        exercises_deleted = db.exercises.delete_many({"bodyPart": name})

        if result.deleted_count == 1:
            return jsonify(
                {
                    "message": f"Body part '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
                }
            )
        else:
            return jsonify({"error": "Body part not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete body part: {str(e)}"}), 500


# API endpoint to delete equipment by its name
@app.route("/api/v1/delete_equipment/<string:name>", methods=["DELETE"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_delete_equipment(name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.equipment.delete_one({"name": name})

        # Also delete associated exercises
        exercises_deleted = db.exercises.delete_many({"equipment": name})

        if result.deleted_count == 1:
            return jsonify(
                {
                    "message": f"Equipment '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
                }
            )
        else:
            return jsonify({"error": "Equipment not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete equipment: {str(e)}"}), 500


# API endpoint to get a list of all body parts
@app.route("/api/v1/body_parts_list", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_body_parts_list():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        # FIX: Use Aggregation to force all names to lowercase and return unique list
        # Only include documents where 'name' exists and is a string so $toLower is safe
        pipeline = [
            {
                "$match": {
                    "name": {"$exists": True, "$type": "string", "$nin": ["", None]}
                }
            },
            {"$group": {"_id": {"$toLower": "$name"}}},
            {"$sort": {"_id": 1}},
        ]

        names_cursor = db.body_parts.aggregate(pipeline)

        # The result is the unique lowercase name (stored in _id)
        body_parts = [doc["_id"] for doc in names_cursor]
        return jsonify(body_parts)
    except Exception as e:
        # NOTE: This endpoint still fails on bad data, but we rely on a clean deploy now.
        return jsonify({"error": f"Failed to retrieve body parts list: {str(e)}"}), 500


# API endpoint to get a list of all equipment
@app.route("/api/v1/equipment_list", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_equipment_list():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        # FIX: Use Aggregation to force all names to lowercase and return unique list
        # Only include documents where 'name' exists and is a string so $toLower is safe
        pipeline = [
            {
                "$match": {
                    "name": {"$exists": True, "$type": "string", "$nin": ["", None]}
                }
            },
            {"$group": {"_id": {"$toLower": "$name"}}},
            {"$sort": {"_id": 1}},
        ]

        names_cursor = db.equipment.aggregate(pipeline)

        # The result is the unique lowercase name (stored in _id)
        equipment_list = [doc["_id"] for doc in names_cursor]
        return jsonify(equipment_list)
    except Exception as e:
        # Defensive fallback: aggregation may fail on corrupt/mixed-type data.
        app.logger.warning(
            "Aggregation failed for equipment_list, falling back to safe scan: %s", e
        )
        try:
            names = set()
            for doc in db.equipment.find({}, {"name": 1}):
                name = doc.get("name")
                if name is None:
                    continue
                if not isinstance(name, str):
                    try:
                        name = str(name)
                    except Exception:
                        continue
                names.add(name.lower())
            equipment_list = sorted(names)
            return jsonify(equipment_list)
        except Exception:
            app.logger.exception("Fallback scan also failed for equipment_list")
            return (
                jsonify({"error": f"Failed to retrieve equipment list: {str(e)}"}),
                500,
            )


# API endpoint to get a list of all exercises
@app.route("/api/v1/exercises_list", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_exercises_list():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        exercises_list = list(db.exercises.find({}, {"_id": 0}))
        return jsonify(exercises_list)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve exercises list: {str(e)}"}), 500


# API endpoint to get a list of all difficulties
@app.route("/api/v1/difficulties", methods=["GET"])
@cross_origin(origins=["https://cspower5.github.io"])  # <--- CORS FIX
def api_difficulties():
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        # FIX: Use Aggregation to force all difficulties to lowercase and return unique list
        # Only include documents where 'difficulty' is present and a string to avoid $toLower on other types
        pipeline = [
            {
                "$match": {
                    "difficulty": {
                        "$exists": True,
                        "$type": "string",
                        "$nin": [None, ""],
                    }
                }
            },
            {"$group": {"_id": {"$toLower": "$difficulty"}}},
            {"$sort": {"_id": 1}},
        ]

        difficulties_cursor = db.exercises.aggregate(pipeline)

        # The result is the unique lowercase name (stored in _id)
        difficulties = [doc["_id"] for doc in difficulties_cursor]

        return jsonify(difficulties)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve difficulties: {str(e)}"}), 500


# --- Error Handling ---


@app.errorhandler(404)
@cross_origin(origins=["https://cspower5.github.io"])  # <--- CORS FIX
def not_found(error):
    return (
        jsonify(
            {
                "error": "Not Found",
                "message": "The requested URL was not found on the server.",
            }
        ),
        404,
    )


@app.errorhandler(500)
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def internal_error(error):
    app.logger.error("Server Error: %s", error)
    return (
        jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred on the server.",
            }
        ),
        500,
    )


# --- Health Check ---
@app.route("/api/v1/health", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_health_check():
    return jsonify({"status": "ok", "message": "API is running and healthy."}), 200


# Management endpoint: preview configured allowed origins
# Protect with ADMIN_PREVIEW_TOKEN environment variable (use a strong token)
@app.route("/api/v1/admin/allowed_origins", methods=["GET"])
def api_admin_allowed_origins():
    token = os.getenv("ADMIN_PREVIEW_TOKEN")
    auth = request.headers.get("Authorization")
    if not token or not auth or auth.strip() != f"Bearer {token}":
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"allowed_origins": ALLOWED_ORIGINS}), 200


# --- Run Server (Production/Development) ---
if __name__ == "__main__":
    # Initial connection attempt when running locally
    db_connect.connect_db()
    app.run(debug=True, port=5000)
