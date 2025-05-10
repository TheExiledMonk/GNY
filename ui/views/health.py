"""
health.py: System health/status endpoint for the Flask UI app.
"""
from flask import render_template, session
from services.resource_monitor import ResourceMonitor
from ui.utils import get_navbar, get_menu, get_plugin_names, require_auth

def health_view():
    require_auth(session)
    stats = ResourceMonitor().get_stats()
    return render_template(
        "health.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        stats=stats,
    )
