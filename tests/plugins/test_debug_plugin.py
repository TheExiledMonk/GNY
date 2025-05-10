"""
Unit tests for debug_plugin.
"""
import os
import tempfile
import shutil
from plugins.debug_plugin import run, status

def test_run_logs_to_file(monkeypatch):
    # Setup temp log file
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        context = {"foo": 1}
        config = {"bar": 2}
        pipeline = "testpipe"
        result = run(context, config, pipeline)
        assert result["status"] == "logged"
        with open(log_path) as f:
            content = f.read()
        assert "foo" in content and "bar" in content and "testpipe" in content

def test_status_reads_log(monkeypatch):
    # Setup temp log file
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "debug_plugins.log")
        monkeypatch.setattr("plugins.debug_plugin.LOG_PATH", log_path)
        with open(log_path, "w") as f:
            f.write("hello\nworld\n")
        out = status()
        assert "hello" in out and "world" in out
