"""
dashboard.py: Plugin/pipeline overview view.
"""
from flask import jsonify

def dashboard_view():
    # TODO: Fetch pipeline/plugin status from orchestrator
    return jsonify({"status": "ok", "message": "Dashboard placeholder"})
