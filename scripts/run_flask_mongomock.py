#!/usr/bin/env python3
import mongomock

import btm_workout_db_connect as db_connect
import flask_server


def main():
    # Attach a mongomock client and db to the db_connect module
    client = mongomock.MongoClient()
    db = client.get_database("btm_workout_db")
    db_connect.client = client
    db_connect.db = db

    print("Starting Flask app with mongomock-backed DB on http://127.0.0.1:5000")
    # Run Flask app; use a non-blocking call which is fine when run as a subprocess
    flask_server.app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
