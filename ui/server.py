"""
server.py: Flask app entrypoint for the Orchestration Framework UI.
"""
from flask import Flask
from ui.routes import register_routes

app = Flask(__name__)
register_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
