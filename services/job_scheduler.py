"""
JobScheduler: Runs dispatched plugin jobs, manages CPU target usage.
Threadsafe, supports background and async jobs.
"""
import threading
import queue
import time
from typing import Callable, Any, Optional

class JobScheduler:
    def __init__(self, max_workers: int = 4, cpu_target: int = 80):
        self._queue = queue.Queue()
        self._threads = []
        self._max_workers = max_workers
        self._cpu_target = cpu_target
        self._stop = threading.Event()
        for _ in range(max_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._threads.append(t)

    def _worker(self):
        while not self._stop.is_set():
            try:
                func, args, kwargs = self._queue.get(timeout=0.1)
                func(*args, **kwargs)
            except queue.Empty:
                continue
            except Exception as e:
                # TODO: Log error
                pass

    def dispatch(self, func: Callable, *args, **kwargs):
        self._queue.put((func, args, kwargs))

    def shutdown(self):
        self._stop.set()
        for t in self._threads:
            t.join()
