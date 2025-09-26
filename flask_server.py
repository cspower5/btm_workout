from flask import Flask, jsonify, request
from flask_cors import CORS
import os
# Removed unused imports: render_template, send_from_directory
from btm_workout_db_connect import connect_db, get_db
from database_refresh import insert_exercises_if_not_exist
from pymongo.errors import DuplicateKeyError

# Configure Flask as an API-ONLY server
app = Flask(__name__)

# Apply CORS to explicitly allow requests from your live GitHub Pages domain
# This fixes the 'Access-Control-Allow-Origin' missing error.
#CORS(app, origins=["https://cspower5.github.io"])
CORS(app, resources={r"/api/v1/*": {"origins": "*"}})

# ======================================================================
# API Endpoints (Routes use /api/v1/ prefix)
# ======================================================================

# API endpoint to handle inserting a new exercise
@app.route('/api/v1/insert_exercise', methods=['POST'])
def api_insert_exercise():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500

    try:
        data = request.json
        exercises_collection = db['exercises']

        # NOTE: Assumed 'gifUrl' requirement was removed from your logic
        if not all(k in data for k in ('name', 'bodyPart', 'equipment', 'target')):
            return jsonify({"error": "Missing required fields."}), 400
        
        data.pop('category', None)

        result = exercises_collection.insert_one(data)

        return jsonify({"message": "Exercise inserted successfully", "id": str(result.inserted_id)})
    
    except DuplicateKeyError as e:
        print(f"Duplicate exercise not inserted: {e}")
        return jsonify({"error": "An exercise with this name, body part, and equipment already exists."}), 409
    
    except Exception as e:
        print(f"Error inserting exercise: {e}")
        return jsonify({"error": "Failed to insert exercise."}), 500

# API endpoint to get 3 random exercises for a selected body part
@app.route('/api/v1/get_random_exercises', methods=['POST'])
def api_get_random_exercises():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500

    try:
        data = request.json
        selected_body_part = data.get('bodyPart')
        num_exercises = data.get('numExercises', 3)

        if not selected_body_part:
            return jsonify({"error": "No body part provided."}), 400

        exercises_collection = db['exercises']
        
        pipeline = [
            {"$match": {"bodyPart": selected_body_part}},
            {"$sample": {"size": int(num_exercises)}}
        ]

        random_exercises = list(exercises_collection.aggregate(pipeline))

        for exercise in random_exercises:
            exercise.pop('_id', None)

        return jsonify(random_exercises)
    except Exception as e:
        print(f"Error getting random exercises: {e}")
        return jsonify({"error": "Failed to retrieve exercises."}), 500

# API endpoint to refresh the database with new exercises
@app.route('/api/v1/refresh_db', methods=['POST'])
def api_refresh_db():
    try:
        count = insert_exercises_if_not_exist()
        return jsonify({"message": f"Database refresh complete. {count} new exercises added."})
    except Exception as e:
        print(f"Error refreshing database: {e}")
        return jsonify({"error": "Failed to refresh database."}), 500

# API endpoint to get a single exercise by its name
@app.route('/api/v1/exercise/<string:name>')
def api_get_exercise_details(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        exercises_collection = db['exercises']
        exercise = exercises_collection.find_one({"name": name})
        
        if exercise:
            exercise.pop('_id', None)
            return jsonify(exercise)
        else:
            return jsonify({"error": "Exercise not found."}), 404
            
    except Exception as e:
        print(f"Error fetching single exercise: {e}")
        return jsonify({"error": "Failed to retrieve exercise details."}), 500

# API endpoint to handle adding a new body part
@app.route('/api/v1/add_body_part', methods=['POST'])
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
def api_delete_body_part(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.body_parts.delete_one({"name": name})
        
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
def api_delete_equipment(name):
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        result = db.equipment.delete_one({"name": name})

        exercises_deleted = db.exercises.delete_many({"equipment": name})

        if result.deleted_count == 1:
            return jsonify({
                "message": f"Equipment '{name}' and {exercises_deleted.deleted_count} associated exercises deleted successfully."
            })
        else:
            return jsonify({"error": "Equipment not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete equipment: {str(e)}"}), 500

# API endpoint to get a list of all body parts
@app.route('/api/v1/body_parts_list')
def api_body_parts_list():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        body_parts = list(db.body_parts.find({}, {"_id": 0}))
        return jsonify(body_parts)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve body parts list: {str(e)}"}), 500

# API endpoint to get a list of all equipment
@app.route('/api/v1/equipment_list')
def api_equipment_list():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        equipment_list = list(db.equipment.find({}, {"_id": 0}))
        return jsonify(equipment_list)
    except Exception as e:
        return jsonify({"error": "Failed to retrieve equipment list: {str(e)}"}), 500

# API endpoint to get a list of all exercises
@app.route('/api/v1/exercises_list')
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
@app.route('/api/v1/difficulties')
def api_difficulties():
    db = get_db()
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    try:
        difficulties = db.exercises.distinct('difficulty')
        return jsonify(difficulties)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve difficulties: {str(e)}"}), 500

# ======================================================================
# Catch-All Route (This MUST be the last route in the file)
# ======================================================================
# The entire Catch-All route is removed to prevent static file conflicts.

if __name__ == '__main__':
    connect_db()
    app.run(debug=True, use_reloader=False)

