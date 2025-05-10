"""
Main entrypoint for the Execution Orchestration Framework.
"""
"""
Main entrypoint for the Execution Orchestration Framework.
Initializes logger and orchestrator once, and returns proper exit code on error.
"""
import sys
import signal
import threading
from core.orchestrator import Orchestrator
from services.logger import get_logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from ui.server import app as flask_app

_logger = None
_orchestrator = None
_flask_thread = None
_scheduler = None


def _graceful_shutdown(signum, frame):
    global _logger, _orchestrator, _scheduler
    if _logger:
        _logger.info({"event": "shutdown", "signal": signum})
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    # Attempt to stop orchestrator threads if possible
    try:
        if hasattr(_orchestrator, 'thread_manager'):
            for name in list(_orchestrator.thread_manager.threads.keys()):
                stop_fn = getattr(_orchestrator.thread_manager, 'stop_pipeline_thread', None)
                if callable(stop_fn):
                    stop_fn(name)
    except Exception as e:
        if _logger:
            _logger.error({"event": "shutdown_error", "error": str(e)})
    # Stop the scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
    # Stop Flask server (not strictly needed since it's daemonized)
    sys.exit(0)

def _run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def main():
    global _logger, _orchestrator, _flask_thread, _scheduler
    _logger = get_logger()
    _orchestrator = Orchestrator()

    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Start Flask UI server in a background thread
    _flask_thread = threading.Thread(target=_run_flask, daemon=True)
    _flask_thread.start()
    print("Flask UI server started on http://0.0.0.0:8080")

    # --- APScheduler setup for cron jobs ---
    _scheduler = BackgroundScheduler()
    for pipeline_name, pdata in _orchestrator.pipelines.items():
        cron = pdata.get("schedule")
        if cron:
            job_id = f"pipeline_{pipeline_name}"
            if _scheduler.get_job(job_id):
                continue  # Job already scheduled
            try:
                trigger = CronTrigger.from_crontab(cron)
                _scheduler.add_job(
                    lambda name=pipeline_name: _orchestrator._run_pipeline(name),
                    trigger,
                    id=job_id,
                    replace_existing=True,
                    max_instances=1,
                )
                _logger.info({"event": "scheduler_job_added", "pipeline": pipeline_name, "cron": cron})
            except Exception as e:
                _logger.error({"event": "scheduler_job_error", "pipeline": pipeline_name, "cron": cron, "error": str(e)})
    _scheduler.start()

    print("Daemon running. Scheduler active. Press Ctrl+C to exit.")
    # Main thread just waits for signals
    try:
        while True:
            signal.pause()
    except KeyboardInterrupt:
        _graceful_shutdown(signal.SIGINT, None)

if __name__ == "__main__":
    main()
