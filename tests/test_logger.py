"""
Unit tests for services.logger UnifiedLogger
"""
import os
import json
import tempfile
import shutil
import logging
import types
import pytest
from services.logger import UnifiedLogger

def test_info_logs_to_file(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr("services.logger.LOG_DIR", temp_dir)
    monkeypatch.setattr("services.logger.LOG_FILE", os.path.join(temp_dir, "orchestrator.log"))
    logger = UnifiedLogger()
    data = {"msg": "hello", "val": 42}
    logger.info(data)
    logger.logger.handlers[0].flush()
    with open(os.path.join(temp_dir, "orchestrator.log")) as f:
        log_content = f.read()
    assert json.dumps(data) in log_content
    shutil.rmtree(temp_dir)

def test_error_sends_slack(monkeypatch):
    sent = {}
    import services.logger
    monkeypatch.setattr(services.logger, "SLACK_WEBHOOK", "http://fake")
    import requests
    monkeypatch.setattr(requests, "post", lambda url, json=None: sent.update({"url": url, "json": json}) or type("Resp", (), {"status_code": 200})())
    logger = UnifiedLogger()
    logger._send_slack({"err": "fail"}, level="ERROR")
    assert sent["url"] == "http://fake"
    assert "[ERROR]" in sent["json"]["text"]

def test_fatal_logs_and_slack(monkeypatch):
    sent = {}
    import services.logger
    monkeypatch.setattr(services.logger, "SLACK_WEBHOOK", "http://fake")
    import requests
    monkeypatch.setattr(requests, "post", lambda url, json=None: sent.update({"url": url, "json": json}) or type("Resp", (), {"status_code": 200})())
    logger = UnifiedLogger()
    logger.fatal({"fatal": True})
    assert sent["url"] == "http://fake"
    assert "[FATAL]" in sent["json"]["text"]
