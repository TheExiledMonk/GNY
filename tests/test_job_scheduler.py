import time

from services.job_scheduler import JobScheduler


def test_worker_handles_exception():
    sched = JobScheduler(max_workers=1)

    def bad_func():
        raise ValueError("fail")

    sched.dispatch(bad_func)
    time.sleep(0.2)
    sched.shutdown()


def test_shutdown_joins_threads():
    sched = JobScheduler(max_workers=1)
    sched.shutdown()


def test_dispatch_runs():
    sched = JobScheduler(max_workers=1)
    called = {}

    def ok_func(x):
        called["x"] = x

    sched.dispatch(ok_func, 42)
    time.sleep(0.2)
    sched.shutdown()
    assert called["x"] == 42
