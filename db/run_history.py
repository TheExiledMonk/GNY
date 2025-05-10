"""
RunHistory: Tracks execution logs and status in MongoDB via ConfigStorage.
"""

from datetime import datetime
from typing import Any, Dict

from db.config_storage import ConfigStorage


class RunHistory:
    """Tracks pipeline/plugin execution status and logs."""

    def __init__(self, config_storage: ConfigStorage):
        self._storage = config_storage

    def log_run(
        self, pipeline: str, plugin: str, status: str, details: Dict[str, Any]
    ) -> None:
        entry = {
            "pipeline": pipeline,
            "plugin": plugin,
            "status": status,
            "details": details,
            "timestamp": datetime.utcnow(),
        }
        self._storage.insert("run_history", entry)

    def get_runs(self, pipeline: str = None, plugin: str = None) -> Any:
        query = {}
        if pipeline:
            query["pipeline"] = pipeline
        if plugin:
            query["plugin"] = plugin
        return self._storage.get("run_history", query)
