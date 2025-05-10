"""
Unit tests for core.plugin_executor: plugin execution, error handling.
"""
import pytest
from types import SimpleNamespace

@pytest.fixture
def plugin_executor():
    from core.plugin_executor import PluginExecutor
    return PluginExecutor()

def test_execute_success(plugin_executor):
    result = {}
    def fn(context, config, pipeline):
        result['called'] = True
        return {'context': context, 'config': config, 'pipeline': pipeline}
    context = {'foo': 1}
    config = {'bar': 2}
    pipeline = 'testpipe'
    out = plugin_executor.execute(fn, context, config, pipeline)
    assert result['called']
    assert out['context'] == context
    assert out['config'] == config
    assert out['pipeline'] == pipeline

def test_execute_exception(plugin_executor):
    def fn(context, config, pipeline):
        raise RuntimeError('fail')
    with pytest.raises(RuntimeError):
        plugin_executor.execute(fn, {}, {}, 'p')
