"""
JobScheduler: Runs dispatched plugin jobs, manages CPU target usage.
Threadsafe, supports background and async jobs.
"""
import threading
import queue
import time
from typing import Callable, Any, Optional

import uuid
import psutil

class PrioritizedJob:
    def __init__(self, priority: int, func: Callable, args: tuple, kwargs: dict):
        self.priority = priority
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.job_id = str(uuid.uuid4())
        self.status = "Queued"
        self.start_time = None
        self.end_time = None
        self.pid = None
        self.cpu = None
        self.mem = None
    def __lt__(self, other):
        return self.priority < other.priority

from services.config_manager import ConfigManager

class JobScheduler:
    """
    JobScheduler with priority queue and pause/resume/stop for low priority jobs.
    """
    def __init__(self, max_workers: int = None, cpu_target: int = 80):
        config = ConfigManager().get_global_config()
        scheduler_cfg = (config or {}).get('system', {}).get('scheduler', {}) if config else {}
        max_workers = max_workers or scheduler_cfg.get('max_workers', 8)
        self._queue = queue.PriorityQueue()
        self._threads = []
        self._max_workers = max_workers
        self._cpu_target = cpu_target
        self._stop = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        self._min_running_priority = None  # If set, only jobs <= this priority run
        self._job_status = {}  # job_id -> PrioritizedJob
        for _ in range(max_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._threads.append(t)

    def _worker(self):
        while not self._stop.is_set():
            self._pause_event.wait()
            try:
                job: PrioritizedJob = self._queue.get(timeout=0.1)
                # --- Auto-priority logic ---
                if job.priority > 5:
                    with self._queue.mutex:
                        has_high = any(j.priority < 5 for j in self._queue.queue)
                    if has_high:
                        self._queue.put(job)
                        time.sleep(0.05)
                        continue
                # Job control: skip if paused/canceled
                if job.status == "Paused":
                    self._queue.put(job)
                    time.sleep(0.05)
                    continue
                if job.status == "Canceled":
                    job.end_time = time.time()
                    continue
                # Job tracking
                job.status = "Running"
                job.start_time = time.time()
                self._job_status[job.job_id] = job
                try:
                    job.func(*job.args, **job.kwargs)
                finally:
                    job.end_time = time.time()
                    job.status = "Done"
                    # Resource usage (best effort)
                    try:
                        p = psutil.Process()
                        job.cpu = p.cpu_percent(interval=0.01)
                        job.mem = p.memory_info().rss
                    except Exception:
                        job.cpu = job.mem = None
            except queue.Empty:
                continue
            except Exception as e:
                # TODO: Log error
                pass

    def dispatch(self, func: Callable, *args, priority: int = 10, **kwargs) -> str:
        """
        Dispatch a job with a given priority (lower = higher priority).
        Returns the job_id for tracking.
        """
        job = PrioritizedJob(priority, func, args, kwargs)
        self._queue.put(job)
        self._job_status[job.job_id] = job
        return job.job_id

    def pause_all(self):
        """Pause all worker threads."""
        self._pause_event.clear()

    def resume_all(self):
        """Resume all worker threads."""
        self._pause_event.set()

    def pause_low_priority(self, min_priority: int):
        """
        Only allow jobs <= min_priority to run (lower value = higher priority).
        Others will be paused (re-queued until allowed).
        """
        self._min_running_priority = min_priority

    def resume_all_priorities(self):
        """Allow all priorities to run."""
        self._min_running_priority = None
        self._pause_event.set()

    def shutdown(self):
        self._stop.set()
        self._pause_event.set()
        for t in self._threads:
            t.join()

    def get_job_status(self):
        """
        Return a summary of all jobs: job_id, priority, status, run time, cpu, mem.
        """
        info = []
        for job in self._job_status.values():
            info.append({
                "job_id": job.job_id,
                "priority": job.priority,
                "status": job.status,
                "run_time": (job.end_time or time.time()) - job.start_time if job.start_time else None,
                "cpu": job.cpu,
                "mem": job.mem
            })
        return info

    def pause_job(self, job_id: str) -> bool:
        job = self._job_status.get(job_id)
        if job and job.status not in ("Done", "Canceled"):
            job.status = "Paused"
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self._job_status.get(job_id)
        if job and job.status == "Paused":
            job.status = "Queued"
            return True
        return False

    def cancel_job(self, job_id: str) -> bool:
        job = self._job_status.get(job_id)
        if job and job.status not in ("Done", "Canceled"):
            job.status = "Canceled"
            return True
        return False
