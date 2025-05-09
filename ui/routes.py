"""
routes.py: Static plugin control and UI routes.
"""
from flask import Blueprint, jsonify
from ui.views.dashboard import dashboard_view
from ui.views.config_editor import config_editor_view
from ui.views.logs import logs_view

bp = Blueprint("ui", __name__)

bp.add_url_rule("/dashboard", view_func=dashboard_view)
bp.add_url_rule("/config", view_func=config_editor_view)
bp.add_url_rule("/logs", view_func=logs_view)


def register_routes(app):
    app.register_blueprint(bp)
