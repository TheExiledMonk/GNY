"""
Unit test for sample_plugin.
"""
import types
from plugins import sample_plugin

def test_sample_plugin_run():
    context = {
        "services": {
            "log": type("FakeLogger", (), {"info": lambda self, data: None})(),
        }
    }
    config = {"foo": "bar"}
    result = sample_plugin.run(context, config)
    assert result["status"] == "success"
