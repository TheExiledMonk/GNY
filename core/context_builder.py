"""
ContextBuilder: Constructs the context object passed into plugins.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from services.config_manager import ConfigManager
from services.job_scheduler import JobScheduler
from services.logger import get_logger

# Singleton service instances for context reuse
global_config_manager = ConfigManager()
global_job_scheduler = JobScheduler()
global_logger = get_logger()


def build_context(pipeline: str, hook: str) -> Dict[str, Any]:
    """
    Build the execution context for a plugin run.
    Returns a dict with run metadata and shared service handles.
    Structure:
        {
            "run_id": str,
            "start_time": datetime,
            "pipeline": str,
            "hook": str,
            "services": {
                "config": ConfigManager,
                "jobs": JobScheduler,
                "log": UnifiedLogger,
            }
        }
    """
    return {
        "run_id": str(uuid4()),
        "start_time": datetime.utcnow(),
        "pipeline": pipeline,
        "hook": hook,
        "services": {
            "config": global_config_manager,
            "jobs": global_job_scheduler,
            "log": global_logger,
        },
    }
