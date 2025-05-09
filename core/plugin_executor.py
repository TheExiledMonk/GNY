"""
PluginExecutor: Executes plugin.run() and applies error handling.
"""
from services.logger import get_logger
from typing import Any, Callable

class PluginExecutor:
    """Executes plugin run logic with error handling."""
    def __init__(self) -> None:
        self.logger = get_logger()

    def execute(self, plugin_run: Callable, context: dict, config: dict) -> Any:
        try:
            return plugin_run(context, config)
        except Exception as e:
            self.logger.error({"event": "plugin_error", "error": str(e)})
            raise
