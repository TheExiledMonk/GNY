"""
jobs.py: Job list view and control endpoints for the UI.
"""

import logging
import sys
from typing import Any, Dict, List

from flask import jsonify, render_template, request
from core.orchestrator import orchestrator
from services.job_scheduler import JobScheduler
from ui.utils import get_menu, get_navbar, get_plugin_names

# Wire up the scheduler from the orchestrator singleton
scheduler: JobScheduler = (
    orchestrator.thread_manager.scheduler
    if hasattr(orchestrator.thread_manager, "scheduler")
    else None
)


def jobs_html_view() -> Any:
    """
    Render jobs.html for browser navigation.
    """
    return render_template(
        "jobs.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
    )

def jobs_status_view() -> Any:
    """
    Always return current job list as JSON for the UI (AJAX).
    Shows jobs from both JobScheduler and ThreadManager.
    """
    jobs: List[Dict[str, Any]] = scheduler.get_job_status() if scheduler else []

    # Get jobs from ThreadManager
    thread_jobs: List[Dict[str, Any]] = []
    try:
        tm = orchestrator.thread_manager
        for name, info in tm.threads.items():
            thread = info.get("thread")
            control = info.get("control")
            status = (
                getattr(control, "status", None)
                or getattr(control, "get_status", lambda: None)()
            )
            thread_jobs.append(
                {
                    "job_id": name,
                    "status": status or ("alive" if thread.is_alive() else "stopped"),
                    "run_time": None,
                    "priority": "thread",
                    "cpu": None,
                    "mem": None,
                    "source": "thread_manager",
                }
            )
    except Exception as e:
        logging.getLogger("ui.jobs").warning(
            f"Could not load thread_manager jobs: {e}"
        )

    # Try to get plugin jobs from latest orchestrator context (legacy plugin jobs)
    plugin_jobs: List[Dict[str, Any]] = []
    try:
        ctx = None
        if (
            hasattr(orchestrator, "last_context")
            and orchestrator.last_context
        ):
            ctx = orchestrator.last_context
        elif (
            hasattr(orchestrator, "_last_context")
            and orchestrator._last_context
        ):
            ctx = orchestrator._last_context
        if (
            ctx
            and "framework_check" in ctx
            and "jobs" in ctx["framework_check"]
        ):
            for job_id, jobinfo in ctx["framework_check"]["jobs"].items():
                plugin_jobs.append(
                    {
                        "job_id": job_id,
                        "status": jobinfo.get("status", "unknown"),
                        "run_time": None,
                        "priority": "plugin",
                        "cpu": None,
                        "mem": None,
                        "source": "plugin",
                        **{
                            k: v
                            for k, v in jobinfo.items()
                            if k not in {"status"}
                        },
                    }
                )
    except Exception as e:
        logging.getLogger("ui.jobs").warning(
            f"Could not load plugin jobs: {e}"
        )

    # Debug: print orchestrator and thread_manager id
    logging.getLogger("ui.jobs").info({
        "event": "debug_orchestrator_ids",
        "sys_modules_id": id(sys.modules['core.orchestrator']),
        "orchestrator_id": id(orchestrator),
        "thread_manager_id": id(orchestrator.thread_manager),
    })
    # Debug: log thread manager jobs
    logging.getLogger("ui.jobs").info({
        "event": "debug_threads",
        "threads": list(tm.threads.keys())
    })
    # Merge jobs
    merged_jobs = jobs + thread_jobs + plugin_jobs
    return jsonify({"jobs": merged_jobs})


def job_action_view() -> Any:
    """
    Handle pause/resume/cancel actions for jobs, supporting both scheduler and
    thread_manager jobs. Logs all actions in structured format to logs/.
    """
    import traceback
    logger = logging.getLogger("ui.jobs")
    try:
        data = request.json
        job_id = data.get("job_id")
        action = data.get("action")
        if not job_id or not action:
            logger.warning(
                {
                    "event": "job_action_invalid_request",
                    "job_id": job_id,
                    "action": action,
                }
            )
            return jsonify({"error": "Missing job_id or action"}), 400

        result = False
        source = None

        # ThreadManager jobs take precedence
        tm = orchestrator.thread_manager
        if job_id in tm.threads:
            try:
                if action == "pause":
                    tm.pause_pipeline_thread(job_id)
                    result = True
                elif action == "resume":
                    tm.resume_pipeline_thread(job_id)
                    result = True
                elif action == "cancel":
                    tm.cancel_pipeline_thread(job_id)
                    result = True
                else:
                    logger.warning(
                        {
                            "event": "job_action_invalid_action",
                            "job_id": job_id,
                            "action": action,
                        }
                    )
                    return jsonify({"error": "Invalid action"}), 400
                source = "thread_manager"
            except Exception as e:
                logger.error(
                    {
                        "event": "job_action_error",
                        "job_id": job_id,
                        "action": action,
                        "source": "thread_manager",
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }
                )
                return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

        elif scheduler and hasattr(scheduler, f"{action}_job"):
            try:
                method = getattr(scheduler, f"{action}_job")
                result = method(job_id)
                source = "scheduler"
            except Exception as e:
                logger.error(
                    {
                        "event": "job_action_error",
                        "job_id": job_id,
                        "action": action,
                        "source": "scheduler",
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }
                )
                return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

        else:
            logger.warning(
                {
                    "event": "job_action_not_found",
                    "job_id": job_id,
                    "action": action,
                }
            )
            return jsonify({"error": "Job not found or action not supported"}), 404

        logger.info(
            {
                "event": "job_action",
                "job_id": job_id,
                "action": action,
                "result": result,
                "source": source,
            }
        )
        return jsonify({"result": result})
    except Exception as e:
        logger.error({
            "event": "job_action_fatal_error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        })
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500
