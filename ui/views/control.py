import logging
import os
import signal
from flask import Blueprint, jsonify, request

control_bp = Blueprint('control', __name__)

from flask import render_template

from ui.utils import get_navbar, get_menu, get_plugin_names

def control_view():
    return render_template(
        "control.html",
        navbar=get_navbar(),
        menu=get_menu(get_plugin_names()),
    )

def restart_view():
    return restart_server()

def stop_view():
    return stop_server()

@control_bp.route('/control/restart', methods=['POST'])
def restart_server():
    logging.getLogger("ui.control").info({"event": "server_restart"})
    os.kill(os.getpid(), signal.SIGHUP)
    return jsonify({"message": "Server restart triggered."})

@control_bp.route('/control/stop', methods=['POST'])
def stop_server():
    logging.getLogger("ui.control").info({"event": "server_stop"})
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"message": "Server shutdown triggered."})
