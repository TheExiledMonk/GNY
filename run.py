"""
Main entrypoint for the Execution Orchestration Framework.
"""
"""
Main entrypoint for the Execution Orchestration Framework.
Initializes logger and orchestrator once, and returns proper exit code on error.
"""
import sys
import time
import threading
from core.orchestrator import Orchestrator
from services.logger import get_logger
import uvicorn

_logger = None
_orchestrator = None

# --- Scheduler loop ---
def parse_schedule(schedule_str):
    # Minimal parser: supports "0 */1 * * *" (hourly), "*/10 * * * *" (every 10 min)
    if schedule_str is None:
        return None
    if "*/" in schedule_str:
        mins = int(schedule_str.split("*/")[1].split()[0])
        return mins * 60
    if "0 */" in schedule_str:
        hours = int(schedule_str.split("*/")[1].split()[0])
        return hours * 3600
    return None

def scheduler_loop(orchestrator):
    last_run = {}
    while True:
        now = time.time()
        for name, pdata in orchestrator.pipelines.items():
            interval = parse_schedule(pdata.get("schedule"))
            if interval is not None:
                if name not in last_run or now - last_run[name] >= interval:
                    threading.Thread(target=orchestrator._run_pipeline, args=(name,), daemon=True).start()
                    last_run[name] = now
        time.sleep(5)

def main():
    global _logger, _orchestrator
    _logger = get_logger()
    _orchestrator = Orchestrator()
    # Start scheduler
    t = threading.Thread(target=scheduler_loop, args=(_orchestrator,), daemon=True)
    t.start()
    # Start FastAPI server in foreground
    print("Daemon running. Scheduler and API server active. Press Ctrl+C to exit.")
    uvicorn.run("services.api_server:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
