#!/bin/bash
# run.sh: Restart run.py automatically on SIGHUP (exit code 129)
# All logs go to logs/server.log

LOGDIR="$(dirname "$0")/logs"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/server.log"

while true; do
    echo "[run.sh] Starting run.py..." | tee -a "$LOGFILE"
    FLASK_ENV=production python3 run.py "$@" 2>&1 | tee -a "$LOGFILE"
    EXIT_CODE=${PIPESTATUS[0]}
    if [ "$EXIT_CODE" -eq 0 ]; then
        echo "[run.sh] Exited cleanly with code 0, not restarting." | tee -a "$LOGFILE"
        exit 0
    elif [ "$EXIT_CODE" -eq 120 ]; then
        echo "[run.sh] Exited with code 120, not restarting." | tee -a "$LOGFILE"
        exit 120
    else
        echo "[run.sh] Exited with code $EXIT_CODE, restarting in 2s..." | tee -a "$LOGFILE"
        sleep 2
    fi
done
