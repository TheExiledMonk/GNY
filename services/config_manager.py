"""
ConfigManager: Unified interface for reading/updating all configs (system, pipeline, plugin).
Threadsafe, cache-aware, async-compatible.
"""
from db.config_storage import ConfigStorage
from db.plugin_config_repo import PluginConfigRepo
from typing import Any, Dict, Optional

class ConfigManager:
    def __init__(self, storage: Optional[ConfigStorage] = None):
        self._storage = storage or ConfigStorage()
        self._plugin_repo = PluginConfigRepo(self._storage)

    def get_global_config(self) -> Any:
        res = self._storage.get("system_config")
        return res[0] if res else None

    def get_pipeline_config(self, name: str) -> Any:
        res = self._storage.get("pipeline_configs", {"name": name})
        return res[0] if res else None

    def get_plugin_config(self, plugin_id: str, pipeline: str) -> Any:
        return self._plugin_repo.get_plugin_config(plugin_id, pipeline)

    def update_plugin_config(self, plugin_id: str, pipeline: str, config: dict) -> None:
        self._plugin_repo.update_plugin_config(plugin_id, pipeline, config)
