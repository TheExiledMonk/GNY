"""
routes.py: Static plugin control and UI routes.
"""

from flask import Blueprint, render_template

from ui.views.config_editor import config_editor_view
from ui.views.dashboard import dashboard_view, trigger_pipeline_view
from ui.views.health import health_view
from ui.views.jobs import jobs_html_view, jobs_status_view, job_action_view
from ui.views.login import login_view
from ui.views.logs import logs_view
from ui.views.plugins import plugin_config_view, plugin_status_view
from ui.views.control import control_view, restart_view, stop_view

bp = Blueprint("ui", __name__)

bp.add_url_rule("/dashboard", view_func=dashboard_view)
bp.add_url_rule("/", view_func=dashboard_view)
bp.add_url_rule("/index", view_func=dashboard_view)
bp.add_url_rule("/trigger", view_func=trigger_pipeline_view, methods=["POST"])

bp.add_url_rule("/config", view_func=config_editor_view, methods=["GET", "POST"])
bp.add_url_rule("/logs", view_func=logs_view)
bp.add_url_rule("/jobs", view_func=jobs_html_view, methods=["GET"])
bp.add_url_rule("/jobs/status", view_func=jobs_status_view, methods=["GET"])
bp.add_url_rule("/jobs/action", view_func=job_action_view, methods=["POST"])

bp.add_url_rule("/control", view_func=control_view)
bp.add_url_rule("/control/restart", view_func=restart_view, methods=["POST"])
bp.add_url_rule("/control/stop", view_func=stop_view, methods=["POST"])

bp.add_url_rule(
    "/plugins/<plugin>/config", view_func=plugin_config_view, methods=["GET", "POST"]
)
bp.add_url_rule(
    "/plugins/<plugin>/status", view_func=plugin_status_view, methods=["GET", "POST"]
)
bp.add_url_rule("/login", view_func=login_view, methods=["POST"])
bp.add_url_rule("/health", view_func=health_view, methods=["GET"])


def register_routes(app):
    # control_view, restart_view, stop_view are already routed via bp above
    app.register_blueprint(bp)
