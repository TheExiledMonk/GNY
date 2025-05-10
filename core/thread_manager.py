"""
ThreadManager: Starts/stops named pipeline threads.
"""

from threading import Thread
from typing import Any, Callable, Dict


class ThreadManager:
    """Manages threads and their controls for each pipeline."""

    def __init__(self) -> None:
        # Store: name -> {"thread": Thread, "control": Any}
        self.threads: Dict[str, Dict[str, Any]] = {}

    def start_pipeline_thread(
        self, name: str, target: Callable, control: Any, *args, **kwargs
    ) -> None:
        """
        Start a pipeline thread with a control object (must support pause/resume/cancel).
        """
        thread = Thread(target=target, args=args, kwargs=kwargs, name=name)
        thread.daemon = True
        thread.start()
        self.threads[name] = {"thread": thread, "control": control}

    def pause_pipeline_thread(self, name: str) -> None:
        """
        Pause the pipeline thread using its control object.
        """
        if name in self.threads:
            self.threads[name]["control"].pause()

    def resume_pipeline_thread(self, name: str) -> None:
        """
        Resume the pipeline thread using its control object.
        """
        if name in self.threads:
            self.threads[name]["control"].resume()

    def cancel_pipeline_thread(self, name: str) -> None:
        """
        Cancel (request stop) the pipeline thread using its control object, then join and remove it.
        """
        if name in self.threads:
            self.threads[name]["control"].cancel()
            self.stop_pipeline_thread(name)

    def stop_pipeline_thread(self, name: str) -> None:
        """
        Join and remove the pipeline thread.
        """
        if name in self.threads:
            thread = self.threads[name]["thread"]
            thread.join(timeout=5)
            del self.threads[name]
