"""
config_editor.py: Load/save plugin configs.
"""

import os

import yaml
from flask import render_template, request, session

from services.logger import get_logger
from ui.utils import get_menu, get_navbar, get_plugin_names, require_auth

CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config"
)
SYSTEM_YAML_PATH = os.path.join(CONFIG_DIR, "system.yaml")
PIPELINES_YAML_PATH = os.path.join(CONFIG_DIR, "pipelines.yaml")


from typing import Optional, Tuple


def _read_yaml_file(path: str, logger) -> Tuple[str, Optional[str]]:
    """Read YAML file and return contents or error message."""
    try:
        with open(path, "r") as f:
            return f.read(), None
    except Exception as e:
        logger.error(
            {
                "event": "config_editor_read_error",
                "file": os.path.basename(path),
                "error": str(e),
            }
        )
        return "", f"Error reading {os.path.basename(path)}: {e}"


def _save_yaml_file(path: str, content: str, logger) -> Optional[str]:
    """Save YAML file and return error message if any."""
    try:
        with open(path, "w") as f:
            f.write(content)
        return None
    except Exception as e:
        logger.error(
            {
                "event": "config_editor_save_error",
                "file": os.path.basename(path),
                "error": str(e),
            }
        )
        return f"Error saving {os.path.basename(path)}: {e}"


def _validate_yaml(content: str, logger) -> Optional[str]:
    """Validate YAML content and return error message if any."""
    try:
        yaml.safe_load(content)
        return None
    except yaml.YAMLError as e:
        logger.error({"event": "config_editor_yaml_error", "error": str(e)})
        return f"YAML syntax error: {e}"


def config_editor_view():
    require_auth(session)
    logger = get_logger()
    error = None
    message = None
    system_yaml, err1 = _read_yaml_file(SYSTEM_YAML_PATH, logger)
    pipelines_yaml, err2 = _read_yaml_file(PIPELINES_YAML_PATH, logger)
    error = err1 or err2

    if request.method == "POST":
        new_system_yaml = request.form.get("system_yaml", "")
        new_pipelines_yaml = request.form.get("pipelines_yaml", "")
        err_sys = _validate_yaml(new_system_yaml, logger)
        err_pipe = _validate_yaml(new_pipelines_yaml, logger)
        if not err_sys and not err_pipe:
            err1 = _save_yaml_file(SYSTEM_YAML_PATH, new_system_yaml, logger)
            err2 = _save_yaml_file(PIPELINES_YAML_PATH, new_pipelines_yaml, logger)
            if not err1 and not err2:
                message = "Configuration saved successfully."
                system_yaml = new_system_yaml
                pipelines_yaml = new_pipelines_yaml
            else:
                error = (err1 or "") + (err2 or "")
        else:
            error = (err_sys or "") + (err_pipe or "")

    return render_template(
        "config_editor.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        system_yaml=system_yaml,
        pipelines_yaml=pipelines_yaml,
        error=error,
        message=message,
    )
