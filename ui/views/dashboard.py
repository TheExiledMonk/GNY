"""
dashboard.py: Plugin/pipeline overview view.
"""
from flask import render_template
from core.orchestrator import Orchestrator
from services.api_server import get_menu, get_navbar, get_plugin_names

def dashboard_view():
    from services.api_server import is_authenticated
    if not is_authenticated():
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
    pipelines = list(orchestrator.pipelines.keys())
    navbar = get_navbar()
    menu = get_menu(get_plugin_names())
    return render_template(
        "dashboard.html",
        pipelines=pipelines,
        navbar=navbar,
        menu=menu
    )
