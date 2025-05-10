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

    def trigger_pipeline(self, pipeline_name: str) -> str:
        """
        Synchronously runs the specified pipeline once. Used by the UI /trigger endpoint.
        Logs trigger events and errors.
        Returns a user-friendly status string.
        """
        if pipeline_name not in self.pipelines:
            self.logger.error({
                "event": "trigger_pipeline_error",
                "pipeline": pipeline_name,
                "error": "Pipeline not found"
            })
            return f"Pipeline '{pipeline_name}' not found."
        try:
            self.logger.info({"event": "trigger_pipeline", "pipeline": pipeline_name})
            self._run_pipeline(pipeline_name)
            return "Triggered successfully."
        except Exception as e:
            self.logger.error({
                "event": "trigger_pipeline_error",
                "pipeline": pipeline_name,
                "error": str(e)
            })
            return f"Error triggering pipeline: {e}"

    def _run_pipeline(self, pipeline_name: str) -> None:
        """
        Run a pipeline. Pass a cumulative context object through the plugin chain, so each plugin can update and see the full pipeline context. Each plugin still receives its own config from the config manager.
        """
        pdata = self.pipelines[pipeline_name]
        hooks = pdata.get("hooks", [])
        # Build initial context once for the pipeline
        context = build_context(pipeline_name, hooks[0] if hooks else None)
        for hook in hooks:
            plugin_ids = self.hook_registry.get_plugins(hook)
            for plugin_id in plugin_ids:
                try:
                    # Each plugin gets its own config
                    config = self.config_manager.get_plugin_config(plugin_id, pipeline_name) or {}
                    # Execute plugin, passing cumulative context
                    new_context = execute_plugin_for_pipeline_with_context(
                        plugin_id=plugin_id,
                        pipeline_name=pipeline_name,
                        hook=hook,
                        pipelines=self.pipelines,
                        plugin_loader=self.plugin_loader,
                        plugin_executor=self.plugin_executor,
                        logger=self.logger,
                        context=context,
                        config=config
                    )
                    # Update context if plugin returned a new one
                    if new_context is not None:
                        context = new_context
                except Exception as e:
                    self.logger.error({
                        "event": "plugin_error",
                        "plugin": plugin_id,
                        "pipeline": pipeline_name,
                        "hook": hook,
                        "error": str(e)
                    })



def execute_plugin_for_pipeline_with_context(
    plugin_id: str,
    pipeline_name: str,
    hook: str,
    pipelines: Dict[str, Any],
    plugin_loader: Any,
    plugin_executor: Any,
    logger: Any,
    context: dict,
    config: dict
) -> dict:
    """
    Helper to load, execute a plugin for a pipeline/hook, and allow context mutation.
    Passes the cumulative context and plugin-specific config to the plugin. If the plugin returns an updated context, it is used for the next plugin.
    """
    plugin_mod = plugin_loader.load(plugin_id)
    pdata = pipelines[pipeline_name]
    command = pdata.get('command')
    context['command'] = command if command is not None else None
    # Run plugin
    result = plugin_executor.execute(plugin_mod.run, context, config, pipeline_name)
    # If plugin returns an updated context, use it
    if isinstance(result, dict) and 'context' in result and isinstance(result['context'], dict):
        logger.info({
            "event": "plugin_context_update",
            "plugin": plugin_id,
            "pipeline": pipeline_name,
            "hook": hook,
            "updated_keys": list(result['context'].keys())
        })
        return result['context']
    logger.info({"event": "plugin_run", "plugin": plugin_id, "pipeline": pipeline_name, "hook": hook})
    return context
