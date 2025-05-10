"""
Gather Plugin: Modular plugin for dynamic exchange/token selection using ccxt.
"""

import json

try:
    from bson import ObjectId
except ImportError:

    class ObjectId:
        pass


def run(context, config, pipeline):
    # Remove MongoDB _id field to avoid ObjectId serialization errors
    config = dict(config)
    config.pop('_id', None)
    """Main entry point for the gather plugin."""
    logger = context["services"]["log"]

    # Emit the full raw config as JSON (handle ObjectId or other non-serializable fields)
    def safe_json(obj):
        try:
            return json.dumps(
                obj,
                indent=2,
                default=lambda o: (
                    str(o) if isinstance(o, ObjectId) else f"<{type(o).__name__}>"
                ),
            )
        except Exception:
            return str(obj)

    logger.info(
        {
            "event": "gather_plugin_config_raw",
            "config_json": safe_json(config),
            "pipeline": pipeline,
        }
    )

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
        "exchange_tokenpairs": config.get("exchange_tokenpairs"),
        "exchange_database": config.get("exchange_database"),
        "indicator_database": config.get("indicator_database"),
        "plugin_id": config.get("plugin_id"),
        "pipeline": config.get("pipeline"),
    }
    if intervals_dict is not None:
        pipeline_config["intervals"] = intervals_dict

    logger.info(
        {
            "event": "gather_plugin_emit",
            "pipeline_config": pipeline_config,
            "pipeline": pipeline,
        }
    )
    # Add the pipeline_config to context so next plugin can access it
    context = dict(context)  # Do not mutate input directly
    context["gather_plugin_config"] = pipeline_config
    return {"status": "success", "pipeline_config": pipeline_config, "context": context}
