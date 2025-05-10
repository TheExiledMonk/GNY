"""
Unit test for ConfigManager.
"""

from services.config_manager import ConfigManager


def test_config_manager_global():
    class FakeStorage:
        def get(self, col, query=None):
            if col == "system_config":
                return [{"sys": 1}]

    cm = ConfigManager(storage=FakeStorage())
    config = cm.get_global_config()
    assert config == {"sys": 1}


def test_config_manager_pipeline():
    class FakeStorage:
        def get(self, col, query=None):
            if col == "pipeline_configs":
                return [{"name": "foo", "val": 2}]

    cm = ConfigManager(storage=FakeStorage())
    config = cm.get_pipeline_config("foo")
    assert config == {"name": "foo", "val": 2}


def test_config_manager_plugin():
    class FakeRepo:
        def get_plugin_config(self, pid, pipe):
            return {"plugin": pid, "pipe": pipe}

        def update_plugin_config(self, pid, pipe, cfg):
            self.last = (pid, pipe, cfg)

    class FakeStorage:
        pass

    cm = ConfigManager(storage=FakeStorage())
    cm._plugin_repo = FakeRepo()
    cfg = cm.get_plugin_config("p1", "pipe1")
    assert cfg == {"plugin": "p1", "pipe": "pipe1"}
    cm.update_plugin_config("p2", "pipe2", {"x": 5})
    assert cm._plugin_repo.last == ("p2", "pipe2", {"x": 5})
