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
from typing import Any, Dict
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
        """Load pipelines from config file."""
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "pipelines.yaml")
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
        return raw.get("pipelines", {})

    def _register_hooks_plugins(self) -> None:
        """Register hooks and plugins."""
        for pipeline, pdata in self.pipelines.items():
            for hook in pdata.get("hooks", []):
                plugin_name = f"{hook}_plugin"
                self.hook_registry.register(hook, [plugin_name])

    def run(self) -> None:
        """Run the orchestrator."""
        self.logger.info({"event": "orchestrator_start"})
        for pipeline_name in self.pipelines:
            self.thread_manager.start_pipeline_thread(
                pipeline_name,
                self._run_pipeline,
                pipeline_name
            )

    def _run_pipeline(self, pipeline_name: str) -> None:
        """Run a pipeline."""
        pdata = self.pipelines[pipeline_name]
        hooks = pdata.get("hooks", [])
        for hook in hooks:
            plugin_ids = self.hook_registry.get_plugins(hook)
            for plugin_id in plugin_ids:
                try:
                    execute_plugin_for_pipeline(
                        plugin_id=plugin_id,
                        pipeline_name=pipeline_name,
                        hook=hook,
                        pipelines=self.pipelines,
                        plugin_loader=self.plugin_loader,
                        config_manager=self.config_manager,
                        plugin_executor=self.plugin_executor,
                        logger=self.logger
                    )
                except Exception as e:
                    self.logger.error({"event": "plugin_error", "plugin": plugin_id, "pipeline": pipeline_name, "hook": hook, "error": str(e)})


def execute_plugin_for_pipeline(
    plugin_id: str,
    pipeline_name: str,
    hook: str,
    pipelines: Dict[str, Any],
    plugin_loader: Any,
    config_manager: Any,
    plugin_executor: Any,
    logger: Any
) -> None:
    """Helper to load, build context, and execute a plugin for a pipeline/hook."""
    plugin_mod = plugin_loader.load(plugin_id)
    context = build_context(pipeline_name, hook)
    pdata = pipelines[pipeline_name]
    command = pdata.get('command')
    context['command'] = command if command is not None else None
    config = config_manager.get_plugin_config(plugin_id, pipeline_name)
    plugin_executor.execute(plugin_mod.run, context, config or {}, pipeline_name)
    logger.info({"event": "plugin_run", "plugin": plugin_id, "pipeline": pipeline_name, "hook": hook})
