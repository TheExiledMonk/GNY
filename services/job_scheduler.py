"""
JobScheduler: Runs dispatched plugin jobs, manages CPU target usage.
Threadsafe, supports background and async jobs.
"""

import logging
import queue
import threading
import time
import uuid
from typing import Callable

import psutil

from services.config_manager import ConfigManager

# Set up logging
logging.basicConfig(filename="logs/job_scheduler.log", level=logging.INFO)


class PrioritizedJob:
    """Represents a job with a given priority."""

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


class JobStatusTracker:
    """Tracks the status of jobs."""

    def __init__(self):
        self._job_status = {}  # job_id -> PrioritizedJob

    def add_job(self, job: PrioritizedJob):
        """Adds a job to the tracker."""
        self._job_status[job.job_id] = job

    def get_job_status(self, job_id: str) -> PrioritizedJob:
        """Returns the status of a job."""
        return self._job_status.get(job_id)

    def update_job_status(self, job_id: str, status: str):
        """Updates the status of a job."""
        job = self._job_status.get(job_id)
        if job:
            job.status = status


class JobWorker:
    """Runs jobs from the queue."""

    def __init__(
        self,
        queue: queue.PriorityQueue,
        job_status_tracker: JobStatusTracker,
        pause_event: threading.Event,
    ):
        self._queue = queue
        self._job_status_tracker = job_status_tracker
        self._pause_event = pause_event

    def run(self):
        """Runs the worker loop."""
        while True:
            self._pause_event.wait()
            try:
                job: PrioritizedJob = self._queue.get(timeout=0.1)
                self._run_job(job)
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error running job: {e}")

    def _run_job(self, job: PrioritizedJob):
        """Runs a single job."""
        self._job_status_tracker.update_job_status(job.job_id, "Running")
        job.start_time = time.time()
        try:
            job.func(*job.args, **job.kwargs)
        finally:
            job.end_time = time.time()
            self._job_status_tracker.update_job_status(job.job_id, "Done")
            # Resource usage (best effort)
            try:
                p = psutil.Process()
                job.cpu = p.cpu_percent(interval=0.01)
                job.mem = p.memory_info().rss
            except Exception:
                job.cpu = job.mem = None


class JobScheduler:
    """
    JobScheduler with priority queue and pause/resume/stop for low priority jobs.
    """

    def __init__(self, max_workers: int = None, cpu_target: int = 80):
        config = ConfigManager().get_global_config()
        scheduler_cfg = (
            (config or {}).get("system", {}).get("scheduler", {}) if config else {}
        )
        max_workers = max_workers or scheduler_cfg.get("max_workers", 8)
        self._queue = queue.PriorityQueue()
        self._job_status_tracker = JobStatusTracker()
        self._workers = []
        self._max_workers = max_workers
        self._cpu_target = cpu_target
        self._stop = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        for _ in range(max_workers):
            worker = JobWorker(self._queue, self._job_status_tracker, self._pause_event)
            t = threading.Thread(target=worker.run, daemon=True)
            t.start()
            self._workers.append(t)

    def dispatch(self, func: Callable, *args, priority: int = 10, **kwargs) -> str:
        """
        Dispatch a job with a given priority (lower = higher priority).
        Returns the job_id for tracking.
        """
        job = PrioritizedJob(priority, func, args, kwargs)
        self._queue.put(job)
        self._job_status_tracker.add_job(job)
        return job.job_id

    def pause_all(self):
        """Pause all worker threads."""
        self._pause_event.clear()

    def resume_all(self):
        """Resume all worker threads."""
        self._pause_event.set()

    def shutdown(self):
        self._stop.set()
        self._pause_event.set()
        for t in self._workers:
            t.join()

    def get_job_status(self):
        """
        Return a summary of all jobs: job_id, priority, status, run time, cpu, mem.
        """
        info = []
        for job in self._job_status_tracker._job_status.values():
            info.append(
                {
                    "job_id": job.job_id,
                    "priority": job.priority,
                    "status": job.status,
                    "run_time": (
                        (job.end_time or time.time()) - job.start_time
                        if job.start_time
                        else None
                    ),
                    "cpu": job.cpu,
                    "mem": job.mem,
                }
            )
        return info
