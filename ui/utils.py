"""
utils.py: Shared UI helper functions (navbar, menu, plugin names, auth).
"""

import os
from typing import Optional

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")


def is_authenticated(session) -> bool:
    """Check if the user is authenticated (session-based)."""
    return session.get("user") == ADMIN_USERNAME


def require_auth(session):
    if not is_authenticated(session):
        from flask import abort

        abort(401, description="Not authenticated")


def get_navbar() -> str:
    """Return the HTML for the navbar."""
    return """
    <nav class="navbar-gny">
      <div class="navbar-title">GNY DataWarehouse NexGen</div>
      <form method="post" action="/logout" class="navbar-logout-form">
        <button class="navbar-logout-btn">Logout</button>
      </form>
    </nav>
    """


def get_menu(plugins: Optional[list] = None) -> str:
    """Return the HTML for the menu bar, matching the original dropdown and styles from api_server_DEAD.py."""
    if not plugins:
        return """
        <div class="menu-bar">
          <div class="menu-item">
            <span class="menu-link">Plugins</span>
          </div>
          <a href="/health" class="menu-link">System Health</a>
          <a href="/logs" class="menu-link">Logs</a>
        </div>"""
    submenu = "".join(
        f"""
      <div class="plugin-dropdown-item">
        <span class="plugin-name">{p}</span>
        <div class="plugin-submenu">
          <a href="/plugins/{p}/config" class="plugin-menu-link">Config</a>
          <a href="/plugins/{p}/status" class="plugin-menu-link">Status</a>
        </div>
      </div>
    """
        for p in plugins
    )
    return f"""
    <div class="menu-bar">
      <div class="plugin-dropdown">
        <span class="menu-link plugin-label">Plugins ▾</span>
        <div class="plugin-dropdown-list">
          {submenu}
        </div>
      </div>
      <a href="/" class="menu-link">Pipelines</a>
      <a href="/config" class="menu-link">System Config</a>
      <a href="/health" class="menu-link">System Health</a>
      <a href="/logs" class="menu-link">Logs</a>
      <a href="/jobs" class="menu-link">Jobs</a>
    </div>
    """


def get_plugin_names() -> list:
    """Return a list of plugin names. Assumes plugins are in plugins/ directory."""
    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
    try:
        return [
            d
            for d in os.listdir(plugins_dir)
            if os.path.isdir(os.path.join(plugins_dir, d)) and not d.startswith("__")
        ]
    except Exception:
        return []
