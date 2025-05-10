"""
Unit tests for core.error_handler
"""
from core.error_handler import ErrorHandler

def test_error_handler_logs(monkeypatch):
    handler = ErrorHandler()
    called = {}
    def fake_error(data):
        called['logged'] = data
    monkeypatch.setattr(handler.logger, 'error', fake_error)
    handler.handle(Exception('fail'), context={"foo": "bar"})
    assert 'logged' in called
