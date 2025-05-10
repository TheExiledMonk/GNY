"""
Unit tests for debug_plugin.
Covers: context/config logging, gather_plugin_config handling, and log structure.
"""
import os
import tempfile
import json
import pytest
import sys
import types
import io
import builtins
from plugins.debug_plugin import run, log_entry, status, get_status


def read_last_log(log_path):
    with open(log_path) as f:
        lines = f.readlines()
    return json.loads(lines[-1])

def test_debug_plugin_logs_context_and_config(monkeypatch):
    """
    Test that debug_plugin logs context and config fields to the log file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        context = {"foo": 1}
        config = {"bar": 2}
        pipeline = "testpipe"
        result = run(context, config, pipeline)
        assert result["status"] == "logged"
        entry = read_last_log(log_path)
        assert entry["context"]["foo"] == 1
        assert entry["config"]["bar"] == 2
        assert entry["pipeline"] == "testpipe"
        assert entry["event"] == "debug_plugin_probe"

def test_debug_plugin_logs_gather_plugin_config(monkeypatch):
    """
    Test that gather_plugin_config in context is logged, but not duplicated at top level.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        context = {"gather_plugin_config": {"baz": 123}}
        config = {}
        pipeline = "testpipe"
        result = run(context, config, pipeline)
        assert result["status"] == "logged"
        entry = read_last_log(log_path)
        assert "gather_plugin_config" in entry["context"]
        assert entry["context"]["gather_plugin_config"]["baz"] == 123
        # Should not be duplicated at top-level
        assert "gather_plugin_config" not in entry or entry["gather_plugin_config"] != 123

def test_debug_plugin_context_mutation(monkeypatch):
    """
    Test that debug_plugin adds debug_plugin_visited and debug_plugin_timestamp to context.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        context = {"foo": 1}
        config = {}
        pipeline = "testpipe"
        result = run(context, config, pipeline)
        assert result["status"] == "logged"
        entry = read_last_log(log_path)
        assert entry["context"]["debug_plugin_visited"] is True
        assert "debug_plugin_timestamp" in entry["context"]

def test_debug_plugin_run_with_step_variants(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        # step in context
        context = {"step": "a"}
        config = {}
        pipeline = "p"
        run(context, config, pipeline)
        entry = read_last_log(log_path)
        assert entry["pipeline_step"] == "a"
        # step in config
        context = {}
        config = {"step": "b"}
        run(context, config, pipeline)
        entry = read_last_log(log_path)
        assert entry["pipeline_step"] == "b"
        # pipeline_step in context
        context = {"pipeline_step": "c"}
        config = {}
        run(context, config, pipeline)
        entry = read_last_log(log_path)
        assert entry["pipeline_step"] == "c"
        # pipeline_step in config
        context = {}
        config = {"pipeline_step": "d"}
        run(context, config, pipeline)
        entry = read_last_log(log_path)
        assert entry["pipeline_step"] == "d"

def test_debug_plugin_status_no_log(monkeypatch):
    import plugins.debug_plugin
    monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", "/tmp/nonexistent_debug_plugins.log")
    assert "No debug logs found." in status()

def test_debug_plugin_status_with_log(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("line1\nline2\n")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        out = status()
        assert "line1" in out and "line2" in out

def test_debug_plugin_status_error(monkeypatch):
    # Patch open to raise error
    import plugins.debug_plugin
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("builtins.open", lambda *a, **kw: (_ for _ in ()).throw(IOError("fail")))
    out = status()
    assert "[ERROR] Could not read debug log" in out

def test_debug_plugin_status_view_patch(monkeypatch):
    import plugins.debug_plugin
    def fake_view(req):
        return "ok"
    monkeypatch.setattr("plugins.debug_plugin.debug_plugin_status_view", fake_view)
    assert plugins.debug_plugin.debug_plugin_status_view(None) == "ok"
