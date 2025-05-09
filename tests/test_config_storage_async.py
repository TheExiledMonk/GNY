"""
Async tests for db.config_storage async methods and worker queue.
"""
import pytest
from db.config_storage import ConfigStorage

class FastAsyncConfigStorage(ConfigStorage):
    def __init__(self):
        pass  # Don't start thread or queue
    async def async_get(self, collection, query=None):
        return self.get(collection, query)
    async def async_insert(self, collection, document):
        return self.insert(collection, document)
    async def async_update(self, collection, query, update):
        return self.update(collection, query, update)
    async def async_delete(self, collection, query):
        return self.delete(collection, query)

@pytest.mark.asyncio
async def test_async_get():
    called = {}
    class Dummy(FastAsyncConfigStorage):
        def get(self, collection, query=None):
            called["get"] = (collection, query)
            return [42]
    store = Dummy()
    res = await store.async_get("foo", {"bar": 1})
    assert res == [42]
    assert called["get"] == ("foo", {"bar": 1})

@pytest.mark.asyncio
async def test_async_insert():
    called = {}
    class Dummy(FastAsyncConfigStorage):
        def insert(self, collection, doc, upsert=False):
            called["insert"] = (collection, doc, upsert)
            return "id"
    store = Dummy()
    res = await store.async_insert("foo", {"x": 1})
    assert res == "id"
    assert called["insert"] == ("foo", {"x": 1}, False)

@pytest.mark.asyncio
async def test_async_update():
    called = {}
    class Dummy(FastAsyncConfigStorage):
        def update(self, collection, query, update, upsert=False):
            called["update"] = (collection, query, update, upsert)
            return 3
    store = Dummy()
    res = await store.async_update("foo", {"a": 1}, {"b": 2})
    assert res == 3
    assert called["update"] == ("foo", {"a": 1}, {"b": 2}, False)

@pytest.mark.asyncio
async def test_async_delete():
    called = {}
    class Dummy(FastAsyncConfigStorage):
        def delete(self, collection, query):
            called["delete"] = (collection, query)
            return 9
    store = Dummy()
    res = await store.async_delete("foo", {"y": 7})
    assert res == 9
    assert called["delete"] == ("foo", {"y": 7})
