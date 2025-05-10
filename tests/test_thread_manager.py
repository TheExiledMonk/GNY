"""
Tests for core.thread_manager
"""
from core.thread_manager import ThreadManager
import time

def test_thread_manager_starts_thread():
    tm = ThreadManager()
    ran = {}
    def fn(name):
        ran[name] = True
    tm.start_pipeline_thread("foo", fn, "foo")
    time.sleep(0.2)
    assert ran.get("foo")
