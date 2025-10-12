"""
Authentication module for BTM Workout app.
Provides user registration, login, logout, and JWT token management.
"""

from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from flask import jsonify
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from btm_workout_db_connect import get_db


def init_auth(app):
    """Initialize authentication for the Flask app."""

    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = app.config.get(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    app.config["JWT_ALGORITHM"] = "HS256"

    jwt = JWTManager(app)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Token is required"}), 401

    return jwt


def hash_password(password):
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt)


def check_password(password, hashed):
    """Check if a password matches the hashed version."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


def validate_user_data(data, is_registration=False):
    """Validate user registration/login data."""
    errors = {}

    # Email validation
    email = data.get("email", "").strip()
    if not email:
        errors["email"] = "Email is required"
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors["email"] = "Please enter a valid email address"

    # Password validation
    password = data.get("password", "")
    if not password:
        errors["password"] = "Password is required"
    elif is_registration and len(password) < 6:
        errors["password"] = "Password must be at least 6 characters long"

    # Registration-specific validation
    if is_registration:
        username = data.get("username", "").strip()
        if not username:
            errors["username"] = "Username is required"
        elif len(username) < 3:
            errors["username"] = "Username must be at least 3 characters long"
        elif not username.replace("_", "").isalnum():
            errors["username"] = (
                "Username can only contain letters, numbers, and underscores"
            )

    return errors


def register_user(data):
    """Register a new user."""
    try:
        db = get_db()
        users_collection = db.users

        # Validate input data
        errors = validate_user_data(data, is_registration=True)
        if errors:
            return {"success": False, "errors": errors}

        email = data["email"].strip().lower()
        username = data["username"].strip()
        password = data["password"]

        # Check if user already exists
        existing_user = users_collection.find_one(
            {"$or": [{"email": email}, {"username": username}]}
        )

        if existing_user:
            if existing_user["email"] == email:
                return {
                    "success": False,
                    "errors": {"email": "Email already registered"},
                }
            else:
                return {
                    "success": False,
                    "errors": {"username": "Username already taken"},
                }

        # Hash password
        hashed_password = hash_password(password)

        # Create user document
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow(),
            "preferences": {},
            "is_active": True,
        }

        # Insert user into database
        result = users_collection.insert_one(user_doc)
        user_id = str(result.inserted_id)

        # Create JWT token
        access_token = create_access_token(identity=user_id)

        # Return user data (without password hash)
        user_data = {
            "id": user_id,
            "username": username,
            "email": email,
            "preferences": {},
            "created_at": user_doc["created_at"].isoformat(),
        }

        return {
            "success": True,
            "user": user_data,
            "access_token": access_token,
            "message": "Account created successfully",
        }

    except Exception as e:
        print(f"Registration error: {str(e)}")
        return {
            "success": False,
            "errors": {"general": "Registration failed. Please try again."},
        }


def login_user(data):
    """Authenticate user login."""
    try:
        db = get_db()
        users_collection = db.users

        # Validate input data
        errors = validate_user_data(data, is_registration=False)
        if errors:
            return {"success": False, "errors": errors}

        email = data["email"].strip().lower()
        password = data["password"]

        # Find user by email
        user = users_collection.find_one({"email": email})

        if not user:
            return {
                "success": False,
                "errors": {"email": "No account found with this email"},
            }

        # Check if account is active
        if not user.get("is_active", True):
            return {
                "success": False,
                "errors": {"general": "Account has been deactivated"},
            }

        # Verify password
        if not check_password(password, user["password_hash"]):
            return {"success": False, "errors": {"password": "Incorrect password"}}

        # Create JWT token
        user_id = str(user["_id"])
        access_token = create_access_token(identity=user_id)

        # Update last login
        users_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}}
        )

        # Return user data (without password hash)
        user_data = {
            "id": user_id,
            "username": user["username"],
            "email": user["email"],
            "preferences": user.get("preferences", {}),
            "created_at": user["created_at"].isoformat(),
        }

        return {
            "success": True,
            "user": user_data,
            "access_token": access_token,
            "message": "Login successful",
        }

    except Exception as e:
        print(f"Login error: {str(e)}")
        return {
            "success": False,
            "errors": {"general": "Login failed. Please try again."},
        }


def get_current_user():
    """Get current user from JWT token."""
    try:
        db = get_db()
        users_collection = db.users

        # Get user ID from JWT token
        user_id = get_jwt_identity()

        if not user_id:
            return None

        # Find user in database
        from bson import ObjectId

        user = users_collection.find_one({"_id": ObjectId(user_id)})

        if not user or not user.get("is_active", True):
            return None

        # Return user data (without password hash)
        return {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "preferences": user.get("preferences", {}),
            "created_at": user["created_at"].isoformat(),
        }

    except Exception as e:
        print(f"Get current user error: {str(e)}")
        return None


def require_auth(f):
    """Decorator to require authentication for routes."""

    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        return f(user, *args, **kwargs)

    return decorated_function


def verify_token():
    """Verify JWT token and return user data."""
    try:
        user = get_current_user()
        if not user:
            return {"success": False, "error": "Invalid or expired token"}

        return {"success": True, "user": user, "message": "Token is valid"}

    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return {"success": False, "error": "Token verification failed"}
