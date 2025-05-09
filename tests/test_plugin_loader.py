"""
Tests for core.plugin_loader
"""
import pytest
from core.plugin_loader import PluginLoader

def test_plugin_loader_import_error():
    loader = PluginLoader()
    with pytest.raises(ModuleNotFoundError):
        loader.load("nonexistent_plugin")
