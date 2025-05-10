"""
health.py: System health/status endpoint for the Flask UI app.
"""
from flask import render_template
from services.resource_monitor import ResourceMonitor
from services.api_server import get_navbar, get_menu, get_plugin_names, require_auth

def health_view():
    require_auth()
    stats = ResourceMonitor().get_stats()
    return render_template(
        "health.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        stats=stats,
    )
