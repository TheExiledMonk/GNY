from fastapi import FastAPI, HTTPException, Request, Response, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from core.orchestrator import Orchestrator
import threading
import os
from dotenv import load_dotenv
from passlib.hash import bcrypt
from services.resource_monitor import ResourceMonitor
from fastapi.templating import Jinja2Templates

load_dotenv()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")
orchestrator = Orchestrator()

security = HTTPBasic()

def is_authenticated(request: Request):
    return request.session.get("user") == ADMIN_USERNAME

def require_auth(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")

templates = Jinja2Templates(directory="ui/templates")

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
    </div>
    '''

@app.get("/health", response_class=HTMLResponse)
def health(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    stats = ResourceMonitor().get_stats()
    return templates.TemplateResponse(
        "health.html",
        {
            "request": request,
            "navbar": get_navbar(),
            "menu": get_menu(get_plugin_names()),
            "stats": stats,
        }
    )

def get_plugin_names():
    import os
    plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")
    return [d for d in os.listdir(plugin_dir)
            if os.path.isdir(os.path.join(plugin_dir, d)) and not d.startswith("__")]

@app.get("/plugins", response_class=HTMLResponse)
def list_plugins(request: Request):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    plugins = get_plugin_names()
    return {"plugins": plugins}

from db.config_storage import ConfigStorage
from db.plugin_config_repo import PluginConfigRepo

config_storage = ConfigStorage()
plugin_config_repo = PluginConfigRepo(config_storage)

from fastapi import Form
from fastapi.responses import RedirectResponse

@app.api_route("/plugins/{plugin}/config", methods=["GET", "POST"], response_class=HTMLResponse)
async def plugin_config(request: Request, plugin: str, pipeline: str = "default"):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    message = None
    # Get default config structure from plugin
    try:
        mod = __import__(f"plugins.{plugin}", fromlist=["get_config_ui"])
        default_config = mod.get_config_ui()
    except Exception as e:
        default_config = {"error": str(e)}
    # On POST, update config in DB
    if request.method == "POST":
        form = await request.form()
        # Flatten form to dict, handle bools/ints
        new_config = {}
        for k, v in form.items():
            if v.lower() == "true":
                new_config[k] = True
            elif v.lower() == "false":
                new_config[k] = False
            else:
                try:
                    new_config[k] = int(v)
                except Exception:
                    new_config[k] = v
        try:
            plugin_config_repo.update_plugin_config(plugin, pipeline, new_config)
            message = "Configuration updated successfully."
        except Exception as e:
            message = f"Error updating config: {e}"
    # On GET or after POST, load config from DB or fallback to default
    config = plugin_config_repo.get_plugin_config(plugin, pipeline)
    if not config:
        config = default_config
    return templates.TemplateResponse(
        "plugin_config.html",
        {
            "request": request,
            "navbar": get_navbar(),
            "menu": get_menu(get_plugin_names()),
            "plugin": plugin,
            "config": config,
            "pipeline": pipeline,
            "message": message,
        }
    )

@app.get("/plugins/{plugin}/status", response_class=HTMLResponse)
def plugin_status(request: Request, plugin: str):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
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
from fastapi import Query

@app.get("/logs", response_class=HTMLResponse)
def logs_page(request: Request, 
              level: str = Query(None), 
              start: str = Query(None), 
              end: str = Query(None), 
              q: str = Query(None)):
    if not is_authenticated(request):
        return RedirectResponse("/", status_code=302)
    log_path = "logs/orchestrator.log"
    logs = []
    filters = {"level": level, "start": start, "end": end, "q": q}
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()[-5000:]  # Only look at last 5000 lines for perf
        filtered = []
        for line in reversed(lines):  # newest first
            # Level filter
            if level and (f" {level.upper()} " not in line):
                continue
            # Date filter (assumes ISO or similar date at start)
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
            # Keyword filter
            if q and q.lower() not in line.lower():
                continue
            filtered.append(line)
            if len(filtered) >= 200:
                break
        logs = [line for line in reversed(filtered) if line.strip()]  # restore to oldest-first, remove blanks
    except Exception as e:
        logs = [f"Error reading logs: {e}\n"]
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "navbar": get_navbar(),
            "menu": get_menu(get_plugin_names()),
            "logs": logs,
            "filters": filters,
        }
    )

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    if not is_authenticated(request):
        return HTMLResponse(
            """
            <h2>Login</h2>
            <form method='post' action='/login'>
                <input name='username' placeholder='Username' />
                <input name='password' type='password' placeholder='Password' />
                <button type='submit'>Login</button>
            </form>
            """,
            status_code=200,
        )
    pipelines = list(orchestrator.pipelines.keys())
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "navbar": get_navbar(),
            "menu": get_menu(get_plugin_names()),
            "pipelines": pipelines,
        }
    )

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    return HTMLResponse("<h2>Login failed</h2><a href='/'>Try again</a>", status_code=401)

@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)

class PipelineTrigger(BaseModel):
    pipeline: str

@app.post("/trigger")
def trigger_pipeline(request: Request, pipeline: str = Form(...)):
    require_auth(request)
    if pipeline not in orchestrator.pipelines:
        return HTMLResponse(f"<h2>Pipeline not found: {pipeline}</h2>", status_code=404)
    threading.Thread(target=orchestrator._run_pipeline, args=(pipeline,), daemon=True).start()
    return RedirectResponse("/", status_code=302)

@app.get("/pipelines")
def list_pipelines(request: Request):
    require_auth(request)
    return list(orchestrator.pipelines.keys())
