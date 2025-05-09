"""
jobs.py: Job list view and control endpoints for the UI.
"""
from flask import jsonify, request, render_template
from services.job_scheduler import JobScheduler
from core.orchestrator import Orchestrator

# Wire up the scheduler from the orchestrator singleton
orchestrator = Orchestrator()
scheduler: JobScheduler = orchestrator.thread_manager.scheduler if hasattr(orchestrator.thread_manager, 'scheduler') else None

def jobs_view():
    """Return current job list as JSON for the UI (AJAX) or render jobs.html for GET."""
    if request.method == "GET" and request.accept_mimetypes.accept_html:
        return render_template("jobs.html")
    return jsonify({"jobs": scheduler.get_job_status()})

def job_action_view():
    """Handle pause/resume/cancel actions for jobs."""
    data = request.json
    job_id = data.get("job_id")
    action = data.get("action")
    if not job_id or not action:
        return jsonify({"error": "Missing job_id or action"}), 400
    result = False
    if action == "pause":
        result = scheduler.pause_job(job_id)
    elif action == "resume":
        result = scheduler.resume_job(job_id)
    elif action == "cancel":
        result = scheduler.cancel_job(job_id)
    else:
        return jsonify({"error": "Invalid action"}), 400
    return jsonify({"result": result})
