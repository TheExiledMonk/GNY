"""
dashboard.py: Plugin/pipeline overview view.
"""
from flask import render_template, request, redirect, url_for, flash
from core.orchestrator import Orchestrator
from ui.utils import get_menu, get_navbar, get_plugin_names, is_authenticated
from flask import session

def trigger_pipeline_view() -> str:
    """
    Handles POST to /trigger. Triggers the selected pipeline via Orchestrator and returns a status message.
    """
    if not is_authenticated(session):
        return redirect(url_for("ui.dashboard_view"))
    pipeline = request.form.get("pipeline")
    if not pipeline:
        flash("No pipeline specified.", "error")
        return redirect(url_for("ui.dashboard_view"))
    orchestrator = Orchestrator()
    try:
        result = orchestrator.trigger_pipeline(pipeline)
        flash(f"Pipeline '{pipeline}' triggered: {result}", "success")
    except Exception as e:
        flash(f"Failed to trigger pipeline '{pipeline}': {e}", "error")
    return redirect(url_for("ui.dashboard_view"))

def dashboard_view():
    if not is_authenticated(session):
        # Show a simple login form
        return '''
            <h2>Login</h2>
            <form method='post' action='/login'>
                <input name='username' placeholder='Username' />
                <input name='password' type='password' placeholder='Password' />
                <button type='submit'>Login</button>
            </form>
            '''
    orchestrator = Orchestrator()  # Or get a global instance if available
    from datetime import datetime
    from croniter import croniter
    pipelines_info = []
    now = datetime.utcnow()
    for name, pdata in orchestrator.pipelines.items():
        schedule = pdata.get("schedule")
        next_run = None
        seconds_remaining = None
        if schedule:
            try:
                itr = croniter(schedule, now)
                next_run_dt = itr.get_next(datetime)
                next_run = next_run_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                seconds_remaining = int((next_run_dt - now).total_seconds())
            except Exception as e:
                next_run = f"Invalid schedule: {e}"
                seconds_remaining = None
        pipelines_info.append({
            "name": name,
            "schedule": schedule,
            "next_run": next_run,
            "seconds_remaining": seconds_remaining,
        })
    navbar = get_navbar()
    menu = get_menu(get_plugin_names())
    return render_template(
        "dashboard.html",
        pipelines=pipelines_info,
        navbar=navbar,
        menu=menu
    )
