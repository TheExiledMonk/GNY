from flask import Flask, request, render_template, redirect, url_for, jsonify
from core.orchestrator import Orchestrator
import threading
import os
from dotenv import load_dotenv
from passlib.hash import bcrypt
from services.resource_monitor import ResourceMonitor
from flask import session

load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")

app = Flask(__name__)
app.secret_key = "supersecret"
orchestrator = Orchestrator()

@app.route("/jobs", methods=["GET"])
def jobs_page():
    if not is_authenticated():
        return redirect(url_for("login"))
    return render_template(
        "jobs.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names())
    )

from core.context_builder import global_job_scheduler

@app.route("/jobs/status", methods=["GET"])
def jobs_status():
    return jsonify({"jobs": global_job_scheduler.get_job_status()})

@app.route("/jobs/action", methods=["POST"])
def jobs_action():
    data = request.get_json()
    job_id = data.get("job_id")
    action = data.get("action")
    if not job_id or not action:
        return {"error": "Missing job_id or action"}
    if action == "pause":
        result = global_job_scheduler.pause_job(job_id)
    elif action == "resume":
        result = global_job_scheduler.resume_job(job_id)
    elif action == "cancel":
        result = global_job_scheduler.cancel_job(job_id)
    else:
        return {"error": "Invalid action"}
    return {"result": result}

def is_authenticated():
    from flask import session
    return session.get("user") == ADMIN_USERNAME

def require_auth():
    if not is_authenticated():
        from flask import abort
        abort(401, description="Not authenticated")


def get_navbar():
    return '''
    <nav style="background: #1557a6; color: #fff; padding: 0.8em 1.5em; display: flex; align-items: center; justify-content: space-between;">
      <div style="font-weight: bold; font-size: 1.3em; letter-spacing: 1px;">GNY DataWarehouse NexGen</div>
      <div>
        <form method="post" action="/logout" style="display:inline; margin:0;">
          <button style="background:#fff; color:#1557a6; border:none; padding:0.4em 1.2em; border-radius:4px; font-weight:bold; cursor:pointer;">Logout</button>
        </form>
      </div>
    </nav>
    '''
def get_menu(plugins=None):
    # Plugins dropdown with hover submenu for config/status
    if not plugins:
        return '''
        <div style="background: #eaf1fb; padding: 0.7em 1.5em; display: flex; gap: 2em; font-size: 1.08em;">
          <div style="position:relative;">
            <span style="color:#1557a6; font-weight:500; cursor:pointer;">Plugins</span>
          </div>
          <a href="/health" style="color:#1557a6; text-decoration:none; font-weight:500;">System Health</a>
          <a href="/logs" style="color:#1557a6; text-decoration:none; font-weight:500;">Logs</a>
        </div>'''
    # Dropdown with all plugins and submenus
    submenu = ''.join(f'''
      <div class="plugin-dropdown-item">
        <span>{p}</span>
        <div class="plugin-submenu">
          <a href="/plugins/{p}/config">Config</a>
          <a href="/plugins/{p}/status">Status</a>
        </div>
      </div>
    ''' for p in plugins)
    return f'''
    <style>
    .plugin-dropdown {{ position:relative; }}
    .plugin-dropdown:hover .plugin-dropdown-list {{ display:block; }}
    .plugin-dropdown-list {{ display:none; position:absolute; left:0; top:100%; background:#fff; border:1px solid #c9e2ff; min-width:150px; z-index:10; border-radius:6px; box-shadow:0 2px 8px #0001; }}
    .plugin-dropdown-item {{ padding:0.4em 1.1em; white-space:nowrap; position:relative; }}
    .plugin-dropdown-item:hover {{ background:#eaf1fb; }}
    .plugin-submenu {{ display:none; position:absolute; left:100%; top:0; background:#fff; border:1px solid #c9e2ff; min-width:110px; z-index:11; border-radius:6px; box-shadow:0 2px 8px #0001; }}
    .plugin-dropdown-item:hover .plugin-submenu {{ display:block; }}
    .plugin-submenu a {{ display:block; padding:0.4em 1em; color:#1557a6; text-decoration:none; }}
    .plugin-submenu a:hover {{ background:#eaf1fb; }}
    </style>
    <div style="background: #eaf1fb; padding: 0.7em 1.5em; display: flex; gap: 2em; font-size: 1.08em;">
      <div class="plugin-dropdown">
        <span style="color:#1557a6; font-weight:500; cursor:pointer;">Plugins ▾</span>
        <div class="plugin-dropdown-list">
          {submenu}
        </div>
      </div>
      <a href="/" style="color:#1557a6; text-decoration:none; font-weight:500;">Pipelines</a>
      <a href="/health" style="color:#1557a6; text-decoration:none; font-weight:500;">System Health</a>
      <a href="/logs" style="color:#1557a6; text-decoration:none; font-weight:500;">Logs</a>
      <a href="/jobs" style="color:#1557a6; text-decoration:none; font-weight:500;">Jobs</a>
    </div>
    '''

@app.route("/health", methods=["GET"])
def health():
    if not is_authenticated():
        return redirect(url_for("dashboard"))
    stats = ResourceMonitor().get_stats()
    return render_template(
        "health.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        stats=stats,
    )

def get_plugin_names():
    import os
    plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
    return [d for d in os.listdir(plugin_dir)
            if os.path.isdir(os.path.join(plugin_dir, d)) and not d.startswith("__")]

@app.route("/plugins", methods=["GET"])
def list_plugins():
    if not is_authenticated():
        return redirect(url_for("dashboard"))
    plugins = get_plugin_names()
    return jsonify({"plugins": plugins})

from db.config_storage import ConfigStorage
from db.plugin_config_repo import PluginConfigRepo

config_storage = ConfigStorage()
plugin_config_repo = PluginConfigRepo(config_storage)

@app.route("/plugins/<plugin>/config", methods=["GET", "POST"])
def plugin_config(plugin):
    if not is_authenticated():
        return redirect(url_for("dashboard"))
    import importlib
    try:
        mod = importlib.import_module(f"plugins.{plugin}")
    except Exception as e:
        import traceback
        from services.logger import get_logger
        get_logger().error({
            "event": "plugin_import_error",
            "plugin": plugin,
            "error": str(e),
        })
        return f"<h2>Error loading plugin '{plugin}': {e}</h2>", 500
    if hasattr(mod, "handle_config_request"):
        from flask import request
        config_html = mod.handle_config_request(request)
        box_style = "max-width:700px;margin:2.5em auto 0 auto;padding:2em 2.5em;background:#fff;border-radius:12px;box-shadow:0 2px 16px #0001;"
        navbar = get_navbar()
        menu = get_menu(get_plugin_names())
        full_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <title>Gather Plugin Config</title>
          <style>body{{margin:0;font-family:sans-serif;background:#f6f8fb;}}</style>
        </head>
        <body>
          {navbar}
          {menu}
          <div style="{box_style}">
            {config_html}
          </div>
        </body>
        </html>
        '''
        return full_html
    return f"<h2>Plugin '{plugin}' does not provide handle_config_request(). No config UI available.</h2>", 501

@app.route("/plugins/<plugin>/status")
def plugin_status(plugin):
    if not is_authenticated():
        return redirect(url_for("dashboard"))
    try:
        mod = __import__(f"plugins.{plugin}", fromlist=["get_status"])
        status = mod.get_status()
    except Exception as e:
        status = {"error": str(e)}
    return templates.TemplateResponse(
        "plugin_status.html",
        {
            "request": request,
            "navbar": get_navbar(),
            "menu": get_menu(get_plugin_names()),
            "plugin": plugin,
            "status": status,
        }
    )

from datetime import datetime

@app.route("/logs", methods=["GET"])
def logs_page():
    if not is_authenticated():
        return redirect(url_for("dashboard"))
    from flask import request, render_template
    log_path = "logs/orchestrator.log"
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

@app.route("/", methods=["GET"])
def dashboard():
    if not is_authenticated():
        return '''
            <h2>Login</h2>
            <form method='post' action='/login'>
                <input name='username' placeholder='Username' />
                <input name='password' type='password' placeholder='Password' />
                <button type='submit'>Login</button>
            </form>
            '''
    pipelines = list(orchestrator.pipelines.keys())
    return render_template(
        "dashboard.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
        pipelines=pipelines,
    )

@app.route("/login", methods=["POST"])
def login():
    from flask import request, session, redirect, url_for
    username = request.form.get("username")
    password = request.form.get("password")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session["user"] = username
        return redirect(url_for("dashboard"))
    return "<h2>Login failed</h2><a href='/'>Try again</a>", 401

@app.route("/logout", methods=["POST"])
def logout():
    from flask import session, redirect, url_for
    session.clear()
    return redirect(url_for("dashboard"))

@app.route("/trigger", methods=["POST"])
def trigger_pipeline():
    require_auth(request)
    pipeline = request.form.get("pipeline")
    if pipeline not in orchestrator.pipelines:
        return "<h2>Pipeline not found: {}</h2>".format(pipeline), 404
    priority = orchestrator.pipelines[pipeline].get("priority", 10)
    from core.context_builder import global_job_scheduler
    global_job_scheduler.dispatch(orchestrator._run_pipeline, pipeline, priority=priority)
    return redirect(url_for("dashboard"))

@app.route("/pipelines", methods=["GET"])
def list_pipelines():
    require_auth()
    from flask import jsonify
    return jsonify(list(orchestrator.pipelines.keys()))
