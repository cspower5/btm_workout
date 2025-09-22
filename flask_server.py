from flask import Flask, render_template, jsonify, request
from list_body_parts import get_body_parts
from database_refresh import insert_exercises_if_not_exist
import json

app = Flask(__name__)

# Route for the main home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the page to insert a new exercise
@app.route('/insert_exercise')
def insert_exercise_page():
    return render_template('insert_exercise.html')

# Route for the page to select a body part and get exercises
@app.route('/select_body_part')
def select_body_part_page():
    return render_template('select_body_part.html')

# API endpoint to get the list of body parts
@app.route('/api/body_parts')
def api_body_parts():
    body_parts = get_body_parts()
    return jsonify(body_parts)

# API endpoint to handle inserting a new exercise
@app.route('/api/insert_exercise', methods=['POST'])
def api_insert_exercise():
    from btm_workout_db_connect import db
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    
    try:
        data = request.json
        exercises_collection = db['exercises']
        
        # Check if the required fields are in the JSON data
        if not all(k in data for k in ('name', 'bodyPart', 'equipment', 'gifUrl', 'target')):
            return jsonify({"error": "Missing required fields."}), 400

        # Insert the new exercise into the database
        result = exercises_collection.insert_one(data)
        
        return jsonify({"message": "Exercise inserted successfully", "id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error inserting exercise: {e}")
        return jsonify({"error": "Failed to insert exercise."}), 500

# API endpoint to get 3 random exercises for a selected body part
@app.route('/api/get_random_exercises', methods=['POST'])
def api_get_random_exercises():
    from btm_workout_db_connect import db
    if db is None:
        return jsonify({"error": "Database not connected."}), 500
    
    try:
        data = request.json
        selected_body_part = data.get('bodyPart')
        
        if not selected_body_part:
            return jsonify({"error": "No body part provided."}), 400

        exercises_collection = db['exercises']
        
        # Use MongoDB's aggregation pipeline to get 3 random documents
        # that match the selected body part.
        pipeline = [
            {"$match": {"bodyPart": selected_body_part}},
            {"$sample": {"size": 3}}
        ]
        
        # Convert the cursor results to a list
        random_exercises = list(exercises_collection.aggregate(pipeline))
        
        # Remove the ObjectId to make the result serializable to JSON
        for exercise in random_exercises:
            exercise.pop('_id', None)

        return jsonify(random_exercises)
    except Exception as e:
        print(f"Error getting random exercises: {e}")
        return jsonify({"error": "Failed to retrieve exercises."}), 500

# API endpoint to refresh the database with new exercises
@app.route('/api/refresh_db', methods=['POST'])
def api_refresh_db():
    try:
        # Call the function from database_refresh.py
        count = insert_exercises_if_not_exist()
        return jsonify({"message": f"Database refresh complete. {count} new exercises added."})
    except Exception as e:
        print(f"Error refreshing database: {e}")
        return jsonify({"error": "Failed to refresh database."}), 500

if __name__ == '__main__':
    # You may want to call connect_db() here from btm_workout_db_connect
    # to ensure the connection is established at app startup.
    app.run(debug=True)

