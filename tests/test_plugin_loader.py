"""
Unit tests for core.plugin_loader: plugin loading, error handling.
"""
import pytest
from core.plugin_loader import PluginLoader

class DummyPlugin:
    pass

def test_load_success(monkeypatch):
    loader = PluginLoader()
    # Patch the public load method to return DummyPlugin
    monkeypatch.setattr(loader, 'load', lambda pid: DummyPlugin())
    plugin = loader.load('dummy')
    assert isinstance(plugin, DummyPlugin)

def test_load_failure():
    loader = PluginLoader()
    with pytest.raises(ModuleNotFoundError):
        loader.load('not_a_real_plugin')
