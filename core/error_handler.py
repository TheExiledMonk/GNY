"""
ErrorHandler: Logs and handles plugin exceptions.
"""

from services.logger import get_logger


class ErrorHandler:
    """Handles and logs errors from plugins or core."""

    def __init__(self) -> None:
        self.logger = get_logger()

    def handle(self, error: Exception, context: dict = None) -> None:
        self.logger.error(
            {"event": "error_handler", "error": str(error), "context": context}
        )
        # Optionally: add more error handling logic
