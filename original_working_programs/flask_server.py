from flask import Flask, render_template, jsonify
from list_body_parts import get_body_parts

app = Flask(__name__)

# Route to serve the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get the list of body parts
@app.route('/api/body_parts')
def api_body_parts():
    body_parts = get_body_parts()
    return jsonify(body_parts)

if __name__ == '__main__':
    app.run(debug=True)
