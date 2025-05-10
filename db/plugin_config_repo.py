"""
PluginConfigRepo: Provides plugin config access via ConfigStorage.
"""
from db.config_storage import ConfigStorage
from typing import Optional, Dict, Any

class PluginConfigRepo:
    """Access layer for plugin configs (never direct DB access)."""
    def __init__(self, config_storage: ConfigStorage):
        self._storage = config_storage

    def delete_plugin_config(self, plugin_id: str, pipeline: str, db_name: str = None) -> None:
        """Delete plugin config for a given plugin_id and pipeline."""
        self._storage.delete("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline}, db_name=db_name)

    def delete_plugin_config(self, plugin_id: str, pipeline: str, db_name: str = None) -> None:
        """Delete plugin config for a given plugin_id and pipeline."""
        self._storage.delete("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline}, db_name=db_name)
    def get_plugin_config(self, plugin_id: str, pipeline: str, db_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch plugin config from the specified database if db_name is provided, else default.
        """
        results = self._storage.get("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline}, db_name=db_name)
        return results[0] if results else None

    def update_plugin_config(self, plugin_id: str, pipeline: str, config: dict, db_name: str = None) -> None:
        """
        Update plugin config in the specified database if db_name is provided, else default.
        Ensures plugin_id and pipeline are present in the config document for upsert/replace semantics.
        """
        doc = dict(config)
        doc["plugin_id"] = plugin_id
        doc["pipeline"] = pipeline
        self._storage.update("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline}, doc, upsert=True, db_name=db_name)

    def insert_plugin_config(self, plugin_id: str, pipeline: str, config: dict, db_name: str = None) -> None:
        """
        Insert plugin config into the specified database if db_name is provided, else default.
        """
        self._storage.insert("plugin_configs", {"plugin_id": plugin_id, "pipeline": pipeline, **config}, db_name=db_name)

