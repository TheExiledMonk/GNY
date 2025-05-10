"""
server.py: Flask app entrypoint for the Orchestration Framework UI.
"""
from flask import Flask
from ui.routes import register_routes
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")
register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
