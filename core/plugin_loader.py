"""
PluginLoader: Dynamically loads plugin modules.
"""

from importlib import import_module
from typing import Any


class PluginLoader:
    """Loads plugins dynamically by name."""

    def load(self, plugin_name: str) -> Any:
        module_path = f"plugins.{plugin_name}"
        return import_module(module_path)
