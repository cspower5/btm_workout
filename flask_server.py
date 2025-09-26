import json
import sqlite3
import random
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin 

# --- Initialization ---
app = Flask(__name__)

# --- Configuration ---
# NOTE: The global CORS(app) line is REMOVED to avoid deployment conflicts.
# The @cross_origin decorator is used on each route for guaranteed functionality.

def get_db_connection():
    # Use the database file in the project root
    conn = sqlite3.connect('btm_workout.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- API Routes (v1) ---

@app.route('/api/v1/body_parts_list', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_body_parts_list():
    conn = get_db_connection()
    body_parts = conn.execute('SELECT DISTINCT body_part FROM exercises ORDER BY body_part').fetchall()
    conn.close()
    
    # Convert Row objects to a list of strings
    body_parts_list = [part['body_part'] for part in body_parts]
    return jsonify(body_parts_list)

@app.route('/api/v1/exercise_list', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_exercise_list():
    body_part = request.args.get('body_part')
    conn = get_db_connection()
    
    if body_part:
        exercises = conn.execute('SELECT * FROM exercises WHERE body_part = ? ORDER BY exercise_name', (body_part,)).fetchall()
    else:
        exercises = conn.execute('SELECT * FROM exercises ORDER BY exercise_name').fetchall()
        
    conn.close()
    
    # Convert Row objects to list of dicts for JSON
    exercise_list = [dict(row) for row in exercises]
    return jsonify(exercise_list)

@app.route('/api/v1/random_exercises', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_get_random_exercises():
    try:
        body_part = request.args.get('body_part')
        num_exercises = int(request.args.get('num_exercises', 4))
    except ValueError:
        return jsonify({"error": "Invalid number of exercises specified."}), 400

    conn = get_db_connection()
    
    if body_part == 'All':
        all_exercises = conn.execute('SELECT * FROM exercises').fetchall()
    else:
        all_exercises = conn.execute('SELECT * FROM exercises WHERE body_part = ?', (body_part,)).fetchall()
        
    conn.close()

    if not all_exercises:
        return jsonify({"error": "No exercises found for this body part."}), 404

    # Select random exercises without replacement
    if len(all_exercises) < num_exercises:
        num_exercises = len(all_exercises) # Adjust if fewer exercises are available

    random_exercises = random.sample(all_exercises, num_exercises)
    
    # Convert to list of dicts
    result = [dict(row) for row in random_exercises]
    return jsonify(result)

@app.route('/api/v1/insert_exercise', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_insert_exercise():
    try:
        data = request.get_json()
        exercise_name = data['exercise_name']
        body_part = data['body_part']
        
        if not exercise_name or not body_part:
            return jsonify({"error": "Missing exercise_name or body_part"}), 400

        conn = get_db_connection()
        conn.execute('INSERT INTO exercises (exercise_name, body_part) VALUES (?, ?)', (exercise_name, body_part))
        conn.commit()
        conn.close()
        
        return jsonify({"message": f"Exercise '{exercise_name}' inserted successfully."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"Exercise '{exercise_name}' already exists for {body_part}."}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/update_exercise/<int:exercise_id>', methods=['PUT'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_update_exercise(exercise_id):
    try:
        data = request.get_json()
        new_name = data.get('exercise_name')
        new_part = data.get('body_part')

        if not new_name and not new_part:
            return jsonify({"error": "No update fields provided"}), 400

        conn = get_db_connection()
        
        updates = []
        params = []
        if new_name:
            updates.append("exercise_name = ?")
            params.append(new_name)
        if new_part:
            updates.append("body_part = ?")
            params.append(new_part)

        params.append(exercise_id)
        
        query = f"UPDATE exercises SET {', '.join(updates)} WHERE id = ?"
        cursor = conn.execute(query, params)
        conn.commit()
        conn.close()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Exercise not found."}), 404
            
        return jsonify({"message": f"Exercise ID {exercise_id} updated successfully."}), 200

    except sqlite3.IntegrityError:
        return jsonify({"error": "Update failed: Exercise name already exists for this body part."}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/delete_exercise/<int:exercise_id>', methods=['DELETE'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_delete_exercise(exercise_id):
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM exercises WHERE id = ?', (exercise_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Exercise not found."}), 404
        
    return jsonify({"message": f"Exercise ID {exercise_id} deleted successfully."}), 200

@app.route('/api/v1/search_exercise', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_search_exercise():
    query = request.args.get('query', '')
    if not query:
        return jsonify({"error": "Missing search query."}), 400

    conn = get_db_connection()
    
    # Use LIKE for partial matching on exercise name or body part
    search_term = f"%{query}%"
    exercises = conn.execute(
        'SELECT * FROM exercises WHERE exercise_name LIKE ? OR body_part LIKE ? ORDER BY exercise_name', 
        (search_term, search_term)
    ).fetchall()
        
    conn.close()
    
    result = [dict(row) for row in exercises]
    return jsonify(result)

# --- Database Management (Internal Utility Routes) ---

@app.route('/api/v1/db_schema', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_db_schema():
    conn = get_db_connection()
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='exercises'")
    schema = cursor.fetchone()
    conn.close()
    if schema:
        return jsonify({"schema": schema[0]}), 200
    return jsonify({"error": "Schema not found"}), 404

@app.route('/api/v1/count_exercises', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_count_exercises():
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM exercises').fetchone()[0]
    conn.close()
    return jsonify({"count": count}), 200

@app.route('/api/v1/delete_all_exercises', methods=['DELETE'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_delete_all_exercises():
    conn = get_db_connection()
    cursor = conn.execute('DELETE FROM exercises')
    conn.commit()
    conn.close()
    return jsonify({"message": f"{cursor.rowcount} exercises deleted."}), 200

@app.route('/api/v1/reset_db', methods=['POST'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_reset_db():
    try:
        conn = get_db_connection()
        
        # 1. Drop the table if it exists
        conn.execute("DROP TABLE IF EXISTS exercises")
        
        # 2. Re-create the table
        conn.execute("""
            CREATE TABLE exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_name TEXT NOT NULL,
                body_part TEXT NOT NULL,
                UNIQUE(exercise_name, body_part)
            )
        """)
        
        # 3. Insert initial seed data
        seed_data = [
            ('Squat', 'Legs'), ('Lunge', 'Legs'), ('Leg Press', 'Legs'),
            ('Bench Press', 'Chest'), ('Push-up', 'Chest'), ('Dumbbell Fly', 'Chest'),
            ('Deadlift', 'Back'), ('Pull-up', 'Back'), ('Row', 'Back'),
            ('Overhead Press', 'Shoulders'), ('Lateral Raise', 'Shoulders'),
            ('Bicep Curl', 'Arms'), ('Tricep Pushdown', 'Arms'), 
            ('Plank', 'Core'), ('Crunches', 'Core')
        ]
        conn.executemany('INSERT INTO exercises (exercise_name, body_part) VALUES (?, ?)', seed_data)

        conn.commit()
        conn.close()
        return jsonify({"message": "Database reset and seeded successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Error Handling ---

@app.errorhandler(404)
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def not_found(error):
    # This ensures a 404 response is still accessible by the frontend
    return jsonify({'error': 'Not Found', 'message': 'The requested URL was not found on the server. Please check the URL for typos.'}), 404

@app.errorhandler(500)
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def internal_error(error):
    # Log the error for debugging on the server
    app.logger.error('Server Error: %s', error)
    # This ensures a 500 response is still accessible by the frontend
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred on the server.'}), 500

# --- Health Check ---
@app.route('/api/v1/health', methods=['GET'])
@cross_origin(origins=['https://cspower5.github.io']) # <--- CORS Fix
def api_health_check():
    # Simple endpoint to confirm the server is running
    return jsonify({"status": "ok", "message": "API is running and healthy."}), 200


# --- Run Server (Production/Development) ---
if __name__ == '__main__':
    # This runs the server only in local development mode
    app.run(debug=True, port=5000)

