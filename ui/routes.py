"""
routes.py: Static plugin control and UI routes.
"""
from flask import Blueprint, jsonify
from ui.views.dashboard import dashboard_view
from ui.views.config_editor import config_editor_view
from ui.views.logs import logs_view
from ui.views.jobs import jobs_view, job_action_view

bp = Blueprint("ui", __name__)

bp.add_url_rule("/dashboard", view_func=dashboard_view)
bp.add_url_rule("/config", view_func=config_editor_view)
bp.add_url_rule("/logs", view_func=logs_view)
bp.add_url_rule("/jobs", view_func=jobs_view, methods=["GET"])
bp.add_url_rule("/job_action", view_func=job_action_view, methods=["POST"])


def register_routes(app):
    app.register_blueprint(bp)
