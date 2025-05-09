"""
Tests for db.config_storage
"""
from db.config_storage import ConfigStorage
import pytest

def test_config_storage_sync():
    class FakeColl:
        def find(self, q=None):
            return [{"bar": 1}]
    storage = ConfigStorage()
    storage._get_collection = lambda name: FakeColl()
    storage._cache = {"foo": [{"bar": 1}]}
    res = storage.get("foo")
    assert isinstance(res, list)

def test_config_storage_insert():
    called = {}
    class FakeColl:
        def insert_one(self, doc):
            called["insert"] = doc
            class Result:
                inserted_id = "mockid"
            return Result()
    storage = ConfigStorage()
    storage._get_collection = lambda name: FakeColl()
    result = storage.insert("foo", {"bar": 2})
    assert called.get("insert") == {"bar": 2}
    assert result == "mockid"

def test_config_storage_insert_upsert():
    called = {}
    class FakeColl:
        def replace_one(self, query, doc, upsert):
            called["replace"] = (query, doc, upsert)
            class Result:
                upserted_id = "upsertid"
            return Result()
    storage = ConfigStorage()
    storage._get_collection = lambda name: FakeColl()
    doc = {"_id": 123, "bar": 3}
    result = storage.insert("foo", doc, upsert=True)
    assert called["replace"] == ({"_id": 123}, doc, True)
    assert result == "upsertid"

def test_config_storage_update():
    called = {}
    class FakeColl:
        def update_many(self, query, update, upsert=False):
            called["update"] = (query, update, upsert)
            class Result:
                modified_count = 2
            return Result()
    storage = ConfigStorage()
    storage._get_collection = lambda name: FakeColl()
    result = storage.update("foo", {"x": 1}, {"bar": 4})
    assert called["update"] == ({"x": 1}, {"$set": {"bar": 4}}, False)
    assert result == 2

def test_config_storage_update_upsert():
    called = {}
    class FakeColl:
        def update_many(self, query, update, upsert=False):
            called["update"] = (query, update, upsert)
            class Result:
                modified_count = 1
            return Result()
    storage = ConfigStorage()
    storage._get_collection = lambda name: FakeColl()
    result = storage.update("foo", {"x": 2}, {"bar": 5}, upsert=True)
    assert called["update"] == ({"x": 2}, {"$set": {"bar": 5}}, True)
    assert result == 1

def test_config_storage_delete():
    called = {}
    class FakeColl:
        def delete_many(self, query):
            called["delete"] = query
            class Result:
                deleted_count = 3
            return Result()
    storage = ConfigStorage()
    storage._get_collection = lambda name: FakeColl()
    result = storage.delete("foo", {"bar": 6})
    assert called["delete"] == {"bar": 6}
    assert result == 3
