"""
Unit tests for framework_check_plugin.
"""

import pytest

from plugins.framework_check_plugin import run


def test_framework_check_plugin_basic():
    context = {}
    config = {}
    pipeline = "test_pipeline"
    result = run(context, config, pipeline)
    assert result["status"] == "checked"
    assert "framework_check" in result
    fc = result["framework_check"]
    assert "core" in fc and "plugins" in fc
    # Check that at least orchestrator and debug_plugin are present and imported
    assert fc["core"]["core.orchestrator"]["import"] is True
    assert fc["plugins"]["plugins.debug_plugin.__init__"]["import"] is True
    # Should add to context as well
    assert "framework_check" in result["context"]
