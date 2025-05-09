"""
PluginConfigRepo: Provides plugin config access via ConfigStorage.
"""
from db.config_storage import ConfigStorage
from typing import Optional, Dict, Any

class PluginConfigRepo:
    """Access layer for plugin configs (never direct DB access)."""
    def __init__(self, config_storage: ConfigStorage):
        self._storage = config_storage

    def get_plugin_config(self, plugin_id: str, pipeline: str) -> Optional[Dict[str, Any]]:
        results = self._storage.get("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline})
        return results[0] if results else None

    def update_plugin_config(self, plugin_id: str, pipeline: str, config: dict) -> None:
        self._storage.update("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline}, config)

    def insert_plugin_config(self, plugin_id: str, pipeline: str, config: dict) -> None:
        self._storage.insert("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline, **config})
