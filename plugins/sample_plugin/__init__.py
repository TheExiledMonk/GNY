"""
Sample Plugin for demo/testing.
"""
PLUGIN_NAME = "sample_plugin"
HOOKS = ["fetch_data"]
PIPELINES = ["default"]
TAGS = ["example"]
VERSION = "0.1.0"
FAIL_HARD = False

def run(context, config):
    log = context["services"]["log"]
    log.info({"event": "sample_plugin_run", "config": config})
    # Your plugin logic here
    return {"status": "success"}

def get_config_ui():
    """
    Returns sample config for demo purposes.
    """
    return {
        "api_key": "sk-1234567890abcdef",
        "interval_minutes": 30,
        "enable_feature_x": True,
        "max_items": 100,
        "mode": "test",
        "advanced": {
            "retry": 3,
            "timeout": 10
        }
    }

def get_status():
    """
    Returns sample status for demo purposes.
    """
    from datetime import datetime
    return {
        "last_run": datetime.now().isoformat(timespec="seconds"),
        "health": "OK",
        "runs_today": 5,
        "last_result": "success",
        "error_count": 0,
        "queued": False
    }
