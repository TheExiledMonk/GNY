"""
ConfigStorage: Threadsafe MongoDB-backed config storage with caching.
Plugins must never access the DB directly; all access is via this class.
"""
from threading import RLock, Thread
from typing import Any, Dict
from pymongo import MongoClient
import copy
import janus
import asyncio
from collections import defaultdict
import time


class ConfigCache:
    """
    Threadsafe cache for config storage.
    """
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any:
        """
        Fetch a value from the cache.
        """
        with self._lock:
            return copy.deepcopy(self._cache.get(key))

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        """
        with self._lock:
            self._cache[key] = copy.deepcopy(value)

    def invalidate(self, key: str) -> None:
        """
        Invalidate a key in the cache.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def invalidate_prefix(self, prefix: str) -> None:
        """
        Invalidate all keys with a given prefix in the cache.
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_remove:
                del self._cache[k]


class BulkBufferManager:
    """
    Manager for bulk buffer logic.
    """
    def __init__(self, client: MongoClient):
        self._client = client
        self._bulk_buffers = defaultdict(list)  # key: (collection, db_name)
        self._bulk_buffer_lock = RLock()
        self._bulk_flush_interval = 2.0  # seconds
        self._bulk_flush_maxsize = 100
        self._bulk_last_flush = defaultdict(lambda: time.monotonic())
        self._bulk_flush_task = None

    async def async_buffered_insert(self, collection: str, doc: dict, db_name: str = None) -> None:
        """
        Buffer documents for bulk insert. Flushes buffer on interval or max size.
        """
        key = (collection, db_name)
        with self._bulk_buffer_lock:
            self._bulk_buffers[key].append(doc)
            if len(self._bulk_buffers[key]) >= self._bulk_flush_maxsize:
                await self._flush_bulk_buffer(collection, db_name)
        # Timed flush is handled by background task

    async def _bulk_flush_daemon(self):
        while True:
            await asyncio.sleep(self._bulk_flush_interval)
            with self._bulk_buffer_lock:
                for (collection, db_name), buf in list(self._bulk_buffers.items()):
                    if buf and (time.monotonic() - self._bulk_last_flush[(collection, db_name)] >= self._bulk_flush_interval):
                        await self._flush_bulk_buffer(collection, db_name)

    async def _flush_bulk_buffer(self, collection: str, db_name: str = None):
        key = (collection, db_name)
        with self._bulk_buffer_lock:
            buf = self._bulk_buffers[key]
            if buf:
                col = self._client[db_name][collection] if db_name else self._client[collection]
                col.insert_many(buf)
                self._bulk_buffers[key] = []
                self._bulk_last_flush[key] = time.monotonic()


class ConfigStorage:
    """
    Threadsafe config storage and cache for system, pipeline, and plugin configs.
    Supports both sync and async DB access via janus.Queue.
    Usage:
      - Use sync methods (get/insert/update/delete) for threaded code.
      - Use async methods (async_get/async_insert/async_update/async_delete) for asyncio code.
      - Use async_bulk_insert/async_buffered_insert for efficient bulk ingestion.
    """
    def __init__(self, mongo_uri: str = None, db_name: str = None) -> None:
        """Initialize ConfigStorage with MongoDB connection, cache, and bulk buffer manager."""
        import os
        mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        db_name = db_name or os.getenv("MONGO_DB", "orchestrator")
        self._client = MongoClient(mongo_uri, connect=True)
        self._db = self._client[db_name]
        self._cache = ConfigCache()
        self._bulk_buffer_manager = BulkBufferManager(self._client)
        self._lock = RLock()
        self._queue = janus.Queue()
        self._stop_thread = False
        self._thread = Thread(target=self._worker, daemon=True)
        self._thread.start()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._bulk_buffer_manager._bulk_flush_task = loop.create_task(self._bulk_buffer_manager._bulk_flush_daemon())
        except Exception:
            pass

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while not self._stop_thread:
            try:
                req = self._queue.sync_q.get(timeout=0.1)
            except Exception:
                continue
            if req is None:
                continue
            op, args, fut = req
            try:
                if op == "get":
                    res = self.get(*args)
                elif op == "insert":
                    res = self.insert(*args)
                elif op == "update":
                    res = self.update(*args)
                elif op == "delete":
                    res = self.delete(*args)
                else:
                    res = None
                loop.call_soon_threadsafe(fut.set_result, res)
            except Exception as e:
                loop.call_soon_threadsafe(fut.set_exception, e)

    async def async_get(self, collection: str, query: dict = None) -> Any:
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._queue.async_q.put(("get", (collection, query), fut))
        return await fut

    async def async_insert(self, collection: str, document: dict) -> Any:
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._queue.async_q.put(("insert", (collection, document), fut))
        return await fut

    async def async_update(self, collection: str, query: dict, update: dict) -> Any:
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._queue.async_q.put(("update", (collection, query, update), fut))
        return await fut

    async def async_delete(self, collection: str, query: dict) -> Any:
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._queue.async_q.put(("delete", (collection, query), fut))
        return await fut

    def close(self):
        self._stop_thread = True
        self._thread.join()

    async def async_bulk_insert(self, collection: str, docs: list, db_name: str = None) -> Any:
        """
        Perform an async bulk insert of multiple documents into a collection and db.
        """
        if not docs:
            return None
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        def _bulk():
            col = self._get_collection(collection, db_name)
            result = col.insert_many(docs)
            self._cache.invalidate_prefix(f"{collection}:{db_name}:")
            return result.inserted_ids
        loop.run_in_executor(None, lambda: fut.set_result(_bulk()))
        return await fut

    async def async_buffered_insert(self, collection: str, doc: dict, db_name: str = None) -> None:
        await self._bulk_buffer_manager.async_buffered_insert(collection, doc, db_name)

    def get(self, collection: str, query: dict = None, db_name: str = None) -> Any:
        """
        Fetch documents from the specified collection (and database if db_name is provided).
        """
        key = f"{collection}:{str(query)}:{db_name}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        col = self._get_collection(collection, db_name)
        result = list(col.find(query or {}))
        self._cache.set(key, result)
        return result

    def _get_collection(self, name: str, db_name: str = None):
        if db_name:
            return self._client[db_name][name]
        return self._db[name]

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            col = self._get_collection(collection, db_name)
            result = list(col.find(query or {}))
            self._cache.set(key, result)
            return result

    def insert(self, collection: str, document: dict, upsert: bool = False, db_name: str = None) -> Any:
        """
        Insert a document into the collection (and database if db_name is provided). If upsert is True, replace or insert.
        """
        with self._lock:
            col = self._get_collection(collection, db_name)
            if upsert:
                key = document.get('_id')
                if key is not None:
                    result = col.replace_one({'_id': key}, document, upsert=True)
                    inserted_id = key if result.upserted_id is None else result.upserted_id
                else:
                    result = col.insert_one(document)
                    inserted_id = result.inserted_id
            else:
                result = col.insert_one(document)
                inserted_id = result.inserted_id
            cache_key = f"{collection}:{str({'_id': document.get('_id')})}:{db_name}"
            self._cache.invalidate(cache_key)
            self._cache.invalidate_prefix(f"{collection}:{db_name}:")
            return inserted_id
        return inserted_id


    def update(self, collection: str, query: dict, update: dict, upsert: bool = False, db_name: str = None) -> Any:
        """
        Update or replace documents matching query in the specified collection (and database if db_name is provided).
        If upsert is True, replace the document if it exists, otherwise insert.
        """
        with self._lock:
            col = self._get_collection(collection, db_name)
            if upsert:
                result = col.replace_one(query, update, upsert=True)
            else:
                result = col.update_many(query, {"$set": update})
        cache_key = f"{collection}:{str(query)}:{db_name}"
        self._cache.invalidate(cache_key)
        self._cache.invalidate_prefix(f"{collection}:{db_name}:")
        return result.modified_count


    def delete(self, collection: str, query: dict, db_name: str = None) -> Any:
        """
        Delete documents matching query from the specified collection (and database if db_name is provided).
        """
        with self._lock:
            col = self._get_collection(collection, db_name)
            result = col.delete_many(query)
        cache_key = f"{collection}:{str(query)}:{db_name}"
        self._cache.invalidate(cache_key)
        self._cache.invalidate_prefix(f"{collection}:{db_name}:")
        return result.deleted_count

