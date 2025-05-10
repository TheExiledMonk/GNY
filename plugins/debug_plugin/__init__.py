"""
Debug Plugin: Insert anywhere in the pipeline to probe and log context/config for debugging.
"""
import json
import threading
from typing import Any, Dict
import os

LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs", "debug_plugins.log"))
_log_lock = threading.Lock()

def run(context: Dict[str, Any], config: Dict[str, Any], pipeline: str) -> Dict[str, Any]:
    """
    Main entry point for the debug plugin. Logs context and config to logs/debug_plugins.log.
    Additionally, adds a marker to the context to verify context mutation in the orchestrator chain.
    Each entry includes:
      - timestamp (UTC, ISO8601)
      - event (string)
      - pipeline (string)
      - pipeline_step (if present in context or config)
      - context (dict)
      - config (dict)
    """
    from datetime import datetime
    pipeline_step = context.get("step") or config.get("step") or context.get("pipeline_step") or config.get("pipeline_step")
    # Add a marker to context to verify mutation
    context = dict(context)  # Copy to avoid mutating input directly
    context["debug_plugin_visited"] = True
    context["debug_plugin_timestamp"] = datetime.utcnow().isoformat() + "Z"
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": "debug_plugin_probe",
        "pipeline": pipeline,
        "context": context,
        "config": config
    }
    if pipeline_step is not None:
        entry["pipeline_step"] = pipeline_step
    log_entry(entry)
    return {"status": "logged", "probe": True, "context": context}


def log_entry(entry: Dict[str, Any]) -> None:
    """
    Thread-safe structured logging to debug_plugins.log.
    Each entry is written as a single-line JSON (JSONL format) for robust parsing in the UI.
    Fields:
      - timestamp (UTC, ISO8601)
      - event (string)
      - pipeline (string)
      - pipeline_step (optional)
      - context (dict)
      - config (dict)
    """
    with _log_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

def status() -> str:
    """
    Returns the contents of the debug_plugins.log file (for UI display).
    Always returns a string, never raises, so the UI never 500s.
    """
    try:
        if not os.path.exists(LOG_PATH):
            return "No debug logs found."
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return f.read()[-10000:]  # Show only last 10k chars for safety
    except Exception as e:
        # Log the error to a fallback log file
        try:
            with open(os.path.join(os.path.dirname(LOG_PATH), "debug_plugin_errors.log"), "a", encoding="utf-8") as ferr:
                ferr.write(f"[status error] {e}\n")
        except Exception:
            pass  # Don't let fallback logging raise
        return f"[ERROR] Could not read debug log: {type(e).__name__}: {e}"

from .config_ui import debug_plugin_status_view

from flask import request

def get_status(req=None):
    """
    Flask-compatible status view for the debug plugin, handles GET and POST (log clearing).
    Accepts Flask request as arg (for plugin_status_view delegation compatibility).
    """
    from .config_ui import debug_plugin_status_view
    # Use the passed-in request if provided, else import from Flask context
    req = req or request
    return debug_plugin_status_view(req)

