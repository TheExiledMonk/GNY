"""
login.py: Login view for the UI Flask app.
"""

import os

from flask import redirect, request, session, url_for


def login_view():
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["user"] = username
            return redirect(url_for("ui.dashboard_view"))
        return "<h2>Login failed</h2><a href='/'>Try again</a>", 401
    # GET fallback (shouldn't be used)
    return redirect(url_for("ui.dashboard_view"))
