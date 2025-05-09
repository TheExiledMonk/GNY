 Execution Orchestration Framework - Technical Documentation

This document defines the full technical specification of the Execution Orchestration Framework, designed to execute complex data processing pipelines using modular plugins, while offering full configurability, live control, and secure runtime isolation through a centralized system.

📌 System Overview

This framework supports:

Modular plugin-based processing

Named pipelines and named hooks

Plugin execution isolation and config

Web-based control panel and monitoring

Thread-based execution with CPU utilization control

Configurable plugin UI rendering

Slack notifications for error conditions

Centralized job handler for plugin-dispatched threaded jobs

🧱 System Components

1. Pipelines

A pipeline is a named sequence of hooks.

Pipelines can be scheduled or manually triggered.

Defined in pipelines.yaml or stored in a DB.

Example:

pipelines:
  default:
    schedule: "*/10 * * * *"
    hooks: ["fetch_data", "aggregate", "calculate_indicators"]
  historical:
    hooks: ["fetch_data"]
  repair:
    hooks: ["repair_missing", "reaggregate"]

2. Hooks

A hook is a named stage in a pipeline (e.g. fetch_data, aggregate).

Each hook can be mapped to one or more plugins.

The hook-plugin mapping is configured centrally.

3. Plugins

Each plugin is a self-contained unit that:

Registers to one or more hooks

Declares which pipelines it runs in

Provides a config schema for the UI

Can be dynamically loaded/reloaded without restarting Flask

May dispatch background jobs to the central thread handler

Plugin Metadata Example:

PLUGIN_NAME = "ccxt_fetcher"
HOOKS = ["fetch_data"]
PIPELINES = ["default", "historical"]
TAGS = ["fetcher"]
VERSION = "1.0.0"
FAIL_HARD = False

Optional Plugin Methods:

def run(context, config): ...
def cancel(): ...
def on_load(): ...
def on_shutdown(): ...
def get_metadata(): ...
def get_config_ui(): ...  # returns HTML or JSON schema

Plugins may request parallel job execution through context["services"]["jobs"], which dispatches tasks to the centralized thread manager that targets ~80% CPU utilization.

4. Plugin Configuration

Stored per-plugin, per-pipeline in a database.

Retrieved by the system before execution.

UI form is rendered from either a JSON schema or embedded HTML via:

GET /api/plugins/<plugin_id>/config_ui

GET /api/plugins/<plugin_id>/config

POST /api/plugins/<plugin_id>/config

5. ConfigManager

Centralized API for config access:

get_global_config()
get_pipeline_config(name)
get_plugin_config(plugin_id, pipeline)
update_plugin_config(plugin_id, pipeline, config)

No plugin or core module should access the DB directly.

6. Execution Context

Every plugin receives a shared context:

context = {
  "run_id": uuid4(),
  "start_time": datetime.utcnow(),
  "pipeline": "default",
  "hook": "fetch_data",
  "services": {
    "config": ConfigManager(),
    "db": MongoDBInterface(),
    "jobs": JobScheduler(),
    "log": UnifiedLogger(),
  }
}

7. Orchestrator

Runs pipelines in named threads. For each pipeline:

Resolves hook list

Resolves plugins assigned to hook/pipeline

Loads plugin config from DB

Executes each plugin with plugin.run(context, config)

Handles errors via error handler

8. Thread Model

One thread per pipeline

One thread for Flask UI

One thread for job scheduler

Optional thread for resource monitoring

Plugins can issue parallel jobs to the centralized job handler, which manages thread pools while maintaining CPU usage ~80%

9. Slack Integration

The UnifiedLogger supports Slack notifications:

ERROR level triggers error alert

FATAL level stops pipeline and sends fatal alert

Configured via environment variables or global config:

slack:
  webhook_url: "https://hooks.slack.com/services/..."
  alert_on_levels: ["ERROR", "FATAL"]

10. Plugin UI & Control

All plugin UIs are accessed via a unified route structure:

/api/plugins/<plugin_id>/config

/api/plugins/<plugin_id>/config_ui

/api/plugins/<plugin_id>/status

/api/plugins/<plugin_id>/trigger

/api/plugins/<plugin_id>/cancel

Flask only registers these static routes. The system uses a dispatcher to load plugin info dynamically.

🚫 Excluded Features

Multi-user support: not needed (single admin only)

Runtime timeouts: long-running jobs allowed, cancel manually

Sandbox security: not required (all plugins are internal)

Retry policy: handled by the plugin itself

✅ Supported Advanced Features

Dry-run execution mode

Plugin output schema validation

Plugin versioning

Plugin tagging & categorization

Hot plugin reload (no Flask restart)

Dev tools for reloading and testing plugins

Pipeline monitoring UI and logs

Manual cancel of plugin execution

Fault-tolerant execution with fail_hard option

This document defines the core contract all components and plugins must follow. Plugins must not access external resources directly — they must use the services provided via context["services"]. All config, logging, parallelization, and job scheduling are handled by the system, not the plugin.

Code Tree for Execution Orchestration Framework

This document outlines the full code structure for the Execution Orchestration Framework, organized into logical components based on responsibility. All files follow the core coding rules:

📏 Coding Rules

No module should exceed 250 lines

No loop or function should exceed 50 lines — use sub-functions to split

All imports should be at the top of each file

Separate modules by responsibility and layer (core, plugins, config, UI, etc.)

🌐 Root Structure

execution_framework/
├── run.py                      # Main entrypoint for the whole system
├── core/                       # Central framework logic
├── plugins/                    # All plugins live here (self-contained)
├── config/                     # Static YAML config files
├── db/                         # Database helpers and interfaces
├── services/                   # Shared framework services
├── ui/                         # Web interface
├── logs/                       # All runtime logs are written here
└── tests/                      # Unit and integration tests

🔧 core/

core/
├── orchestrator.py            # Runs pipelines, resolves hooks/plugins, passes context
├── hook_registry.py           # Mapping of hook names → plugin IDs
├── plugin_executor.py         # Executes plugin.run(), applies error handling
├── plugin_loader.py           # Dynamically loads plugin modules
├── context_builder.py         # Constructs the context object passed into plugins
├── error_handler.py           # Logs and handles plugin exceptions
├── thread_manager.py          # Starts/stops named pipeline threads

🔌 plugins/

plugins/
├── ccxt_fetcher/
│   ├── __init__.py            # Contains plugin metadata, run(), get_config_ui()
│   └── utils.py               # Fetch helpers, API wrappers
├── backfill_gaps/
│   └── __init__.py
├── ohlcv_aggregator/
│   └── __init__.py

Each plugin folder:

Must contain an __init__.py

Can optionally include utils.py, schema.py, resources/ etc.

⚙️ config/

config/
├── pipelines.yaml             # Defines all named pipelines
├── system.yaml                # Global config (e.g. CPU limit, exchanges, tokens)

🗄 db/

db/
├── config_storage.py          # Loads/saves plugin & global configs
├── plugin_config_repo.py      # Plugin config access layer
├── run_history.py             # Execution logs and status tracking

🛠 services/

services/
├── config_manager.py          # Unified interface for reading/updating all configs
├── job_scheduler.py           # Runs dispatched plugin jobs, manages CPU target usage
├── logger.py                  # Central structured logger + Slack integration
├── resource_monitor.py        # Optional: CPU/mem usage stats for UI

🌐 ui/

ui/
├── server.py                  # Flask or FastAPI app entrypoint
├── routes.py                  # Static plugin control routes
├── views/
│   ├── dashboard.py           # Plugin/pipeline overview
│   ├── config_editor.py       # Load/save plugin configs
│   ├── logs.py                # Runtime + error logs
├── templates/                 # Jinja or static HTML if needed
│   ├── index.html
│   ├── plugin_panel.html

🧪 tests/

tests/
├── test_orchestrator.py
├── test_plugins/
│   ├── test_ccxt_fetcher.py
├── test_config_manager.py
├── test_scheduler.py

This tree ensures strict separation of concerns, plugin isolation, and compliance with project coding rules. Each file must be kept minimal and focused, with additional logic broken into helper submodules or utilities as needed.