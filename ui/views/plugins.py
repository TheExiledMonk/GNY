"""
Dynamic plugin config and status endpoints for the UI Flask app.
"""
from flask import render_template, request, session
from ui.utils import require_auth
import importlib
from services.config_manager import ConfigManager
from typing import Any

def make_json_safe(val: Any) -> Any:
    """Recursively make a value JSON serializable."""
    import json
    if isinstance(val, dict):
        return {k: make_json_safe(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [make_json_safe(v) for v in val]
    elif 'bson' in str(type(val)) or type(val).__name__ == 'ObjectId':
        return str(val)
    else:
        try:
            json.dumps(val)
            return val
        except Exception:
            return str(val)

def _render_plugin_config(mod: Any, plugin: str) -> str:
    """Render the generic plugin config UI."""
    from ui.utils import get_plugin_names, get_menu, get_navbar
    config_manager = ConfigManager()
    config = config_manager.get_plugin_config(plugin, None)
    message = None
    navbar = get_navbar()
    menu = get_menu(get_plugin_names())
    config_serializable = make_json_safe(config)
    return render_template('plugin_config.html',
        navbar=navbar,
        menu=menu,
        plugin=plugin,
        pipeline=None,
        config=config,
        config_serializable=config_serializable,
        message=message,
        config_html=mod.handle_config_request(request, config, None, message, config_manager))

def plugin_config_view(plugin: str) -> str:
    require_auth(session)
    # Special-case: use gather_plugin's own UI handler/template
    if plugin == "gather_plugin":
        from plugins.gather_plugin.config_ui import handle_config_request
        from ui.utils import get_plugin_names, get_menu, get_navbar
        config_manager = ConfigManager()
        config = config_manager.get_plugin_config(plugin, None)
        message = None
        pipeline = None
        plugin_config_repo = config_manager
        return handle_config_request(request, config, pipeline, message, plugin_config_repo)
    # Generic fallback for plugins without their own UI
    try:
        mod = importlib.import_module(f"plugins.{plugin}")
    except Exception as e:
        from services.logger import get_logger
        get_logger().error({
            "event": "plugin_import_error",
            "plugin": plugin,
            "error": str(e),
        })
        return f"<h2>Error loading plugin '{plugin}': {e}</h2>", 500
    if hasattr(mod, "handle_config_request"):
        return _render_plugin_config(mod, plugin)
    return f"<h2>Plugin '{plugin}' does not provide handle_config_request(). No config UI available.</h2>", 501

def plugin_status_view(plugin):
    """
    Dynamic status endpoint for plugins. Returns HTML or Response for plugin status UI.
    Handles plugins that return Flask Response, string, or dict.
    Delegates to plugin's get_status(request) if present and callable.
    """
    require_auth(session)
    try:
        import importlib
        from flask import request, Response
        mod = importlib.import_module(f"plugins.{plugin}")
        get_status = getattr(mod, "get_status", None)
        if callable(get_status):
            return get_status(request)
        # fallback to old logic
        status = getattr(mod, "status", lambda: {"error": "No status available"})()
        if isinstance(status, Response) or isinstance(status, str):
            return status
        return str(status)
    except Exception as e:
        status = {"error": str(e)}
        return f"<h2>Status for {plugin}</h2><pre>{status}</pre>"
