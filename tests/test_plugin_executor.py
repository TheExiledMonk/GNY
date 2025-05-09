"""
Unit tests for core.plugin_executor
"""
from core.plugin_executor import PluginExecutor
import pytest

def test_execute_success():
    def plugin(context, config):
        return 'ok'
    ex = PluginExecutor()
    result = ex.execute(plugin, {}, {})
    assert result == 'ok'

def test_execute_error():
    def plugin(context, config):
        raise ValueError('fail')
    ex = PluginExecutor()
    with pytest.raises(ValueError):
        ex.execute(plugin, {}, {})
