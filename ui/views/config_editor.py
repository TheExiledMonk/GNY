"""
config_editor.py: Load/save plugin configs.
"""
from flask import request, render_template, redirect, url_for, session
from ui.utils import get_navbar, get_menu, get_plugin_names, require_auth
import os
import yaml
from services.logger import get_logger

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config')
SYSTEM_YAML_PATH = os.path.join(CONFIG_DIR, 'system.yaml')
PIPELINES_YAML_PATH = os.path.join(CONFIG_DIR, 'pipelines.yaml')


def config_editor_view():
    require_auth(session)
    logger = get_logger()
    error = None
    message = None
    system_yaml = ''
    pipelines_yaml = ''

    # Load YAML files
    try:
        with open(SYSTEM_YAML_PATH, 'r') as f:
            system_yaml = f.read()
    except Exception as e:
        error = f"Error reading system.yaml: {e}"
        logger.error({"event": "config_editor_read_error", "file": "system.yaml", "error": str(e)})
    try:
        with open(PIPELINES_YAML_PATH, 'r') as f:
            pipelines_yaml = f.read()
    except Exception as e:
        error = (error or "") + f" Error reading pipelines.yaml: {e}"
        logger.error({"event": "config_editor_read_error", "file": "pipelines.yaml", "error": str(e)})

    # Handle POST (save)
    if request.method == "POST":
        new_system_yaml = request.form.get("system_yaml", "")
        new_pipelines_yaml = request.form.get("pipelines_yaml", "")
        # Validate YAML
        try:
            yaml.safe_load(new_system_yaml)
            yaml.safe_load(new_pipelines_yaml)
            # Save
            with open(SYSTEM_YAML_PATH, 'w') as f:
                f.write(new_system_yaml)
            with open(PIPELINES_YAML_PATH, 'w') as f:
                f.write(new_pipelines_yaml)
            message = "Configuration saved successfully."
            system_yaml = new_system_yaml
            pipelines_yaml = new_pipelines_yaml
        except yaml.YAMLError as e:
            error = f"YAML syntax error: {e}"
            logger.error({"event": "config_editor_yaml_error", "error": str(e)})
        except Exception as e:
            error = f"Error saving configuration: {e}"
            logger.error({"event": "config_editor_save_error", "error": str(e)})

    return render_template(
        "config_editor.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        system_yaml=system_yaml,
        pipelines_yaml=pipelines_yaml,
        error=error,
        message=message,
    )
