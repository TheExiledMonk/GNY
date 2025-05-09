"""
Gather Plugin: Modular plugin for dynamic exchange/token selection using ccxt.
"""

from fastapi import APIRouter
from .config_ui import gather_config_router, handle_config_request
from .core import get_default_config, get_supported_exchanges, get_tokens_for_exchanges, get_stablecoins_for_exchanges
import logging

# Register the router for config UI
router = APIRouter()
router.include_router(gather_config_router, prefix="/config", tags=["gather_plugin_config"])

def run(context, config, pipeline):
    """Main entry point for the gather plugin."""
    logger = context["services"]["log"]

    # Emit the full raw config as JSON (handle ObjectId or other non-serializable fields)
    def safe_json(obj):
        try:
            return json.dumps(obj, indent=2, default=lambda o: str(o) if isinstance(o, ObjectId) else f"<{type(o).__name__}>")
        except Exception as e:
            return str(obj)
    logger.info({"event": "gather_plugin_config_raw", "config_json": safe_json(config), "pipeline": pipeline})

    logger.info({"event": "gather_plugin_run", "config": config, "pipeline": pipeline})
    # Parse intervals from config (accept comma-separated string or list)
    intervals = config.get("intervals")
    if isinstance(intervals, dict):
        intervals_dict = intervals
    elif isinstance(intervals, list):
        intervals_dict = {i: True for i in intervals}
    elif isinstance(intervals, str):
        intervals_dict = {i.strip(): True for i in intervals.split(",") if i.strip()}
    else:
        intervals_dict = None
    pipeline_config = {
        "base_stablecoin": config.get("base_stablecoin"),
        "exchanges": config.get("exchanges", []),
        "stablecoins": config.get("stablecoins", []),
        "tokens": config.get("tokens", []),
    }
    if intervals_dict is not None:
        pipeline_config["intervals"] = intervals_dict

    logger.info({"event": "gather_plugin_emit", "pipeline_config": pipeline_config, "pipeline": pipeline})
    return {"status": "success", "pipeline_config": pipeline_config}

def run(context, config, pipeline):
    """Main entry point for the gather plugin."""
    logger = context["services"]["log"]

    # Emit the full raw config as JSON (handle ObjectId or other non-serializable fields)
    def safe_json(obj):
        try:
            return json.dumps(obj, indent=2, default=lambda o: str(o) if isinstance(o, ObjectId) else f"<{type(o).__name__}>")
        except Exception as e:
            return str(obj)
    logger.info({"event": "gather_plugin_config_raw", "config_json": safe_json(config), "pipeline": pipeline})

    logger.info({"event": "gather_plugin_run", "config": config, "pipeline": pipeline})
    # Parse intervals from config (accept comma-separated string or list)
    intervals = config.get("intervals")
    if isinstance(intervals, dict):
        intervals_dict = intervals
    elif isinstance(intervals, list):
        intervals_dict = {i: True for i in intervals}
    elif isinstance(intervals, str):
        intervals_dict = {i.strip(): True for i in intervals.split(",") if i.strip()}
    else:
        intervals_dict = None
    pipeline_config = {
        "base_stablecoin": config.get("base_stablecoin"),
        "exchanges": config.get("exchanges", []),
        "stablecoins": config.get("stablecoins", []),
        "tokens": config.get("tokens", []),
    }
    if intervals_dict is not None:
        pipeline_config["intervals"] = intervals_dict

    logger.info({"event": "gather_plugin_emit", "pipeline_config": pipeline_config, "pipeline": pipeline})
    return {"status": "success", "pipeline_config": pipeline_config}





