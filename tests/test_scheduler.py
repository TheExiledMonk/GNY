"""
Unit test for JobScheduler.
"""
from services.job_scheduler import JobScheduler
import time

def test_scheduler_dispatch():
    scheduler = JobScheduler(max_workers=1)
    result = {}
    def job():
        result["ran"] = True
    scheduler.dispatch(job)
    time.sleep(0.2)
    assert result.get("ran") is True
    scheduler.shutdown()
