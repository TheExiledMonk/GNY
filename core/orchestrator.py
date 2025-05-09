"""
Orchestrator: Runs pipelines, resolves hooks/plugins, passes context, manages threads.
"""
import yaml
from core.hook_registry import HookRegistry
from core.plugin_executor import PluginExecutor
from core.context_builder import build_context
from core.thread_manager import ThreadManager
from services.logger import get_logger
from services.config_manager import ConfigManager
from core.plugin_loader import PluginLoader
from typing import Any, Dict, List
import os

class Orchestrator:
    """Main orchestrator for pipeline execution."""
    def __init__(self) -> None:
        self.logger = get_logger()
        self.hook_registry = HookRegistry()
        self.plugin_executor = PluginExecutor()
        self.thread_manager = ThreadManager()
        self.config_manager = ConfigManager()
        self.plugin_loader = PluginLoader()
        self.pipelines = self._load_pipelines()
        self._register_hooks_plugins()

    def _load_pipelines(self) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "pipelines.yaml")
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
        return raw.get("pipelines", {})

    def _register_hooks_plugins(self):
        # Example: Register hooks and map to plugin names (from config or convention)
        for pipeline, pdata in self.pipelines.items():
            for hook in pdata.get("hooks", []):
                # For demo, assume plugin name == hook name + "_plugin"
                plugin_name = f"{hook}_plugin"
                self.hook_registry.register(hook, [plugin_name])

    def run(self) -> None:
        self.logger.info({"event": "orchestrator_start"})
        for pipeline_name in self.pipelines:
            self.thread_manager.start_pipeline_thread(
                pipeline_name,
                self._run_pipeline,
                pipeline_name
            )

    def _run_pipeline(self, pipeline_name: str):
        pdata = self.pipelines[pipeline_name]
        hooks = pdata.get("hooks", [])
        for hook in hooks:
            plugin_ids = self.hook_registry.get_plugins(hook)
            for plugin_id in plugin_ids:
                try:
                    plugin_mod = self.plugin_loader.load(plugin_id)
                    context = build_context(pipeline_name, hook)
                    config = self.config_manager.get_plugin_config(plugin_id, pipeline_name)
                    self.plugin_executor.execute(plugin_mod.run, context, config or {})
                    self.logger.info({"event": "plugin_run", "plugin": plugin_id, "pipeline": pipeline_name, "hook": hook})
                except Exception as e:
                    self.logger.error({"event": "plugin_error", "plugin": plugin_id, "pipeline": pipeline_name, "hook": hook, "error": str(e)})
