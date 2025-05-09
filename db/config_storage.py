"""
ConfigStorage: Threadsafe MongoDB-backed config storage with caching.
Plugins must never access the DB directly; all access is via this class.
"""
from threading import RLock, Thread
from typing import Any, Dict, Optional
from pymongo import MongoClient
import copy
import janus
import asyncio


class ConfigStorage:
    """
    Threadsafe config storage and cache for system, pipeline, and plugin configs.
    Supports both sync and async DB access via janus.Queue.
    Usage:
      - Use sync methods (get/insert/update/delete) for threaded code.
      - Use async methods (async_get/async_insert/async_update/async_delete) for asyncio code.
    """
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "orchestrator"):
        self._client = MongoClient(mongo_uri, connect=True)
        self._db = self._client[db_name]
        self._lock = RLock()
        self._cache: Dict[str, Any] = {}
        self._queue = janus.Queue()
        self._stop_thread = False
        self._thread = Thread(target=self._worker, daemon=True)
        self._thread.start()

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

    def _get_collection(self, name: str):
        return self._db[name]

    def get(self, collection: str, query: dict = None) -> Any:
        key = f"{collection}:{str(query)}"
        with self._lock:
            if key in self._cache:
                return copy.deepcopy(self._cache[key])
            col = self._get_collection(collection)
            result = list(col.find(query or {}))
            self._cache[key] = copy.deepcopy(result)
            return result

    def insert(self, collection: str, document: dict, upsert: bool = False) -> Any:
        """
        Insert a document into the collection. If upsert is True, replace or insert.
        """
        key_prefix = f"{collection}:"
        with self._lock:
            col = self._get_collection(collection)
            if upsert:
                # Use a unique key if provided, else fallback to insert_one
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
            # Invalidate all cache for this collection
            keys_to_remove = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_remove:
                del self._cache[k]
            return inserted_id

    def update(self, collection: str, query: dict, update: dict, upsert: bool = False) -> Any:
        """
        Update documents matching query. If upsert is True, insert if no match.
        """
        key_prefix = f"{collection}:"
        with self._lock:
            col = self._get_collection(collection)
            result = col.update_many(query, {"$set": update}, upsert=upsert)
            # Invalidate all cache for this collection
            keys_to_remove = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_remove:
                del self._cache[k]
            return result.modified_count

    def delete(self, collection: str, query: dict) -> Any:
        key_prefix = f"{collection}:"
        with self._lock:
            col = self._get_collection(collection)
            result = col.delete_many(query)
            # Invalidate all cache for this collection
            keys_to_remove = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_remove:
                del self._cache[k]
            return result.deleted_count
