"""
HookRegistry: Maintains mapping from hooks to plugin IDs.
"""
from typing import Dict, List

class HookRegistry:
    """
    Central registry for hook to plugin mapping.
    For orchestrator-internal use only.
    """
    def __init__(self) -> None:
        self.hook_map: Dict[str, List[str]] = {}

    def register(self, hook: str, plugin_ids: List[str]) -> None:
        """
        Register a list of plugin IDs for a given hook.
        """
        self.hook_map[hook] = plugin_ids

    def get_plugins(self, hook: str) -> List[str]:
        """
        Get the list of plugin IDs registered for a given hook.
        """
        return self.hook_map.get(hook, [])
