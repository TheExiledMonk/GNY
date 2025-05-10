"""
Dynamic plugin config and status endpoints for the UI Flask app.
"""
from flask import request
from services.api_server import get_navbar, get_menu, get_plugin_names, require_auth
import importlib
from services.config_manager import ConfigManager

def plugin_config_view(plugin):
    require_auth()
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
        config_manager = ConfigManager()
        config = config_manager.get_plugin_config(plugin, None)
        message = None
        config_html = mod.handle_config_request(request, config, None, message, config_manager)
        box_style = "max-width:700px;margin:2.5em auto 0 auto;padding:2em 2.5em;background:#fff;border-radius:12px;box-shadow:0 2px 16px #0001;"
        navbar = get_navbar()
        menu = get_menu(get_plugin_names())
        full_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset=\"utf-8\">
          <title>Plugin Config</title>
          <style>body{{margin:0;font-family:sans-serif;background:#f6f8fb;}}</style>
        </head>
        <body>
          {navbar}
          {menu}
          <div style=\"{box_style}\">
            {config_html}
          </div>
        </body>
        </html>
        '''
        return full_html
    return f"<h2>Plugin '{plugin}' does not provide handle_config_request(). No config UI available.</h2>", 501

def plugin_status_view(plugin):
    require_auth()
    try:
        mod = importlib.import_module(f"plugins.{plugin}")
        status = getattr(mod, "get_status", lambda: {"error": "No status available"})()
    except Exception as e:
        status = {"error": str(e)}
    navbar = get_navbar()
    menu = get_menu(get_plugin_names())
    return f"<h2>Status for {plugin}</h2><pre>{status}</pre>"
