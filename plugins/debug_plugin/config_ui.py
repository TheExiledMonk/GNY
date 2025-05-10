"""
Debug Plugin Config UI: Exposes log file contents via Flask route for UI inspection.
"""

from html import escape

from flask import Response, flash, redirect, render_template, request, url_for

from ui.utils import get_menu, get_navbar, get_plugin_names

from . import status


def debug_plugin_status_view(req) -> Response:
    """
    Flask-compatible view: renders the debug_plugins.log file in the shared plugin_status.html template.
    Includes navbar and menu for UI consistency.
    Handles POST to clear the log file.
    Always returns a valid HTML response, even on error.
    """
    plugin = "debug_plugin"
    if req.method == "POST":
        import os
        import sys
        from datetime import datetime

        log_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "logs", "debug_plugins.log"
            )
        )
        logs_dir = os.path.dirname(log_path)
        orchestrator_log = os.path.join(logs_dir, "orchestrator.log")
        # Ensure logs/ exists
        os.makedirs(logs_dir, exist_ok=True)
        print(f"[DEBUG_PLUGIN] POST to status, form={dict(req.form)}", file=sys.stderr)
        try:
            if req.form.get("clear_log"):
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write("")
                # Try to log to debug_plugin_errors.log
                try:
                    with open(
                        os.path.join(logs_dir, "debug_plugin_errors.log"),
                        "a",
                        encoding="utf-8",
                    ) as ferr:
                        ferr.write(
                            f"[{datetime.utcnow()}] Cleared debug log via POST\n"
                        )
                except Exception:
                    pass
                flash("Debug log cleared.", "success")
                # Add cache-busting param to force browser to reload
                import time

                return redirect(
                    url_for(
                        "ui.plugin_status_view", plugin=plugin, _cb=int(time.time())
                    )
                )
            else:
                # Log unexpected POST without clear_log
                try:
                    with open(
                        os.path.join(logs_dir, "debug_plugin_errors.log"),
                        "a",
                        encoding="utf-8",
                    ) as ferr:
                        ferr.write(
                            f"[{datetime.utcnow()}] POST to status but no clear_log in form: {dict(req.form)}\n"
                        )
                except Exception:
                    pass
        except Exception as e:
            flash(f"Error clearing debug log: {e}", "error")
            # Only log error to orchestrator.log if debug_plugin_errors.log fails
            try:
                with open(
                    os.path.join(logs_dir, "debug_plugin_errors.log"),
                    "a",
                    encoding="utf-8",
                ) as ferr:
                    ferr.write(
                        f"[{datetime.utcnow()}] Error clearing log: {type(e).__name__}: {e}\n"
                    )
            except Exception:
                with open(orchestrator_log, "a", encoding="utf-8") as ferr:
                    ferr.write(
                        f"[{datetime.utcnow()}] [DEBUG_PLUGIN] Error clearing log: {type(e).__name__}: {e}\n"
                    )
            # Fall through to render status
    import json
    import os
    from datetime import datetime

    step = req.args.get("step", "").strip()
    event = req.args.get("event", "").strip()
    start = req.args.get("start", "").strip()
    end = req.args.get("end", "").strip()
    try:
        # Parse log file as JSON lines, filter
        log_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "logs", "debug_plugins.log"
            )
        )
        entries = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if step and str(entry.get("pipeline_step", "")) != step:
                            continue
                        if event and str(entry.get("event", "")) != event:
                            continue
                        if start:
                            try:
                                ts = entry.get("timestamp")
                                if ts and ts < start:
                                    continue
                            except Exception:
                                continue
                        if end:
                            try:
                                ts = entry.get("timestamp")
                                if ts and ts > end:
                                    continue
                            except Exception:
                                continue
                        entries.append(entry)
                    except Exception:
                        continue
        # Show last 100 filtered entries, newest last
        entries = entries[-100:]
        pretty = (
            "\n\n".join(json.dumps(e, indent=2, default=str) for e in entries)
            if entries
            else "No debug logs found."
        )
        # Filter form
        filter_form = f"""
      <form method="get" style="margin-bottom:1.5em;display:flex;gap:0.7em;align-items:flex-end;">
        <div><label>Step<br><input type="text" name="step" value="{step}" style="width:7em;"></label></div>
        <div><label>Event<br><input type="text" name="event" value="{event}" style="width:7em;"></label></div>
        <div><label>Start (UTC)<br><input type="text" name="start" value="{start}" placeholder="YYYY-MM-DD" style="width:10em;"></label></div>
        <div><label>End (UTC)<br><input type="text" name="end" value="{end}" placeholder="YYYY-MM-DD" style="width:10em;"></label></div>
        <button type="submit" style="background:#1557a6;color:#fff;border:none;padding:0.6em 1.3em;border-radius:5px;font-size:1em;cursor:pointer;">Filter</button>
      </form>
      """
        status_html = (
            filter_form
            + f"<pre style='background:#f4f8fd;border-radius:6px;padding:1.2em;font-size:1.07em;overflow-x:auto;'>{pretty}</pre>"
        )
    except Exception as e:
        status_html = f"<div style='color:#fff;background:#a00;padding:1em;border-radius:8px;'>[UI ERROR] Could not load debug log: {type(e).__name__}: {escape(str(e))}</div>"
    navbar = get_navbar()
    menu = get_menu(get_plugin_names())
    return Response(
        render_template(
            "plugin_status.html",
            navbar=navbar,
            menu=menu,
            plugin=plugin,
            status=status_html,
        ),
        mimetype="text/html",
    )
