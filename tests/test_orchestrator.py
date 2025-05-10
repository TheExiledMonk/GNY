"""
Unit test for Orchestrator pipeline/thread startup.
"""
from core.orchestrator import Orchestrator

def test_orchestrator_runs(monkeypatch):
    orch = Orchestrator()
    called = {}
    def fake_run_pipeline(pipeline_name):
        called[pipeline_name] = True
    monkeypatch.setattr(orch, "_run_pipeline", fake_run_pipeline)
    orch.run()
    assert called

def test_run_pipeline_plugin_error(monkeypatch):
    orch = Orchestrator()
    orch.pipelines = {"pipe": {"hooks": ["h1"]}}
    orch.hook_registry = type("HR", (), {"get_plugins": lambda self, h: ["p1"]})()
    # Plugin whose run raises
    class FakePlugin:
        def run(self, *a, **kw):
            raise ValueError("failtest")
    orch.plugin_loader = type("PL", (), {"load": lambda self, pid: FakePlugin()})()
    orch.config_manager = type("CM", (), {"get_plugin_config": lambda self, pid, p: {}})()
    orch.plugin_executor = type("PE", (), {"execute": lambda self, fn, ctx, cfg: fn()})()
    errors = {}
    class FakeLogger:
        def info(self, data): pass
        def error(self, data): errors.update(data)
    orch.logger = FakeLogger()
    orch._run_pipeline("pipe")
    assert errors["event"] == "plugin_error"
    assert errors["plugin"] == "p1"
    assert errors["pipeline"] == "pipe"
    assert errors["hook"] == "h1"
    assert "failtest" in errors["error"]
