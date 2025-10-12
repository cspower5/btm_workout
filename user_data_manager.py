"""
User data isolation utilities for BTM Workout app.
Provides backward-compatible access to both legacy data and user-specific data.
"""

from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from btm_workout_db_connect import get_db


def get_current_user_id():
    """Get the current user's ID from JWT token, or None if not authenticated"""
    try:
        return get_jwt_identity()
    except Exception:
        return None


def get_user_query_filter(user_id=None, include_public=True):
    """
    Generate MongoDB query filter for user data isolation.

    Args:
        user_id: User ID to filter by (None for current user)
        include_public: Whether to include public/legacy data (userId=null)

    Returns:
        dict: MongoDB query filter
    """
    if user_id is None:
        user_id = get_current_user_id()

    if user_id and include_public:
        # Include both user's data and public/legacy data
        return {"$or": [{"userId": user_id}, {"userId": None}]}
    elif user_id:
        # Only user's data
        return {"userId": user_id}
    else:
        # Only public/legacy data (for unauthenticated access)
        return {"userId": None}


def add_user_id_to_document(doc, user_id=None):
    """
    Add userId to a document before saving.

    Args:
        doc: Document to modify
        user_id: User ID to add (None for current user)

    Returns:
        dict: Modified document
    """
    if user_id is None:
        user_id = get_current_user_id()

    doc["userId"] = user_id
    return doc


def optional_auth(f):
    """
    Decorator that makes JWT authentication optional.
    Sets user context if token is present, but doesn't require it.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Try to get user from JWT token
            return jwt_required(optional=True)(f)(*args, **kwargs)
        except Exception:
            # If JWT fails, continue without authentication
            return f(*args, **kwargs)

    return decorated_function


class UserDataManager:
    """
    Manages user data isolation across collections.
    Provides backward-compatible access to legacy and user-specific data.
    """

    def __init__(self):
        self.db = get_db()

    def get_exercises(self, user_id=None, filters=None):
        """Get exercises for user, including public/legacy exercises"""
        collection = self.db.exercises

        # Start with user filter
        query = get_user_query_filter(user_id, include_public=True)

        # Add additional filters
        if filters:
            query.update(filters)

        return list(collection.find(query, {"_id": 0}))

    def get_body_parts(self, user_id=None):
        """Get body parts for user, including public/legacy body parts"""
        collection = self.db.body_parts
        query = get_user_query_filter(user_id, include_public=True)
        return list(collection.find(query, {"_id": 0}))

    def get_equipment(self, user_id=None):
        """Get equipment for user, including public/legacy equipment"""
        collection = self.db.equipment
        query = get_user_query_filter(user_id, include_public=True)
        return list(collection.find(query, {"_id": 0}))

    def add_exercise(self, exercise_data, user_id=None):
        """Add exercise with user isolation"""
        exercise_data = add_user_id_to_document(exercise_data, user_id)
        return self.db.exercises.insert_one(exercise_data)

    def add_body_part(self, body_part_data, user_id=None):
        """Add body part with user isolation"""
        body_part_data = add_user_id_to_document(body_part_data, user_id)
        return self.db.body_parts.insert_one(body_part_data)

    def add_equipment(self, equipment_data, user_id=None):
        """Add equipment with user isolation"""
        equipment_data = add_user_id_to_document(equipment_data, user_id)
        return self.db.equipment.insert_one(equipment_data)

    def delete_exercise(self, exercise_name, user_id=None):
        """Delete exercise (only user's own exercises)"""
        if user_id is None:
            user_id = get_current_user_id()

        if not user_id:
            return {"success": False, "error": "Authentication required for deletion"}

        # Only allow deletion of user's own exercises
        query = {"exercise_name": exercise_name, "userId": user_id}
        result = self.db.exercises.delete_one(query)

        return {
            "success": result.deleted_count > 0,
            "deleted_count": result.deleted_count,
        }

    def delete_body_part(self, body_part_name, user_id=None):
        """Delete body part (only user's own body parts)"""
        if user_id is None:
            user_id = get_current_user_id()

        if not user_id:
            return {"success": False, "error": "Authentication required for deletion"}

        query = {"body_part": body_part_name, "userId": user_id}
        result = self.db.body_parts.delete_one(query)

        return {
            "success": result.deleted_count > 0,
            "deleted_count": result.deleted_count,
        }

    def delete_equipment(self, equipment_name, user_id=None):
        """Delete equipment (only user's own equipment)"""
        if user_id is None:
            user_id = get_current_user_id()

        if not user_id:
            return {"success": False, "error": "Authentication required for deletion"}

        query = {"equipment": equipment_name, "userId": user_id}
        result = self.db.equipment.delete_one(query)

        return {
            "success": result.deleted_count > 0,
            "deleted_count": result.deleted_count,
        }
