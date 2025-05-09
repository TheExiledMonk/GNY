"""
Tests for core.orchestrator pipeline execution and error handling.
"""
import pytest
from core.orchestrator import Orchestrator
from core.thread_manager import ThreadManager

def test_orchestrator_thread_start(monkeypatch):
    orch = Orchestrator()
    started = {}
    def fake_start_pipeline_thread(name, fn, *args):
        started[name] = True
    monkeypatch.setattr(orch.thread_manager, "start_pipeline_thread", fake_start_pipeline_thread)
    orch.run()
    assert started

def test_orchestrator_plugin_error(monkeypatch):
    orch = Orchestrator()
    def fake_run_pipeline(name):
        raise Exception("fail")
    monkeypatch.setattr(orch, "_run_pipeline", fake_run_pipeline)
    # Should not raise
    orch.run()
