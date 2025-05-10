"""
Unit tests for db.plugin_config_repo: config fetch/insert/delete, edge cases.
"""
import pytest
from db.plugin_config_repo import PluginConfigRepo

class DummyStorage:
    def __init__(self):
        self.data = []
        self.last_update = None
        self.last_insert = None
    def get(self, collection, query=None, db_name=None):
        # Simulate $or for pipeline=None
        if query and "$or" in query:
            return [d for d in self.data if d.get("plugin_id") == query["plugin_id"] and (d.get("pipeline") is None or "pipeline" not in d)]
        return [d for d in self.data if all(d.get(k) == v for k, v in (query or {}).items())]
    def insert(self, collection, doc, db_name=None):
        self.last_insert = (collection, doc, db_name)
        self.data.append(doc)
    def delete(self, collection, query, db_name=None):
        self.data = [d for d in self.data if not all(d.get(k) == v for k, v in query.items())]
    def update(self, collection, query, doc, upsert=False, db_name=None):
        self.last_update = (collection, query, doc, upsert, db_name)
        found = False
        for i, d in enumerate(self.data):
            if all(d.get(k) == v for k, v in query.items()):
                self.data[i] = doc
                found = True
        if upsert and not found:
            self.data.append(doc)

@pytest.fixture
def plugin_repo():
    return PluginConfigRepo(DummyStorage())

def test_get_plugin_config_none(plugin_repo):
    assert plugin_repo.get_plugin_config('pid', 'pipe') is None

def test_insert_and_get_plugin_config(plugin_repo):
    plugin_repo.insert_plugin_config('p', 'x', {'foo': 1})
    res = plugin_repo.get_plugin_config('p', 'x')
    assert res['foo'] == 1

def test_get_plugin_config_global(plugin_repo):
    # Insert global config (pipeline=None)
    plugin_repo._storage.data.append({'plugin_id': 'g', 'pipeline': None, 'bar': 2})
    plugin_repo._storage.data.append({'plugin_id': 'g'})  # missing pipeline field
    res = plugin_repo.get_plugin_config('g', None)
    assert res['bar'] == 2 or res['plugin_id'] == 'g'

def test_update_plugin_config_upsert_and_update(plugin_repo):
    # Upsert: should insert if not found
    plugin_repo.update_plugin_config('pid', 'pipe', {'a': 1})
    found = plugin_repo.get_plugin_config('pid', 'pipe')
    assert found['a'] == 1 and found['plugin_id'] == 'pid' and found['pipeline'] == 'pipe'
    # Update: should update if found
    plugin_repo.update_plugin_config('pid', 'pipe', {'a': 2})
    found2 = plugin_repo.get_plugin_config('pid', 'pipe')
    assert found2['a'] == 2
    # Check upsert flag and doc
    last = plugin_repo._storage.last_update
    assert last[3] is True and last[2]['plugin_id'] == 'pid' and last[2]['pipeline'] == 'pipe'

def test_delete_plugin_config(plugin_repo):
    plugin_repo.insert_plugin_config('del', 'p', {'x': 1})
    assert plugin_repo.get_plugin_config('del', 'p') is not None
    plugin_repo.delete_plugin_config('del', 'p')
    assert plugin_repo.get_plugin_config('del', 'p') is None

def test_insert_plugin_config_merges(plugin_repo):
    plugin_repo.insert_plugin_config('merge', 'pipe', {'foo': 7, 'bar': 8})
    found = plugin_repo.get_plugin_config('merge', 'pipe')
    assert found['foo'] == 7 and found['bar'] == 8 and found['plugin_id'] == 'merge' and found['pipeline'] == 'pipe'

def test_delete_plugin_config(plugin_repo):
    plugin_repo.insert_plugin_config('p', 'x', {'foo': 1})
    plugin_repo.delete_plugin_config('p', 'x')
    assert plugin_repo.get_plugin_config('p', 'x') is None

def test_get_plugin_config_pipeline_none_found(plugin_repo):
    # Insert with pipeline=None
    plugin_repo.insert_plugin_config('p', None, {'bar': 2})
    res = plugin_repo.get_plugin_config('p', None)
    assert res['bar'] == 2

def test_get_plugin_config_pipeline_none_not_found(plugin_repo):
    assert plugin_repo.get_plugin_config('notfound', None) is None

def test_update_plugin_config_upsert_and_doc(plugin_repo):
    repo = plugin_repo
    repo.update_plugin_config('p', 'y', {'baz': 3})
    res = repo.get_plugin_config('p', 'y')
    assert res['baz'] == 3
    assert res['plugin_id'] == 'p'
    assert res['pipeline'] == 'y'

def test_insert_plugin_config_extra_fields_and_dbname():
    storage = DummyStorage()
    repo = PluginConfigRepo(storage)
    repo.insert_plugin_config('p', 'z', {'foo': 9, 'bar': 10}, db_name='testdb')
    assert storage.last_insert[2] == 'testdb'
    assert {'plugin_id': 'p', 'pipeline': 'z', 'foo': 9, 'bar': 10} in storage.data

def test_update_plugin_config_dbname():
    storage = DummyStorage()
    repo = PluginConfigRepo(storage)
    repo.update_plugin_config('p', 'z', {'foo': 9}, db_name='db1')
    assert storage.last_update[4] == 'db1'
