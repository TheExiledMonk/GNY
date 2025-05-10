"""
Thread lifecycle test: supports start, pause, resume, and cancel for a worker thread.
"""

import threading
import time


class LifecycleWorker:
    def __init__(self):
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        self._cancel_event = threading.Event()
        self._status = []
        self._lock = threading.Lock()

    def run_test(self, result_dict):
        """
        Test-style worker: runs for 10 cycles, logs progress to result_dict.
        """
        self._status.append("started")
        for i in range(10):
            if self._cancel_event.is_set():
                self._status.append("cancelled")
                break
            self._pause_event.wait()  # Wait if paused
            self._status.append(f"working_{i}")
            time.sleep(0.05)
        else:
            self._status.append("completed")
        result_dict["status"] = self._status.copy()

    def pause(self):
        self._pause_event.clear()
        self._status.append("paused")

    def resume(self):
        self._pause_event.set()
        self._status.append("resumed")

    def cancel(self):
        self._cancel_event.set()
        self._status.append("cancel_signal")


class InteractiveLifecycleWorker:
    """
    A worker that runs indefinitely, supports pause/resume/cancel, and updates a jobs dict every 10 seconds.
    """
    @property
    def status(self):
        with self._lock:
            return self._status[-1] if self._status else "unknown"

    def __init__(self, jobs_dict, job_id):
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._cancel_event = threading.Event()
        self._lock = threading.Lock()
        self.jobs_dict = jobs_dict
        self.job_id = job_id
        self._status = []
        self._status.append("waiting")
        self._last_update = time.time()

    def run(self):
        self._set_status("active")
        while not self._cancel_event.is_set():
            self._pause_event.wait()  # Block here if paused
            # If unpaused, keep status as 'active'
            time.sleep(1)
        self._set_status("cancelled")

    def pause(self):
        self._pause_event.clear()
        self._set_status("paused")

    def resume(self):
        self._pause_event.set()
        self._set_status("resumed")

    def cancel(self):
        self._cancel_event.set()
        self._set_status("cancel_signal")

    def _set_status(self, status):
        with self._lock:
            self._status.clear()
            self._status.append(status)
            self.jobs_dict[self.job_id] = {
                "status": self._status,
                "timestamp": time.time(),
            }

    def run_test(self, result_dict):
        """
        Test-style worker: runs for 10 cycles, logs progress to result_dict.
        """
        self._log("started")
        for i in range(10):
            if self._cancel_event.is_set():
                self._log("cancelled")
                break
            self._pause_event.wait()  # Wait if paused
            self._log(f"working_{i}")
            time.sleep(0.05)
        else:
            self._log("completed")
        result_dict["status"] = self._status.copy()

    def pause(self):
        self._pause_event.clear()
        self._log("paused")

    def resume(self):
        self._pause_event.set()
        self._log("resumed")

    def cancel(self):
        self._cancel_event.set()
        self._log("cancel_signal")

    def _log(self, msg):
        with self._lock:
            self._status.append(msg)
