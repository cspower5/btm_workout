import json
import random
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin # <-- Keep CORS and Import cross_origin
from btm_workout_db_connect import get_db, connect_db
from database_refresh import insert_exercises_if_not_exist
from pymongo.errors import DuplicateKeyError, BulkWriteError
import os

# --- Initialization ---
app = Flask(__name__)
# NOTE: The global CORS(app) is REMOVED. @cross_origin is used on each route for guaranteed functionality.

# --- API Routes (v1) ---

@app.route('/api/v1/insert_exercise', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_insert_exercise():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500

    try:
        data = request.json
        exercises_collection = db['exercises']

        if not all(k in data for k in ('name', 'bodyPart', 'equipment', 'target')):
            return jsonify({"error": "Missing required fields."}), 400
            
        data.pop('category', None) # Clean up potential extra fields

        result = exercises_collection.insert_one(data)

        return jsonify({"message": "Exercise inserted successfully", "id": str(result.inserted_id)})
    
    except DuplicateKeyError:
        return jsonify({"error": "An exercise with this name, body part, and equipment already exists."}), 409
    
    except Exception as e:
        print(f"Error inserting exercise: {e}")
        return jsonify({"error": "Failed to insert exercise."}), 500

# API endpoint to get 3 random exercises for a selected body part
@app.route('/api/v1/get_random_exercises', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_get_random_exercises():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500

    try:
        data = request.json
        selected_body_part = data.get('bodyPart')
        num_exercises = data.get('numExercises', 4)
    except Exception:
        return jsonify({"error": "Invalid request format."}), 400

    if not selected_body_part:
        return jsonify({"error": "No body part provided."}), 400
        
    match_stage = {"$match": {"bodyPart": selected_body_part}}
        
    try:
        pipeline = [
            match_stage,
            {"$sample": {"size": int(num_exercises)}},
            {"$project": {"_id": 0}} # Exclude MongoDB's _id field
        ]

        random_exercises = list(db.exercises.aggregate(pipeline))

        if not random_exercises:
             return jsonify({"error": f"No exercises found for body part: {selected_body_part}."}), 404
             
        return jsonify(random_exercises)
    except Exception as e:
        print(f"Error getting random exercises: {e}")
        return jsonify({"error": "Failed to retrieve exercises."}), 500

# API endpoint to refresh the database with new exercises
@app.route('/api/v1/refresh_db', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_refresh_db():
    try:
        # Calls the external API logic from database_refresh.py
        count = insert_exercises_if_not_exist() 
        return jsonify({"message": f"Database refresh complete. {count} new exercises added."})
    except Exception as e:
        return jsonify({"error": f"Failed to refresh database: {e}"}), 500

# API endpoint to get a single exercise by its name
@app.route('/api/v1/exercise/<string:name>', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_get_exercise_details(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        exercises_collection = db['exercises']
        exercise = exercises_collection.find_one({"name": name}, {'_id': 0})
        
        if exercise:
            return jsonify(exercise)
        else:
            return jsonify({"error": "Exercise not found."}), 404
            
    except Exception as e:
        return jsonify({"error": "Failed to retrieve exercise details."}), 500

# API endpoint to handle adding a new body part
@app.route('/api/v1/add_body_part', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_add_body_part():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({"error": "Missing 'name' field."}), 400
        result = db.body_parts.insert_one({"name": name})
        return jsonify({"message": "Body part added successfully", "id": str(result.inserted_id)})
    except DuplicateKeyError:
        return jsonify({"error": "This body part already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Failed to add body part: {str(e)}"}), 500

# API endpoint to handle adding new equipment
@app.route('/api/v1/add_equipment', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_add_equipment():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({"error": "Missing 'name' field."}), 400
        result = db.equipment.insert_one({"name": name})
        return jsonify({"message": "Equipment added successfully", "id": str(result.inserted_id)})
    except DuplicateKeyError:
        return jsonify({"error": "This equipment already exists."}), 409
    except Exception as e:
        return jsonify({"error": f"Failed to add equipment: {str(e)}"}), 500

# API endpoint to delete an exercise by its name
@app.route('/api/v1/delete_exercise/<path:name>', methods=['DELETE'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_delete_exercise(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.exercises.delete_one({"name": name})
        if result.deleted_count == 1:
            return jsonify({"message": f"Exercise '{name}' deleted successfully."})
        else:
            return jsonify({"error": "Exercise not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete exercise: {str(e)}"}), 500

# API endpoint to delete a body part by its name
@app.route('/api/v1/delete_body_part/<string:name>', methods=['DELETE'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_delete_body_part(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.body_parts.delete_one({"name": name})
        
        # Also delete associated exercises
        exercises_deleted = db.exercises.delete_many({"bodyPart": name})

        if result.deleted_count == 1:
            return jsonify({
                "message": f"Body part '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
            })
        else:
            return jsonify({"error": "Body part not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete body part: {str(e)}"}), 500

# API endpoint to delete equipment by its name
@app.route('/api/v1/delete_equipment/<string:name>', methods=['DELETE'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_delete_equipment(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.equipment.delete_one({"name": name})

        # Also delete associated exercises
        exercises_deleted = db.exercises.delete_many({"equipment": name})

        if result.deleted_count == 1:
            return jsonify({
                "message": f"Equipment '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
            })
        else:
            return jsonify({"error": "Equipment not found."}), 404
    except Exception as e:
        return jsonify({"error": "Failed to delete equipment: {str(e)}"}), 500

# API endpoint to get a list of all body parts
@app.route('/api/v1/body_parts_list', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_body_parts_list():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        # Use MongoDB's distinct to fetch unique body parts from the exercises collection
        body_parts = db.exercises.distinct('bodyPart')
        return jsonify(body_parts)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve body parts list: {str(e)}"}), 500

# API endpoint to get a list of all equipment
@app.route('/api/v1/equipment_list', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_equipment_list():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        equipment_list = db.exercises.distinct('equipment')
        return jsonify(equipment_list)
    except Exception as e:
        return jsonify({"error": "Failed to retrieve equipment list: {str(e)}"}), 500

# API endpoint to get a list of all exercises
@app.route('/api/v1/exercises_list', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_exercises_list():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        exercises_list = list(db.exercises.find({}, {"_id": 0}))
        return jsonify(exercises_list)
    except Exception as e:
        return jsonify({"error": "Failed to retrieve exercises list: {str(e)}"}), 500

# API endpoint to get a list of all difficulties
@app.route('/api/v1/difficulties', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_difficulties():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        difficulties = db.exercises.distinct('difficulty')
        return jsonify(difficulties)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve difficulties: {str(e)}"}), 500

# --- Error Handling ---

@app.errorhandler(404)
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'The requested URL was not found on the server.'}), 404

@app.errorhandler(500)
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def internal_error(error):
    app.logger.error('Server Error: %s', error)
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred on the server.'}), 500

# --- Health Check ---
@app.route('/api/v1/health', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS FIX
def api_health_check():
    return jsonify({"status": "ok", "message": "API is running and healthy."}), 200

# --- Run Server (Production/Development) ---
if __name__ == '__main__':
    # Initial connection attempt when running locally
    connect_db() 
    app.run(debug=True, port=5000)



