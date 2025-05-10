"""
Unit tests for orchestrator: config/context propagation, plugin execution, error handling.
"""
import pytest
from types import SimpleNamespace

class DummyPlugin:
    def __init__(self):
        self.contexts = []
    def run(self, context, config, pipeline):
        self.contexts.append((context.copy(), config.copy()))
        context = dict(context)
        context['dummy_marker'] = True
        return {'context': context}

def test_pipeline_config_propagation(monkeypatch):
    """
    End-to-end: orchestrator passes config/context, plugins mutate context, gather_plugin_config flows through.
    """
    from core.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.pipelines = {'testpipe': {'hooks': ['gather', 'debug']}}
    orch.hook_registry = SimpleNamespace(get_plugins=lambda h: [h + '_plugin'])
    dummy_gather = DummyPlugin()
    dummy_debug = DummyPlugin()
    orch.plugin_loader = SimpleNamespace(load=lambda pid: dummy_gather if 'gather' in pid else dummy_debug)
    orch.config_manager = SimpleNamespace(get_plugin_config=lambda pid, p: {'foo': 'bar', 'exchange_tokenpairs': {'binance': ['BTC/USDT']}})
    orch.plugin_executor = SimpleNamespace(execute=lambda fn, ctx, cfg, pl: fn(ctx, cfg, pl))
    orch.logger = SimpleNamespace(info=lambda d: None, error=lambda d: None)
    orch._run_pipeline('testpipe')
    # gather_plugin should get config with exchange_tokenpairs
    gather_ctx, gather_cfg = dummy_gather.contexts[0]
    assert 'foo' in gather_cfg and 'exchange_tokenpairs' in gather_cfg
    # debug_plugin should see mutated context
    debug_ctx, debug_cfg = dummy_debug.contexts[0]
    assert 'dummy_marker' in debug_ctx
    # gather_plugin_config should flow through if set by gather
    dummy_gather.contexts = []
    dummy_debug.contexts = []
    def gather_run(context, config, pipeline):
        context = dict(context)
        context['gather_plugin_config'] = {'baz': 123}
        return {'context': context}
    orch.plugin_loader = SimpleNamespace(load=lambda pid: SimpleNamespace(run=gather_run if "gather" in pid else dummy_debug.run))
    orch._run_pipeline('testpipe')
    debug_ctx, _ = dummy_debug.contexts[0]
    assert 'gather_plugin_config' in debug_ctx and debug_ctx['gather_plugin_config']['baz'] == 123

def test_plugin_error_handling(monkeypatch):
    """
    Test that orchestrator logs plugin errors with correct context.
    """
    from core.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.pipelines = {'pipe': {'hooks': ['h1']}}
    orch.hook_registry = SimpleNamespace(get_plugins=lambda h: ['p1'])
    class FakePlugin:
        def run(self, *a, **kw):
            raise ValueError("failtest")
    orch.plugin_loader = SimpleNamespace(load=lambda pid: FakePlugin())
    orch.config_manager = SimpleNamespace(get_plugin_config=lambda pid, p: {})
    orch.plugin_executor = SimpleNamespace(execute=lambda fn, ctx, cfg, pl: fn())
    errors = {}
    class FakeLogger:
        def info(self, data):
            pass
        def error(self, data):
            errors.update(data)
    orch.logger = FakeLogger()
    orch._run_pipeline('pipe')
    assert errors['event'] == 'plugin_error'
    assert errors['plugin'] == 'p1'
    assert errors['pipeline'] == 'pipe'
    assert errors['hook'] == 'h1'
    assert 'failtest' in errors['error']
