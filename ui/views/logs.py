"""
logs.py: Runtime + error logs view.
"""
from flask import render_template, request, session
from ui.utils import get_navbar, get_menu, get_plugin_names, require_auth
from datetime import datetime
import os

def logs_view():
    require_auth(session)
    log_path = os.path.join("logs", "orchestrator.log")
    logs = []
    level = request.args.get("level")
    start = request.args.get("start")
    end = request.args.get("end")
    q = request.args.get("q")
    filters = {"level": level, "start": start, "end": end, "q": q}
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()[-5000:]
        filtered = []
        for line in reversed(lines):
            if level and (f" {level.upper()} " not in line):
                continue
            if (start or end):
                try:
                    dt_str = line.split()[0]
                    dt = datetime.fromisoformat(dt_str)
                    if start and dt < datetime.fromisoformat(start):
                        continue
                    if end and dt > datetime.fromisoformat(end):
                        continue
                except Exception:
                    pass
            if q and q.lower() not in line.lower():
                continue
            filtered.append(line)
            if len(filtered) >= 200:
                break
        logs = [line for line in reversed(filtered) if line.strip()]
    except Exception as e:
        logs = [f"Error reading logs: {e}\n"]
    return render_template(
        "logs.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        logs=logs,
        filters=filters,
    )
