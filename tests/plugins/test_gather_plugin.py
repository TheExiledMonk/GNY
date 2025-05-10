"""
Unit tests for gather_plugin.
Covers: config serialization, removal of _id, and pipeline_config structure.
"""
import pytest
import sys
import importlib

def test_gather_plugin_fallback_objectid(monkeypatch):
    # Remove bson from sys.modules and patch import to raise ImportError for bson
    import builtins
    orig_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == 'bson':
            raise ImportError('forced')
        return orig_import(name, *args, **kwargs)
    builtins.__import__, old = fake_import, builtins.__import__
    try:
        import plugins.gather_plugin
        importlib.reload(plugins.gather_plugin)
        # Should define fallback ObjectId
        assert hasattr(plugins.gather_plugin, 'ObjectId')
    finally:
        builtins.__import__ = old

from plugins.gather_plugin import run

def test_gather_plugin_removes_id_and_serializes(monkeypatch):
    class DummyLog:
        def __init__(self): self.events = []
        def info(self, d): self.events.append(d)
    context = {'services': {'log': DummyLog()}}
    config = {'_id': 'fakeid', 'intervals': ['1m', '5m'], 'base_stablecoin': 'USDT', 'exchanges': ['binance'], 'stablecoins': [], 'tokens': [], 'exchange_tokenpairs': None, 'exchange_database': None, 'indicator_database': None, 'plugin_id': 'pid', 'pipeline': 'pipe'}
    result = run(context, config, 'pipe')
    assert '_id' not in result['pipeline_config']
    assert 'intervals' in result['pipeline_config']
    assert result['status'] == 'success'
    # Should emit config as JSON
    assert any('gather_plugin_config_raw' in e.get('event','') for e in context['services']['log'].events)

def test_gather_plugin_intervals_dict():
    class DummyLog:
        def info(self, d): pass
    context = {'services': {'log': DummyLog()}}
    config = {'intervals': {'1m': True, '5m': True}, 'base_stablecoin': 'USDT'}
    result = run(context, config, 'pipe')
    assert result['pipeline_config']['intervals'] == {'1m': True, '5m': True}

def test_gather_plugin_intervals_str():
    class DummyLog:
        def info(self, d): pass
    context = {'services': {'log': DummyLog()}}
    config = {'intervals': '1m,5m, 15m', 'base_stablecoin': 'USDT'}
    result = run(context, config, 'pipe')
    assert result['pipeline_config']['intervals'] == {'1m': True, '5m': True, '15m': True}

def test_gather_plugin_intervals_missing():
    class DummyLog:
        def info(self, d): pass
    context = {'services': {'log': DummyLog()}}
    config = {'base_stablecoin': 'USDT'}
    result = run(context, config, 'pipe')
    assert 'intervals' not in result['pipeline_config']

def test_gather_plugin_intervals_unrecognized_type():
    class DummyLog:
        def info(self, d): pass
    context = {'services': {'log': DummyLog()}}
    config = {'intervals': 123, 'base_stablecoin': 'USDT'}
    result = run(context, config, 'pipe')
    assert 'intervals' not in result['pipeline_config']

def test_gather_plugin_safe_json_exception(monkeypatch):
    # Patch json.dumps to raise
    class DummyLog:
        def __init__(self): self.events = []
        def info(self, d): self.events.append(d)
    context = {'services': {'log': DummyLog()}}
    config = {'foo': object()}
    import plugins.gather_plugin
    monkeypatch.setattr('json.dumps', lambda *a, **kw: (_ for _ in ()).throw(TypeError('fail')))
    result = run(context, config, 'pipe')
    # Should fallback to str(obj) in config_json
    assert any(isinstance(e.get('config_json'), str) for e in context['services']['log'].events if 'gather_plugin_config_raw' in e.get('event',''))

def test_gather_plugin_minimal_config():
    class DummyLog:
        def info(self, d): pass
    context = {'services': {'log': DummyLog()}}
    config = {}
    result = run(context, config, 'pipe')
    # Should not fail, pipeline_config should have only keys with None or []
    assert result['status'] == 'success'
    assert isinstance(result['pipeline_config'], dict)

def test_gather_plugin_context_not_mutated():
    class DummyLog:
        def info(self, d): pass
    context = {'services': {'log': DummyLog()}, 'foo': 1}
    config = {'base_stablecoin': 'USDT'}
    orig = dict(context)
    run(context, config, 'pipe')
    assert context == orig

def test_gather_plugin_full_config_fields():
    context = {"services": {"log": type("L", (), {"info": lambda self, d: None})()}}
    config = {
        "base_stablecoin": "USDT",
        "exchanges": ["binance"],
        "stablecoins": ["USDT"],
        "tokens": ["BTC"],
        "exchange_tokenpairs": {"binance": ["BTC/USDT"]},
        "exchange_database": "API_exchanges",
        "indicator_database": "API_indicators",
        "plugin_id": "gather_plugin",
        "pipeline": None,
        "intervals": ["1h"]
    }
    pipeline = "testpipe"
    result = run(context, config, pipeline)
    pcfg = result["pipeline_config"]
    for k in ["base_stablecoin", "exchanges", "stablecoins", "tokens", "exchange_tokenpairs", "exchange_database", "indicator_database", "plugin_id", "pipeline"]:
        assert k in pcfg
    assert isinstance(pcfg.get("intervals"), dict) or pcfg.get("intervals") is None
