"""
UnifiedLogger: Central structured logger with Slack integration.
All logs go to logs/ and are multiprocess/thread safe.
"""

import json
import logging
import logging.handlers
import os
from threading import Lock
from typing import Any, Dict

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
LOG_FILE = os.path.join(LOG_DIR, "orchestrator.log")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK_URL")

_logger_instance = None
_logger_lock = Lock()


class UnifiedLogger:
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.logger = logging.getLogger("orchestrator")
        self.logger.setLevel(logging.INFO)
        # Only add handler if it hasn't been added yet
        if not any(
            isinstance(h, logging.handlers.RotatingFileHandler)
            and h.baseFilename == os.path.abspath(LOG_FILE)
            for h in self.logger.handlers
        ):
            handler = logging.handlers.RotatingFileHandler(
                LOG_FILE, maxBytes=5_000_000, backupCount=5
            )
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, data: Dict[str, Any]):
        self.logger.info(json.dumps(data))

    def error(self, data: Dict[str, Any]):
        self.logger.error(json.dumps(data))
        self._send_slack(data, level="ERROR")

    def fatal(self, data: Dict[str, Any]):
        self.logger.critical(json.dumps(data))
        self._send_slack(data, level="FATAL")

    def _send_slack(self, data: Dict[str, Any], level: str):
        if not SLACK_WEBHOOK:
            return
        if level not in ("ERROR", "FATAL"):
            return
        import requests

        msg = f"[{level}] {json.dumps(data)}"
        try:
            requests.post(SLACK_WEBHOOK, json={"text": msg})
        except Exception:
            pass


def get_logger():
    global _logger_instance
    with _logger_lock:
        if _logger_instance is None:
            _logger_instance = UnifiedLogger()
        return _logger_instance
