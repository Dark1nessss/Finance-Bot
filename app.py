from flask import Flask
from flask_socketio import SocketIO
from routes import init_routes
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'
socketio = SocketIO(app)

if __name__ == '__main__':
    def initialize_database():
        try:
            subprocess.run(['python', 'initdb.py', 'insert_data.py'], check=True)
            print("Database initialized successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Database initialization failed: {e}")

    initialize_database()
    init_routes(app, socketio)
    socketio.run(app, debug=True)