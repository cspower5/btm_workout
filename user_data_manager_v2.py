"""
User-customizable data manager for BTM Workout app.
Allows users to hide/show exercises, body parts, and equipment from their view.
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
    Manages user-customizable data visibility.

    Core concept:
    - All exercises/body_parts/equipment start as "visible" for everyone
    - Users can hide specific items from their view
    - Users can add their own custom items
    - Hidden items are stored per-user, not deleted globally
    """

    def __init__(self):
        self.db = get_db()

    def _get_user_hidden_items(self, user_id, collection_name):
        """Get list of item IDs that user has hidden"""
        if not user_id:
            return set()

        hidden_collection = self.db.user_hidden_items
        user_hidden = hidden_collection.find_one(
            {"userId": user_id, "collection": collection_name}
        )

        return set(user_hidden.get("hidden_items", [])) if user_hidden else set()

    def _hide_item_for_user(self, user_id, collection_name, item_identifier):
        """Hide a specific item for a user"""
        if not user_id:
            return False

        hidden_collection = self.db.user_hidden_items

        # Use upsert to create or update the hidden items list
        hidden_collection.update_one(
            {"userId": user_id, "collection": collection_name},
            {
                "$addToSet": {"hidden_items": item_identifier},
                "$set": {"userId": user_id, "collection": collection_name},
            },
            upsert=True,
        )
        return True

    def _unhide_item_for_user(self, user_id, collection_name, item_identifier):
        """Unhide a specific item for a user"""
        if not user_id:
            return False

        hidden_collection = self.db.user_hidden_items
        hidden_collection.update_one(
            {"userId": user_id, "collection": collection_name},
            {"$pull": {"hidden_items": item_identifier}},
        )
        return True

    def get_exercises(self, user_id=None, filters=None):
        """Get exercises visible to user (all exercises minus hidden ones)"""
        collection = self.db.exercises

        # Start with all exercises (both public and user's custom ones)
        if user_id:
            query = {
                "$or": [
                    {"userId": None},  # Public exercises
                    {"userId": user_id},  # User's custom exercises
                ]
            }
        else:
            query = {"userId": None}  # Only public exercises for anonymous users

        # Add additional filters
        if filters:
            query.update(filters)

        all_exercises = list(collection.find(query, {"_id": 0}))

        # Filter out hidden exercises
        if user_id:
            hidden_exercises = self._get_user_hidden_items(user_id, "exercises")
            # Hide exercises by name+body_part+equipment combination
            visible_exercises = []
            for exercise in all_exercises:
                identifier = f"{exercise.get('exercise_name', '')}|{exercise.get('body_part', '')}|{exercise.get('equipment', '')}"
                if identifier not in hidden_exercises:
                    visible_exercises.append(exercise)
            return visible_exercises

        return all_exercises

    def get_body_parts(self, user_id=None):
        """Get body parts visible to user"""
        collection = self.db.body_parts

        if user_id:
            query = {"$or": [{"userId": None}, {"userId": user_id}]}
        else:
            query = {"userId": None}

        all_body_parts = list(collection.find(query, {"_id": 0}))

        # Filter out hidden body parts
        if user_id:
            hidden_body_parts = self._get_user_hidden_items(user_id, "body_parts")
            visible_body_parts = []
            for body_part in all_body_parts:
                identifier = body_part.get("name") or body_part.get("body_part", "")
                if identifier not in hidden_body_parts:
                    visible_body_parts.append(body_part)
            return visible_body_parts

        return all_body_parts

    def get_equipment(self, user_id=None):
        """Get equipment visible to user"""
        collection = self.db.equipment

        if user_id:
            query = {"$or": [{"userId": None}, {"userId": user_id}]}
        else:
            query = {"userId": None}

        all_equipment = list(collection.find(query, {"_id": 0}))

        # Filter out hidden equipment
        if user_id:
            hidden_equipment = self._get_user_hidden_items(user_id, "equipment")
            visible_equipment = []
            for equipment in all_equipment:
                identifier = equipment.get("name") or equipment.get("equipment", "")
                if identifier not in hidden_equipment:
                    visible_equipment.append(equipment)
            return visible_equipment

        return all_equipment

    def add_exercise(self, exercise_data, user_id=None):
        """Add custom exercise for user"""
        if user_id:
            exercise_data["userId"] = user_id
        else:
            exercise_data["userId"] = None

        return self.db.exercises.insert_one(exercise_data)

    def add_body_part(self, body_part_data, user_id=None):
        """Add custom body part for user"""
        if user_id:
            body_part_data["userId"] = user_id
        else:
            body_part_data["userId"] = None

        return self.db.body_parts.insert_one(body_part_data)

    def add_equipment(self, equipment_data, user_id=None):
        """Add custom equipment for user"""
        if user_id:
            equipment_data["userId"] = user_id
        else:
            equipment_data["userId"] = None

        return self.db.equipment.insert_one(equipment_data)

    def hide_exercise(self, exercise_name, body_part, equipment, user_id=None):
        """Hide an exercise from user's view"""
        if not user_id:
            return {"success": False, "error": "Authentication required"}

        identifier = f"{exercise_name}|{body_part}|{equipment}"
        success = self._hide_item_for_user(user_id, "exercises", identifier)

        return {
            "success": success,
            "message": f"Exercise '{exercise_name}' hidden from your view",
        }

    def hide_body_part(self, body_part_name, user_id=None):
        """Hide a body part from user's view"""
        if not user_id:
            return {"success": False, "error": "Authentication required"}

        success = self._hide_item_for_user(user_id, "body_parts", body_part_name)

        return {
            "success": success,
            "message": f"Body part '{body_part_name}' hidden from your view",
        }

    def hide_equipment(self, equipment_name, user_id=None):
        """Hide equipment from user's view"""
        if not user_id:
            return {"success": False, "error": "Authentication required"}

        success = self._hide_item_for_user(user_id, "equipment", equipment_name)

        return {
            "success": success,
            "message": f"Equipment '{equipment_name}' hidden from your view",
        }

    def unhide_exercise(self, exercise_name, body_part, equipment, user_id=None):
        """Unhide an exercise for user"""
        if not user_id:
            return {"success": False, "error": "Authentication required"}

        identifier = f"{exercise_name}|{body_part}|{equipment}"
        success = self._unhide_item_for_user(user_id, "exercises", identifier)

        return {
            "success": success,
            "message": f"Exercise '{exercise_name}' restored to your view",
        }

    def delete_custom_exercise(self, exercise_name, user_id=None):
        """Delete user's own custom exercise (not hide, actually delete)"""
        if not user_id:
            return {"success": False, "error": "Authentication required"}

        # Only allow deletion of user's own custom exercises
        result = self.db.exercises.delete_one(
            {"exercise_name": exercise_name, "userId": user_id}
        )

        return {
            "success": result.deleted_count > 0,
            "deleted_count": result.deleted_count,
            "message": (
                f"Custom exercise '{exercise_name}' deleted"
                if result.deleted_count > 0
                else "Exercise not found or not owned by user"
            ),
        }

    def get_hidden_items(self, user_id, collection_name=None):
        """Get list of items user has hidden"""
        if not user_id:
            return {}

        hidden_collection = self.db.user_hidden_items

        if collection_name:
            hidden_doc = hidden_collection.find_one(
                {"userId": user_id, "collection": collection_name}
            )
            return hidden_doc.get("hidden_items", []) if hidden_doc else []
        else:
            # Return all hidden items for user
            all_hidden = {}
            for doc in hidden_collection.find({"userId": user_id}):
                all_hidden[doc["collection"]] = doc.get("hidden_items", [])
            return all_hidden
