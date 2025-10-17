import os
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin  # <-- Keep CORS and Import cross_origin
import btm_workout_db_connect as db_connect
from database_refresh import insert_exercises_if_not_exist
from pymongo.errors import DuplicateKeyError
from auth import init_auth, register_user, login_user, verify_token, require_auth
from flask_jwt_extended import jwt_required, get_jwt_identity
from user_data_manager import UserDataManager, optional_auth, get_current_user_id

# Production-only allowed origin
PROD_ORIGINS = ["https://cspower5.github.io"]

# Developer: set FLASK_ALLOW_DEV_ORIGINS=1 in your local env to allow local dev origins
_allow_dev = os.getenv("FLASK_ALLOW_DEV_ORIGINS", "1").lower() in ("1", "true", "yes")

# Tightened dev origins (only exact ports used for dev Vite server)
DEV_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://192.168.40.88:5174",
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

# Apply your CORS settings to the entire app
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}})

# Initialize JWT authentication
jwt = init_auth(app)


# Register before_request CORS logger (helps surface CORS origin rejections in server logs)
@app.before_request
def _log_cors_wrapper():
    return log_cors_origin_mismatch()


# --- API Routes (v1) ---


# @app.route("/api/v1/insert_exercise", methods=["POST"])
@app.route("/v1/insert_exercise", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@require_auth  # Require authentication for adding exercises
def api_insert_exercise(user):
    try:
        data = request.json
        if data is None:
            return jsonify({"error": "Invalid or missing JSON body."}), 400

        # Initialize user data manager
        user_data_manager = UserDataManager()

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

        # Remove unrelated/legacy fields if present
        data.pop("category", None)
        data.pop("bodyPart", None)
        data.pop("name", None)

        # Normalize fields for consistency
        def _safe_strip(val):
            try:
                return val.strip() if isinstance(val, str) else val
            except Exception:
                return val

        original_ex_name = _safe_strip(data.get("exercise_name"))
        bp = _safe_strip(data.get("body_part"))
        eq = _safe_strip(data.get("equipment"))

        # Normalized values (lowercased) used for uniqueness checking
        norm_name = (
            original_ex_name.lower()
            if isinstance(original_ex_name, str)
            else original_ex_name
        )
        norm_bp = bp.lower() if isinstance(bp, str) else bp
        norm_eq = eq.lower() if isinstance(eq, str) else eq

        # Store both display and normalized fields
        data["exercise_name"] = original_ex_name
        data["name"] = norm_name
        data["body_part"] = norm_bp
        data["equipment"] = norm_eq

        # Check for duplicates in user's exercises (including public exercises)
        user_id = user[
            "id"
        ]  # Use the user object passed by the decorator (note: it's 'id', not '_id')
        existing_exercises = user_data_manager.get_exercises(user_id)

        for existing in existing_exercises:
            if (
                existing.get("name") == norm_name
                and existing.get("body_part") == norm_bp
                and existing.get("equipment") == norm_eq
            ):
                return (
                    jsonify(
                        {
                            "error": "An exercise with this name, body part, and equipment already exists."
                        }
                    ),
                    409,
                )

        # Add exercise with user isolation
        result = user_data_manager.add_exercise(data, user_id)

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


# API endpoint to get random exercises for a selected body part
# @app.route("/api/v1/get_random_exercises", methods=["POST"])
@app.route("/v1/get_random_exercises", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@optional_auth  # Allow both authenticated and unauthenticated access
def api_get_random_exercises():
    try:
        data = request.json
        # Accept either `bodyPart` (frontend legacy) or `body_part` (canonical)
        selected_body_part = None
        selected_equipment = None
        if data is not None:
            selected_body_part = data.get("body_part") or data.get("bodyPart")
            selected_equipment = data.get("equipment")  # Optional equipment filter

        # Normalize and validate number of exercises
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

    # Use UserDataManager to get exercises (includes both user's and public exercises)
    try:
        user_data_manager = UserDataManager()
        user_id = get_current_user_id()

        # Get all exercises available to the user
        all_exercises = user_data_manager.get_exercises(user_id)

        # Filter by body part (case-insensitive) and optional equipment
        matching_exercises = []
        for exercise in all_exercises:
            body_part = exercise.get("body_part") or exercise.get("bodyPart", "")
            equipment = exercise.get("equipment", "")

            # Check if body part matches
            body_part_matches = body_part.lower() == selected_body_part.lower()

            # Check if equipment matches (if specified)
            equipment_matches = True  # Default to True if no equipment filter
            if selected_equipment:
                equipment_matches = equipment.lower() == selected_equipment.lower()

            # Include exercise if both conditions are met
            if body_part_matches and equipment_matches:
                matching_exercises.append(exercise)

        if not matching_exercises:
            error_msg = f"No exercises found for body part: {selected_body_part}"
            if selected_equipment:
                error_msg += f" with equipment: {selected_equipment}"
            return jsonify({"error": error_msg + "."}), 404

        # Sample random exercises
        import random

        if len(matching_exercises) <= num_exercises:
            random_exercises = matching_exercises
        else:
            random_exercises = random.sample(matching_exercises, num_exercises)

        # Transform canonical DB fields into the legacy frontend shape
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
# @app.route("/api/v1/refresh_db", methods=["POST"])
@app.route("/v1/refresh_db", methods=["POST"])
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
# @app.route("/api/v1/exercise/<string:name>", methods=["GET"])
@app.route("/v1/exercise/<string:name>", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@optional_auth
def api_get_exercise_details(name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        # Get current user ID from JWT token (if authenticated)
        current_user_id = None
        try:
            current_user_id = get_jwt_identity()
        except Exception:
            pass  # User not authenticated, that's okay

        # Use UserDataManager to get exercise (respects user data isolation)
        user_data_manager = UserDataManager()

        # Get all exercises accessible to this user
        all_exercises = user_data_manager.get_exercises(user_id=current_user_id)

        # Find the specific exercise by name (case-insensitive)
        try:
            norm_query = name.strip().lower()
        except Exception:
            norm_query = name

        exercise = None
        for ex in all_exercises:
            ex_name = (ex.get("exercise_name") or ex.get("name", "")).lower()
            if (
                ex_name == norm_query
                or ex.get("exercise_name") == name
                or ex.get("name") == name
            ):
                exercise = ex
                break

        if exercise:
            # Remove _id if present
            if "_id" in exercise:
                del exercise["_id"]
            return jsonify(exercise)

        return jsonify({"error": "Exercise not found."}), 404

    except Exception as e:
        print(f"Error in exercise details: {e}")
        return jsonify({"error": "Failed to retrieve exercise details."}), 500


# API endpoint to handle adding a new body part
# @app.route("/api/v1/add_body_part", methods=["POST"])
@app.route("/v1/add_body_part", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@require_auth  # Require authentication for adding body parts
def api_add_body_part(user):
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

        # Use UserDataManager to add body part with user isolation
        user_data_manager = UserDataManager()
        user_id = user["id"]

        # Check if this body part already exists for this user
        existing_body_parts = user_data_manager.get_body_parts(user_id)
        for bp in existing_body_parts:
            bp_name = bp.get("name", "").lower()
            # Check if user already owns this body part
            if bp_name == norm_name and bp.get("userId") == user_id:
                return (
                    jsonify(
                        {"error": "This body part already exists in your collection."}
                    ),
                    409,
                )

        # Add body part with userId
        result = user_data_manager.add_body_part({"name": norm_name}, user_id)
        return jsonify(
            {"message": "Body part added successfully", "id": str(result.inserted_id)}
        )
    except DuplicateKeyError:
        return jsonify({"error": "This body part already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Failed to add body part: {str(e)}"}), 500


# API endpoint to handle adding new equipment
# @app.route("/api/v1/add_equipment", methods=["POST"])
@app.route("/v1/add_equipment", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@require_auth  # Require authentication for adding equipment
def api_add_equipment(user):
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

        # Use UserDataManager to add equipment with user isolation
        user_data_manager = UserDataManager()
        user_id = user["id"]

        # Check if this equipment already exists for this user
        existing_equipment = user_data_manager.get_equipment(user_id)
        for eq in existing_equipment:
            eq_name = eq.get("name", "").lower()
            # Check if user already owns this equipment
            if eq_name == norm_name and eq.get("userId") == user_id:
                return (
                    jsonify(
                        {"error": "This equipment already exists in your collection."}
                    ),
                    409,
                )

        # Add equipment with userId
        result = user_data_manager.add_equipment({"name": norm_name}, user_id)
        return jsonify(
            {"message": "Equipment added successfully", "id": str(result.inserted_id)}
        )
    except DuplicateKeyError:
        return jsonify({"error": "This equipment already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Failed to add equipment: {str(e)}"}), 500


# API endpoint to delete an exercise by its name
# @app.route("/api/v1/delete_exercise/<path:name>", methods=["DELETE"])
@app.route("/v1/delete_exercise/<path:name>", methods=["DELETE"])
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
# @app.route("/api/v1/delete_body_part/<string:name>", methods=["DELETE"])
@app.route("/v1/delete_body_part/<string:name>", methods=["DELETE"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@require_auth  # Require authentication for deletion
def api_delete_body_part(user, name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        user_id = user["id"]
        user_data_manager = UserDataManager()

        # Normalize name to match how it's stored (lowercase)
        norm_name = name.strip().lower()

        # Delete body part (only user's own)
        result = user_data_manager.delete_body_part(norm_name, user_id)

        if not result["success"]:
            return jsonify({"error": result.get("error", "Body part not found.")}), 404

        # Cascade delete: Remove user's exercises that use this body part
        # Only delete exercises owned by this user
        exercises_deleted = db.exercises.delete_many(
            {
                "userId": user_id,
                "$or": [
                    {"body_part": {"$regex": f"^{norm_name}$", "$options": "i"}},
                    {"bodyPart": {"$regex": f"^{norm_name}$", "$options": "i"}},
                ],
            }
        )

        return jsonify(
            {
                "message": f"Body part '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to delete body part: {str(e)}"}), 500


# API endpoint to delete equipment by its name
# @app.route("/api/v1/delete_equipment/<string:name>", methods=["DELETE"])
@app.route("/v1/delete_equipment/<string:name>", methods=["DELETE"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@require_auth  # Require authentication for deletion
def api_delete_equipment(user, name):
    db = db_connect.get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        user_id = user["id"]
        user_data_manager = UserDataManager()

        # Normalize name to match how it's stored (lowercase)
        norm_name = name.strip().lower()

        # Delete equipment (only user's own)
        result = user_data_manager.delete_equipment(norm_name, user_id)

        if not result["success"]:
            return jsonify({"error": result.get("error", "Equipment not found.")}), 404

        # Cascade delete: Remove user's exercises that use this equipment
        # Only delete exercises owned by this user
        exercises_deleted = db.exercises.delete_many(
            {
                "userId": user_id,
                "equipment": {"$regex": f"^{norm_name}$", "$options": "i"},
            }
        )

        return jsonify(
            {
                "message": f"Equipment '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to delete equipment: {str(e)}"}), 500


# API endpoint to get a list of all body parts
# @app.route("/api/v1/body_parts_list", methods=["GET"])
@app.route("/v1/body_parts_list", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@optional_auth  # Allow both authenticated and unauthenticated access
def api_body_parts_list():
    try:
        # Use UserDataManager to get body parts (includes both user's and public body parts)
        user_data_manager = UserDataManager()
        user_id = get_current_user_id()

        body_parts_docs = user_data_manager.get_body_parts(user_id)

        # Extract unique body part names (case-insensitive)
        body_parts_set = set()
        for doc in body_parts_docs:
            name = doc.get("name") or doc.get("body_part")
            if name and isinstance(name, str):
                body_parts_set.add(name.lower())

        # Return sorted list
        body_parts = sorted(list(body_parts_set))
        return jsonify(body_parts)

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve body parts list: {str(e)}"}), 500


# API endpoint to get a list of all equipment
# @app.route("/api/v1/equipment_list", methods=["GET"])
@app.route("/v1/equipment_list", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@optional_auth  # Allow both authenticated and unauthenticated access
def api_equipment_list():
    try:
        # Use UserDataManager to get equipment (includes both user's and public equipment)
        user_data_manager = UserDataManager()
        user_id = get_current_user_id()

        equipment_docs = user_data_manager.get_equipment(user_id)

        # Extract unique equipment names (case-insensitive)
        equipment_set = set()
        for doc in equipment_docs:
            name = doc.get("name") or doc.get("equipment")
            if name and isinstance(name, str):
                equipment_set.add(name.lower())

        # Return sorted list
        equipment_list = sorted(list(equipment_set))
        return jsonify(equipment_list)

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve equipment list: {str(e)}"}), 500


# API endpoint to get a list of all exercises
# @app.route("/api/v1/exercises_list", methods=["GET"])
@app.route("/v1/exercises_list", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@optional_auth  # Allow both authenticated and unauthenticated access
def api_exercises_list():
    print("[DEBUG] Entered api_exercises_list")
    try:
        # Use UserDataManager to get exercises (includes both user's and public exercises)
        user_data_manager = UserDataManager()
        user_id = get_current_user_id()

        exercises = user_data_manager.get_exercises(user_id)
        print("[DEBUG] Raw exercises from DB:", exercises)

        # Remove MongoDB _id field for clean JSON response and ensure all fields are serializable
        from bson import ObjectId

        def clean_obj(obj):
            if isinstance(obj, dict):
                return {
                    k: clean_obj(v)
                    for k, v in obj.items()
                    if not isinstance(v, ObjectId)
                }
            elif isinstance(obj, list):
                return [clean_obj(v) for v in obj]
            elif isinstance(obj, ObjectId):
                return str(obj)
            else:
                return obj

        cleaned_exercises = [clean_obj(ex) for ex in exercises]
        print("[DEBUG] Cleaned exercises for response:", cleaned_exercises)
        import json

        try:
            print(
                "[DEBUG] Final JSON response:", json.dumps(cleaned_exercises, indent=2)
            )
        except Exception as log_err:
            print(
                f"[DEBUG] Could not serialize cleaned_exercises for logging: {log_err}"
            )
        return jsonify(cleaned_exercises)

    except Exception as e:
        print(f"[ERROR] Exception in api_exercises_list: {e}")

        return jsonify({"error": f"Failed to retrieve exercises list: {str(e)}"}), 500


# API endpoint to get a list of all difficulties
# @app.route("/api/v1/difficulties", methods=["GET"])
@app.route("/v1/difficulties", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
@optional_auth  # Allow both authenticated and unauthenticated access
def api_difficulties():
    try:
        # Use UserDataManager to get exercises (includes both user's and public exercises)
        user_data_manager = UserDataManager()
        user_id = get_current_user_id()

        exercises = user_data_manager.get_exercises(user_id)

        # Extract unique difficulty levels (case-insensitive)
        difficulties_set = set()
        for exercise in exercises:
            difficulty = exercise.get("difficulty")
            if difficulty and isinstance(difficulty, str):
                difficulties_set.add(difficulty.lower())

        # Return sorted list
        difficulties = sorted(list(difficulties_set))
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
# @app.route("/api/v1/health", methods=["GET"])
@app.route("/v1/health", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)  # <--- CORS FIX
def api_health_check():
    return jsonify({"status": "ok", "message": "API is running and healthy."}), 200


# Management endpoint: preview configured allowed origins
# Protect with ADMIN_PREVIEW_TOKEN environment variable (use a strong token)
# @app.route("/api/v1/admin/allowed_origins", methods=["GET"])
@app.route("/v1/admin/allowed_origins", methods=["GET"])
def api_admin_allowed_origins():
    token = os.getenv("ADMIN_PREVIEW_TOKEN")
    auth = request.headers.get("Authorization")
    if not token or not auth or auth.strip() != f"Bearer {token}":
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"allowed_origins": ALLOWED_ORIGINS}), 200


# --- Authentication Routes ---


# @app.route("/api/v1/auth/register", methods=["POST"])
@app.route("/v1/auth/register", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)
def api_register():
    """Register a new user account."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        result = register_user(data)

        if result["success"]:
            return (
                jsonify(
                    {
                        "success": True,
                        "user": result["user"],
                        "access_token": result["access_token"],
                        "message": result["message"],
                    }
                ),
                201,
            )
        else:
            return jsonify({"success": False, "errors": result["errors"]}), 400

    except Exception as e:
        app.logger.error(f"Registration endpoint error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500


# @app.route("/api/v1/auth/login", methods=["POST"])
@app.route("/v1/auth/login", methods=["POST"])
@cross_origin(origins=ALLOWED_ORIGINS)
def api_login():
    """Authenticate user login."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        result = login_user(data)

        if result["success"]:
            return (
                jsonify(
                    {
                        "success": True,
                        "user": result["user"],
                        "access_token": result["access_token"],
                        "message": result["message"],
                    }
                ),
                200,
            )
        else:
            return jsonify({"success": False, "errors": result["errors"]}), 401

    except Exception as e:
        app.logger.error(f"Login endpoint error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500


# @app.route("/api/v1/auth/verify", methods=["GET"])
@app.route("/v1/auth/verify", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)
@jwt_required()
def api_verify_token():
    """Verify JWT token and return user data."""
    try:
        result = verify_token()

        if result["success"]:
            return (
                jsonify(
                    {
                        "success": True,
                        "user": result["user"],
                        "message": result["message"],
                    }
                ),
                200,
            )
        else:
            return jsonify({"success": False, "error": result["error"]}), 401

    except Exception as e:
        app.logger.error(f"Token verification endpoint error: {str(e)}")
        return jsonify({"error": "Token verification failed"}), 500


# @app.route("/api/v1/auth/me", methods=["GET"])
@app.route("/v1/auth/me", methods=["GET"])
@cross_origin(origins=ALLOWED_ORIGINS)
@require_auth
def api_get_current_user(current_user):
    """Get current user profile."""
    return jsonify({"success": True, "user": current_user}), 200


# --- Run Server (Production/Development) ---
if __name__ == "__main__":
    # Initial connection attempt when running locally
    db_connect.connect_db()
    app.run(debug=True, port=5000)
