from db.plugin_config_repo import PluginConfigRepo

def test_get_plugin_config_none():
    class FakeStorage:
        def get(self, col, query): return []
    repo = PluginConfigRepo(FakeStorage())
    assert repo.get_plugin_config("pid", "pipe") is None

def test_update_plugin_config_calls_storage():
    called = {}
    class FakeStorage:
        def update(self, col, query, config): called.update(locals())
    repo = PluginConfigRepo(FakeStorage())
    repo.update_plugin_config("pid", "pipe", {"x": 1})
    assert called["col"] == "plugin_configs"
    assert called["query"] == {"plugin_id": "pid", "pipeline": "pipe"}
    assert called["config"] == {"x": 1}

def test_insert_plugin_config_calls_storage():
    called = {}
    class FakeStorage:
        def insert(self, col, doc): called.update(locals())
    repo = PluginConfigRepo(FakeStorage())
    repo.insert_plugin_config("pid", "pipe", {"foo": 2})
    assert called["col"] == "plugin_configs"
    assert called["doc"]["plugin_id"] == "pid"
    assert called["doc"]["pipeline"] == "pipe"
    assert called["doc"]["foo"] == 2
