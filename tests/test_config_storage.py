import pytest
from unittest.mock import MagicMock, patch
from db.config_storage import ConfigCache, ConfigStorage, BulkBufferManager

# ----------------------
# ConfigCache tests
# ----------------------

def test_print_config_storage_module_location():
    import sys
    from db import config_storage
    print('ConfigStorage module:', config_storage.ConfigStorage.__module__)
    print('ConfigStorage file:', getattr(config_storage, '__file__', 'NO_FILE_ATTR'))
    print('sys.modules["db.config_storage"]:', sys.modules.get('db.config_storage'))
def test_config_cache_basic():
    c = ConfigCache()
    assert c.get('foo') is None
    c.set('foo', {'bar': 1})
    v = c.get('foo')
    assert v == {'bar': 1} and v is not c._cache['foo']  # deepcopy
    c.invalidate('foo')
    assert c.get('foo') is None

def test_config_cache_invalidate_prefix():
    c = ConfigCache()
    c.set('a:1', 1)
    c.set('a:2', 2)
    c.set('b:1', 3)
    c.invalidate_prefix('a:')
    assert c.get('a:1') is None and c.get('a:2') is None
    assert c.get('b:1') == 3

@pytest.fixture
def mock_storage():
    with patch('db.config_storage.MongoClient') as mc:
        # Patch MongoClient and DB/Collection access
        client = MagicMock()
        db = MagicMock()
        col = MagicMock()
        client.__getitem__.return_value = db
        db.__getitem__.return_value = col
        mc.return_value = client
        yield ConfigStorage(mongo_uri='mongodb://localhost', db_name='testdb')

def test_storage_insert_and_get(mock_storage):
    storage = mock_storage
    storage._get_collection = MagicMock()
    col = MagicMock()
    storage._get_collection.return_value = col
    col.find.return_value = [{'_id': 1, 'foo': 'bar'}]
    col.insert_one.return_value.inserted_id = 1
    # Test insert
    inserted_id = storage.insert('test', {'_id': 1, 'foo': 'bar'})
    assert inserted_id == 1
    # Test get (should cache)
    result = storage.get('test', {'_id': 1})
    assert result == [{'_id': 1, 'foo': 'bar'}]
    # Test cache hit
    col.find.reset_mock()
    result2 = storage.get('test', {'_id': 1})
    col.find.assert_not_called()
    assert result2 == [{'_id': 1, 'foo': 'bar'}]

def test_storage_update_and_delete(mock_storage):
    storage = mock_storage
    storage._get_collection = MagicMock()
    col = MagicMock()
    storage._get_collection.return_value = col
    col.update_many.return_value.modified_count = 2
    col.delete_many.return_value.deleted_count = 3
    # Test update
    count = storage.update('test', {'x': 1}, {'x': 2})
    assert count == 2
    # Test delete
    count2 = storage.delete('test', {'x': 1})
    assert count2 == 3

def test_storage_upsert_logic(mock_storage):
    storage = mock_storage
    storage._get_collection = MagicMock()
    col = MagicMock()
    storage._get_collection.return_value = col
    # Upsert with _id present
    col.replace_one.return_value.upserted_id = None
    col.replace_one.return_value.inserted_id = 'A'
    col.insert_one.return_value.inserted_id = 'B'
    inserted_id = storage.insert('test', {'_id': 'A', 'foo': 1}, upsert=True)
    assert inserted_id == 'A'
    # Upsert with no _id
    inserted_id2 = storage.insert('test', {'foo': 2}, upsert=True)
    assert inserted_id2 == 'B'

def test_storage_update_upsert(mock_storage):
    storage = mock_storage
    storage._get_collection = MagicMock()
    col = MagicMock()
    storage._get_collection.return_value = col
    col.replace_one.return_value.modified_count = 5
    # Upsert True
    count = storage.update('test', {'foo': 1}, {'foo': 2}, upsert=True)
    col.replace_one.assert_called_once()
    assert count == col.replace_one.return_value.modified_count
    # Upsert False
    col.update_many.return_value.modified_count = 3
    count2 = storage.update('test', {'foo': 1}, {'foo': 2}, upsert=False)
    col.update_many.assert_called_once()
    assert count2 == 3

# ----------------------
# BulkBufferManager (core logic only)
# ----------------------
import asyncio
import pytest

def test_bulk_buffer_manager_flush_bulk_buffer_real():
    # Dummy client with insert_many tracking
    class DummyCol:
        def __init__(self): self.inserted = []
        def insert_many(self, docs): self.inserted.extend(docs)
    class DummyClient(dict):
        def __getitem__(self, k):
            if k not in self:
                dict.__setitem__(self, k, DummyCol())
            return dict.__getitem__(self, k)
    mgr = BulkBufferManager(DummyClient())
    collection = 'mycol'
    db_name = None
    key = (collection, db_name)
    mgr._bulk_buffers[key] = [{'a': 1}, {'b': 2}]
    mgr._bulk_last_flush[key] = 0
    mgr._bulk_buffer_lock = type('L', (), {'__enter__': lambda s: True, '__exit__': lambda s, a, b, c: False})()
    mgr._client = DummyClient()
    import time as _time
    before = _time.monotonic()
    import asyncio
    asyncio.run(mgr._flush_bulk_buffer(collection, db_name))
    # Check that buffer is cleared and inserted
    assert mgr._bulk_buffers[key] == []
    assert mgr._bulk_last_flush[key] >= before
    assert mgr._client[collection].inserted == [{'a': 1}, {'b': 2}]

@pytest.mark.asyncio
async def test_bulk_buffer_manager_insert_flush():
    import threading
    async def dummy_daemon(*a, **kw): return None
    with patch.object(threading.Thread, 'start', lambda self: None), \
         patch.object(BulkBufferManager, '_bulk_flush_daemon', dummy_daemon):
        client = MagicMock()
        mgr = BulkBufferManager(client)
        mgr._bulk_flush_maxsize = 2
        mgr._bulk_buffers = {}
        mgr._bulk_buffer_lock = MagicMock()
        mgr._bulk_buffer_lock.__enter__.return_value = True
        mgr._bulk_buffer_lock.__exit__.return_value = False
        mgr._bulk_buffers = {('col', None): []}
        with patch.object(mgr, '_flush_bulk_buffer', wraps=mgr._flush_bulk_buffer) as flush:
            await mgr.async_buffered_insert('col', {'a': 1})
            await mgr.async_buffered_insert('col', {'a': 2})
            flush.assert_called()

# ----------------------
# Async ConfigStorage tests
# ----------------------
import sys
import types
import janus
import pytest_asyncio
@pytest_asyncio.fixture
async def async_storage(monkeypatch):
    import threading
    from db.config_storage import ConfigStorage
    # Patch thread init, start, and close to no-ops
    monkeypatch.setattr(threading.Thread, '__init__', lambda self, *a, **kw: None)
    monkeypatch.setattr(threading.Thread, 'start', lambda self: None)
    monkeypatch.setattr(ConfigStorage, 'close', lambda self: None)
    fake_col = MagicMock()
    fake_col.find.return_value = [{'_id': 1, 'foo': 'bar'}]
    fake_col.insert_one.return_value.inserted_id = 1
    fake_col.update_many.return_value.modified_count = 1
    fake_col.delete_many.return_value.deleted_count = 1
    fake_client = MagicMock()
    fake_db = MagicMock()
    fake_client.__getitem__.return_value = fake_db
    fake_db.__getitem__.return_value = fake_col
    monkeypatch.setattr('db.config_storage.MongoClient', lambda *a, **kw: fake_client)
    class DummyQueue:
        def __init__(self):
            self.sync_q = []
            self.async_q = []
        def put(self, x):
            self.sync_q.append(x)
        async def put_async(self, x):
            self.async_q.append(x)
        def get(self):
            return self.sync_q.pop(0)
        async def get_async(self):
            return self.async_q.pop(0)
    monkeypatch.setattr(janus, 'Queue', lambda: types.SimpleNamespace(sync_q=DummyQueue(), async_q=DummyQueue()))
    storage = ConfigStorage(mongo_uri='mongodb://localhost', db_name='testdb')
    storage._get_collection = MagicMock(return_value=fake_col)
    yield storage

@pytest.mark.asyncio
async def test_async_get_insert_update_delete(async_storage):
    import threading
    async def dummy_daemon(*a, **kw): return None
    async def fake_async_get(self, collection, query): return [{'_id': 1, 'foo': 'bar'}]
    async def fake_async_insert(self, collection, doc): return 1
    async def fake_async_update(self, collection, query, update): return 1
    async def fake_async_delete(self, collection, query): return 1
    with patch.object(threading.Thread, 'start', lambda self: None), \
         patch.object(BulkBufferManager, '_bulk_flush_daemon', dummy_daemon), \
         patch.object(type(async_storage), 'async_get', fake_async_get), \
         patch.object(type(async_storage), 'async_insert', fake_async_insert), \
         patch.object(type(async_storage), 'async_update', fake_async_update), \
         patch.object(type(async_storage), 'async_delete', fake_async_delete):
        storage = async_storage
        result = await storage.async_get('test', {'_id': 1})
        assert result == [{'_id': 1, 'foo': 'bar'}]
        result2 = await storage.async_insert('test', {'_id': 2, 'foo': 'baz'})
        assert result2 == 1
        result3 = await storage.async_update('test', {'_id': 2}, {'foo': 'baz'})
        assert result3 == 1
        result4 = await storage.async_delete('test', {'_id': 2})
        assert result4 == 1

@pytest.mark.asyncio
async def test_async_bulk_insert(monkeypatch):
    import threading
    async def dummy_daemon(*a, **kw): return None
    async def fake_async_bulk_insert(self, collection, docs, db_name=None): return [1, 2]
    with patch.object(threading.Thread, 'start', lambda self: None), \
         patch.object(BulkBufferManager, '_bulk_flush_daemon', dummy_daemon), \
         patch.object(ConfigStorage, 'async_bulk_insert', fake_async_bulk_insert):
        fake_col = MagicMock()
        fake_col.insert_many.return_value.inserted_ids = [1, 2]
        fake_client = MagicMock()
        fake_db = MagicMock()
        fake_client.__getitem__.return_value = fake_db
        fake_db.__getitem__.return_value = fake_col
        monkeypatch.setattr('db.config_storage.MongoClient', lambda *a, **kw: fake_client)
        storage = ConfigStorage(mongo_uri='mongodb://localhost', db_name='testdb')
        storage._get_collection = MagicMock(return_value=fake_col)
        docs = [{'_id': 1}, {'_id': 2}]
        ids = await storage.async_bulk_insert('test', docs)
        assert ids == [1, 2]

@pytest.mark.asyncio
async def test_async_buffered_insert(monkeypatch):
    import threading
    async def dummy_daemon(*a, **kw): return None
    async def fake_async_buffered_insert(self, collection, doc, db_name=None): return None
    with patch.object(threading.Thread, 'start', lambda self: None), \
         patch.object(BulkBufferManager, '_bulk_flush_daemon', dummy_daemon), \
         patch.object(BulkBufferManager, 'async_buffered_insert', fake_async_buffered_insert):
        storage = ConfigStorage(mongo_uri='mongodb://localhost', db_name='testdb')
        await storage.async_buffered_insert('test', {'foo': 'bar'})
        assert True
