"""
Framework Check Plugin: Scans core modules and plugins for health, emits results to context for downstream inspection.
"""

import importlib
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict

from db.config_storage import ConfigStorage

from .thread_lifecycle_test import InteractiveLifecycleWorker, LifecycleWorker
from .threaded_db_test import db_worker


def run(
    context: Dict[str, Any], config: Dict[str, Any], pipeline: str
) -> Dict[str, Any]:
    """
    Main entry point for the framework check plugin.
    Scans core modules and plugins, checks for importability and key symbols, and emits results in context.
    Also spawns 5 threads that perform insert, update, get, and delete DB operations.
    Always returns the context and framework_check result, even on error.
    """
    result = {
        "core": {},
        "plugins": {},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    try:
        core_modules = [
            ("core.context_builder", ["build_context"]),
            ("core.error_handler", []),
            ("core.hook_registry", ["HookRegistry"]),
            ("core.orchestrator", ["Orchestrator"]),
            ("core.plugin_executor", ["PluginExecutor"]),
            ("core.plugin_loader", ["PluginLoader"]),
            ("core.thread_manager", ["ThreadManager"]),
        ]
        plugin_modules = [
            ("plugins.debug_plugin.__init__", ["run"]),
            ("plugins.gather_plugin.__init__", ["run"]),
            ("plugins.sample_plugin.__init__", ["run"]),
        ]
        # Check core modules
        for mod_name, symbols in core_modules:
            mod_result = {"import": False}
            try:
                mod = importlib.import_module(mod_name)
                mod_result["import"] = True
                for sym in symbols:
                    mod_result[sym] = hasattr(mod, sym)
            except Exception as e:
                mod_result["error"] = str(e)
            result["core"][mod_name] = mod_result
        # Check plugins
        for mod_name, symbols in plugin_modules:
            mod_result = {"import": False}
            try:
                mod = importlib.import_module(mod_name)
                mod_result["import"] = True
                for sym in symbols:
                    mod_result[sym] = hasattr(mod, sym)
            except Exception as e:
                mod_result["error"] = str(e)
            result["plugins"][mod_name] = mod_result
        # Threaded DB test
        db_results = {}
        threads = []
        try:
            storage = ConfigStorage()
            for i in range(5):
                t = threading.Thread(
                    target=db_worker, args=(storage, i, db_results), daemon=True
                )
                threads.append(t)
                t.start()
            for t in threads:
                t.join(timeout=5)
        except Exception as e:
            db_results["error"] = str(e)
        result["threaded_db"] = db_results
        # Thread lifecycle test (start, pause, resume, cancel)
        lifecycle_results = {}
        try:
            worker = LifecycleWorker()
            thread = threading.Thread(
                target=worker.run_test, args=(lifecycle_results,), daemon=True
            )
            thread.start()
            import time

            time.sleep(0.1)
            worker.pause()
            time.sleep(0.05)
            worker.resume()
            time.sleep(0.1)
            worker.pause()
            time.sleep(0.05)
            worker.resume()
            time.sleep(0.05)
            worker.cancel()
            thread.join(timeout=2)
            lifecycle_results["thread_alive"] = thread.is_alive()
        except Exception as e:
            lifecycle_results["error"] = str(e)
        result["thread_lifecycle"] = lifecycle_results
        # Deliberate error tests for plugin isolation
        deliberate_errors = {}
        try:
            _ = 1 / 0
        except Exception as e:
            deliberate_errors["division_by_zero"] = str(e)
        try:
            import not_a_real_module
        except Exception as e:
            deliberate_errors["import_error"] = str(e)
        try:
            x = None
            x.attribute_that_does_not_exist
        except Exception as e:
            deliberate_errors["attribute_error"] = str(e)
        finally:
            result["deliberate_errors"] = deliberate_errors
        # Interactive lifecycle worker for UI testing
        try:
            if "jobs" not in context:
                context["jobs"] = {}
            jobs_dict = context["jobs"]
            job_id = "interactive_lifecycle_test"
            from core.orchestrator import orchestrator
            # Check if the job is already tracked and thread is alive
            thread_info = orchestrator.thread_manager.threads.get(job_id)
            thread_alive = False
            if thread_info and thread_info.get("thread") and thread_info["thread"].is_alive():
                thread_alive = True
            if not thread_alive:
                worker = InteractiveLifecycleWorker(jobs_dict, job_id)
                orchestrator.thread_manager.start_pipeline_thread(
                    job_id, worker.run, worker
                )
                print(f"[framework_check_plugin] Started InteractiveLifecycleWorker job: {job_id}")
                print(f"[DEBUG] sys.modules['core.orchestrator'] id: {id(sys.modules['core.orchestrator'])}")
                print(f"[DEBUG] orchestrator id: {id(orchestrator)} thread_manager id: {id(orchestrator.thread_manager)} (plugin)")
                jobs_dict[job_id] = {"status": "started", "timestamp": time.time()}
            else:
                print(f"[framework_check_plugin] InteractiveLifecycleWorker job already running: {job_id}")
            print("[framework_check_plugin] Registered jobs:", list(orchestrator.thread_manager.threads.keys()))
            # Block until the job is finished (cancelled or completed)
            thread = orchestrator.thread_manager.threads[job_id]["thread"]
            print(f"[framework_check_plugin] Waiting for job {job_id} to finish...")
            thread.join()  # Block until the thread is done
            print(f"[framework_check_plugin] Job {job_id} finished.")
            result["interactive_lifecycle_job"] = jobs_dict[job_id]
        except Exception as e:
            result["interactive_lifecycle_job_error"] = str(e)
        finally:
            pass
    except Exception as e:
        # Top-level catch: ensure context is always returned
        result["framework_check_top_error"] = str(e)
    finally:
        # Always add to context and return
        context = dict(context)
        context["framework_check"] = result
        return {"status": "checked", "context": context, "framework_check": result}
