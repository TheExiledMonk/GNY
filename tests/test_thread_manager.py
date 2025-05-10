"""
Unit tests for core.thread_manager: thread start/stop, error handling.
"""
import pytest
from core.thread_manager import ThreadManager
import threading

import pytest
from core.thread_manager import ThreadManager
import threading

class DummyControl:
    def __init__(self):
        self.paused = False
        self.resumed = False
        self.cancelled = False
    def pause(self): self.paused = True
    def resume(self): self.resumed = True
    def cancel(self): self.cancelled = True

def test_start_and_control_thread():
    tm = ThreadManager()
    def target(): pass
    control = DummyControl()
    tm.start_pipeline_thread('t1', target, control)
    assert 't1' in tm.threads
    tm.pause_pipeline_thread('t1')
    assert control.paused
    tm.resume_pipeline_thread('t1')
    assert control.resumed
    tm.cancel_pipeline_thread('t1')  # Should also stop and remove
    assert control.cancelled
    assert 't1' not in tm.threads

def test_stop_pipeline_thread():
    tm = ThreadManager()
    def target(): pass
    control = DummyControl()
    tm.start_pipeline_thread('t2', target, control)
    assert 't2' in tm.threads
    tm.stop_pipeline_thread('t2')
    assert 't2' not in tm.threads

def test_control_nonexistent_thread():
    tm = ThreadManager()
    # Should not raise
    tm.pause_pipeline_thread('notfound')
    tm.resume_pipeline_thread('notfound')
    tm.cancel_pipeline_thread('notfound')
    tm.stop_pipeline_thread('notfound')
