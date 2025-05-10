"""
ResourceMonitor: Tracks CPU/mem/storage/usage/database_health stats for the system.
Threadsafe, can be polled or run in background.
"""

import shutil
from typing import Any, Dict

import psutil
from pymongo import MongoClient


class ResourceMonitor:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017"):
        self._mongo_uri = mongo_uri

    def get_stats(self) -> Dict[str, Any]:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()._asdict()
        disk = shutil.disk_usage("/")
        db_health = self._get_db_health()
        return {
            "cpu": cpu,
            "memory": mem,
            "disk": {"total": disk.total, "used": disk.used, "free": disk.free},
            "db_health": db_health,
        }

    def _get_db_health(self) -> Dict[str, Any]:
        try:
            client = MongoClient(self._mongo_uri, serverSelectionTimeoutMS=500)
            info = client.admin.command("serverStatus")
            return {"ok": True, "info": info.get("ok", 0)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
