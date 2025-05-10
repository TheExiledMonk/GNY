"""
Gather Plugin Config UI logic - clean separation from handler and HTML.
"""
from typing import List, Dict, Any
from fastapi import Request
from jinja2 import Environment, FileSystemLoader
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def render_config_ui(context: Dict[str, Any]) -> str:
    template = env.get_template("config.html")
    return template.render(**context)

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from typing import Any, Dict
from .tokenpair_utils import get_all_exchange_tokenpairs
from .core import get_default_config, get_supported_exchanges, get_tokens_for_exchanges, get_stablecoins_for_exchanges
import logging


def ensure_list(val: object) -> list:
    if isinstance(val, list):
        return val
    if val is None:
        return []
    return [val]

def normalize_config(config: dict) -> dict:
    for k, v in get_default_config().items():
        if k not in config:
            config[k] = v
    config["exchanges"] = ensure_list(config.get("exchanges"))
    config["tokens"] = ensure_list(config.get("tokens"))
    config["stablecoins"] = ensure_list(config.get("stablecoins"))
    if "exchange_database" not in config:
        config["exchange_database"] = ""
    if "indicator_database" not in config:
        config["indicator_database"] = ""
    return config

def get_intervals_str_and_update(config: dict) -> str:
    intervals_val = config.get("intervals")
    if isinstance(intervals_val, dict):
        intervals_str = ",".join(sorted(intervals_val.keys()))
        config["intervals"] = list(intervals_val.keys())
    elif isinstance(intervals_val, list):
        intervals_str = ",".join(str(i) for i in intervals_val if i)
    elif isinstance(intervals_val, str):
        intervals_str = intervals_val
        config["intervals"] = [i.strip() for i in intervals_val.split(",") if i.strip()]
    else:
        intervals_str = ""
    return intervals_str

def process_form(form, config: dict) -> dict:
    new_config = dict(config)
    # Standard fields
    for key in ["exchanges", "tokens", "stablecoins", "base_stablecoin", "intervals", "exchange_database", "indicator_database"]:
        if key in ["exchanges", "tokens", "stablecoins"]:
            value = form.getlist(key)
            new_config[key] = value if value else []
        elif key == "intervals":
            value = form.get(key)
            if value:
                new_config[key] = [i.strip() for i in value.split(",") if i.strip()]
            else:
                new_config[key] = []
        else:
            value = form.get(key)
            new_config[key] = value
    if "pipeline" in new_config:
        del new_config["pipeline"]
    return new_config

def update_tokenpairs(new_config: dict) -> None:
    new_config["exchange_tokenpairs"] = get_all_exchange_tokenpairs(
        new_config.get("exchanges", []),
        new_config.get("tokens", []),
        new_config.get("stablecoins", []),
    )

def build_context(request, config, pipeline, message, all_exchanges, all_tokens, all_stablecoins, intervals_str) -> dict:
    return {
        "request": request,
        "plugin": "gather_plugin",
        "config": config,
        "pipeline": pipeline,
        "message": message,
        "all_exchanges": all_exchanges,
        "all_tokens": all_tokens,
        "all_stablecoins": all_stablecoins,
        "intervals_str": intervals_str,
    }

def handle_config_request(
    request,
    config: dict,
    pipeline: str,
    message: Any,
    plugin_config_repo: Any,
) -> str:
    """
    Handles GET/POST and rendering for plugin config UI.
    All config reads/writes MUST use plugin_config_repo as the source of truth.
    The only use of get_default_config() is to fill missing keys, never to overwrite user config.
    """
    # Always use global config (no pipeline key), to match how config is saved
    config = plugin_config_repo.get_plugin_config("gather_plugin", None)
    if config is None or not isinstance(config, dict):
        config = {}
    config = normalize_config(config)
    selected_exchanges = config["exchanges"]
    all_exchanges = get_supported_exchanges()
    all_tokens = get_tokens_for_exchanges(selected_exchanges) if selected_exchanges else []
    all_stablecoins = get_stablecoins_for_exchanges(selected_exchanges) if selected_exchanges else []
    intervals_str = get_intervals_str_and_update(config)
    ctx = build_context(request, config, pipeline, message, all_exchanges, all_tokens, all_stablecoins, intervals_str)

    if request.method == "POST":
        logging.getLogger("gather_plugin").info({"event": "post_received"})
        form = request.form
        logging.getLogger("gather_plugin").info({"event": "form_parsed", "form": dict(form)})
        action = form.get("action")
        new_config = process_form(form, config)
        update_tokenpairs(new_config)
        plugin_config_repo.update_plugin_config("gather_plugin", None, new_config)
        config = new_config
        if action == "reload_tokens":
            selected_exchanges = new_config["exchanges"]
            all_tokens = get_tokens_for_exchanges(selected_exchanges) if selected_exchanges else []
            all_stablecoins = get_stablecoins_for_exchanges(selected_exchanges) if selected_exchanges else []
            ctx["all_tokens"] = all_tokens
            ctx["all_stablecoins"] = all_stablecoins
            ctx["config"] = new_config
    ctx["exchange_tokenpairs"] = config.get("exchange_tokenpairs", {})
    return render_config_ui(ctx)


gather_config_router = APIRouter()

gather_config_router.add_api_route(
    "/config",
    handle_config_request,
    methods=["GET", "POST"],
    response_class=HTMLResponse,
)
