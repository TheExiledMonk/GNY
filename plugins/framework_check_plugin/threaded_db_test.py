"""
Threaded DB test helpers for framework_check_plugin.
"""

import threading
import time
import uuid

from db.config_storage import ConfigStorage


def db_worker(storage: ConfigStorage, thread_id: int, results: dict):
    """Each thread writes, updates, and deletes a config doc."""
    collection = "framework_check_test"
    doc_id = str(uuid.uuid4())
    # Insert
    doc = {"_id": doc_id, "thread_id": thread_id, "val": 1}
    storage.insert(collection, doc)
    results[thread_id] = {"inserted": doc_id}
    # Update
    storage.update(collection, {"_id": doc_id}, {"val": 2, "thread_id": thread_id})
    results[thread_id]["updated"] = True
    # Get
    res = storage.get(collection, {"_id": doc_id})
    results[thread_id]["fetched"] = bool(res)
    # Delete
    storage.delete(collection, {"_id": doc_id})
    results[thread_id]["deleted"] = True
