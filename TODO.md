# TODO: Execution Orchestration Framework Implementation Guide

This checklist will guide you through implementing the orchestration framework and creating a sample plugin.

---

## 1. Project Structure Setup
- [x] Create the following folders:
  - `core/` (framework logic)
  - `plugins/` (all plugins)
  - `config/` (YAML config)
  - `db/` (DB helpers)
  - `services/` (shared services)
  - `ui/` (web interface)
  - `logs/` (runtime logs)
  - `tests/` (unit/integration tests)
- [x] Add `__init__.py` to each Python module folder.

## 2. Core Framework Implementation
- [x] Implement `run.py` (main entrypoint)
- [x] Implement `core/orchestrator.py` (pipeline runner)
- [x] Implement `core/hook_registry.py` (hook → plugin mapping)
- [x] Implement `core/plugin_executor.py` (executes plugin.run, error handling)
- [x] Implement `core/plugin_loader.py` (dynamic plugin loading)
- [x] Implement `core/context_builder.py` (builds execution context)
- [x] Implement `core/error_handler.py` (logs/handles plugin exceptions)
- [x] Implement `core/thread_manager.py` (pipeline thread management)

## 3. Config & DB Layer - (database is MongoDB)
- [x] Implement `config/pipelines.yaml` (pipeline definitions)
- [x] Implement `config/system.yaml` (global config)
- [x] Implement `db/config_storage.py` (loads/saves configs)
- [x] Implement `db/plugin_config_repo.py` (plugin config access)
- [x] Implement `db/run_history.py` (execution logs/status)
  
  **Note:**
  - Config/DB layer uses `pymongo` + `janus` for MongoDB access.
  - Fully threadsafe and async-compatible (supports both sync and asyncio code).
  - Plugins never access the DB directly; all access goes through this layer with system-wide cache and cache-invalidation on writes.

## 4. Services
- [x] Implement `services/config_manager.py` (unified config interface)
- [x] Implement `services/job_scheduler.py` (plugin job dispatcher, CPU usage)
- [x] Implement `services/logger.py` (structured logging + Slack)
- [x] Implement `services/resource_monitor.py` (CPU/mem/storage/usage/database_health stats)

  **Note:**
  - All services are threadsafe, structured, and follow project logging/testing rules.
  - Logging is always structured and written to logs/.

## 5. UI
- [x] Implement `ui/server.py` (Flask or FastAPI app)
- [x] Implement `ui/routes.py` (static plugin control routes)
- [x] Implement views: `dashboard.py`, `config_editor.py`, `logs.py`
- [x] Add templates: `index.html`, `plugin_panel.html`

  **Note:**
  - UI is Flask-based, modular, and ready for extension.
  - Uses Bootstrap for styling and a clean, modern look.

## 6. Logging
- [x] All logs go to `logs/` using structured logging (see user rules)
- [x] Ensure logging is multiprocess/thread safe

  **Note:**
  - Logging is structured (JSON), multiprocess/thread safe, and all logs are written to `logs/`.
  - Slack integration is supported for ERROR/FATAL events via environment variable.

## 7. Testing
- [x] Add unit tests for each module in `tests/`
- [x] Use test files: `test_orchestrator.py`, `test_plugins/`, `test_config_manager.py`, `test_scheduler.py`
- [ ] Integrate CI for linting (black, flake8, isort, ruff) and tests

  **Note:**
  - Unit tests for orchestrator, config manager, scheduler, and sample plugin are implemented in `tests/`.

## 8. Sample Plugin Implementation
- [x] Create `plugins/sample_plugin/`
  - [x] `__init__.py` with:
    - PLUGIN_NAME, HOOKS, PIPELINES, TAGS, VERSION, FAIL_HARD
    - `run(context, config)` function
    - Optional: `cancel`, `on_load`, `on_shutdown`, `get_metadata`, `get_config_ui`
  - [ ] (Optional) `utils.py`, `schema.py`, `resources/`
- [x] Register plugin in `core/hook_registry.py` (auto-mapped by orchestrator)
- [ ] Add sample config in DB/config
- [x] Add unit test in `tests/test_plugins/test_sample_plugin.py`

  **Note:**
  - Sample plugin is implemented and testable. Registration is handled automatically by orchestrator convention.

## 9. Example: Minimal Sample Plugin
```python
# plugins/sample_plugin/__init__.py
PLUGIN_NAME = "sample_plugin"
HOOKS = ["fetch_data"]
PIPELINES = ["default"]
TAGS = ["example"]
VERSION = "0.1.0"
FAIL_HARD = False

def run(context, config):
    log = context["services"]["log"]
    log.info({"event": "sample_plugin_run", "config": config})
    # Your plugin logic here
    return {"status": "success"}
```

---

## 10. Final Review
- [ ] Check compliance with coding rules (file/function size, typing, docstrings)
- [ ] Ensure no hardcoded secrets/configs
- [ ] Update README and onboarding docs
- [ ] Profile/monitor performance if needed

---

*Follow this checklist to ensure a clean, testable, and maintainable implementation. For questions, see `README.md` or ask for help!*
