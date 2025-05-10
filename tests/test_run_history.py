"""
Unit tests for db.run_history
"""

from db.run_history import RunHistory


class FakeStorage:
    def __init__(self):
        self.entries = []

    def insert(self, col, entry):
        self.entries.append(entry)

    def get(self, col, query=None):
        # Simple filter for pipeline
        if not query:
            return self.entries
        return [e for e in self.entries if all(e.get(k) == v for k, v in query.items())]


def test_log_and_get_runs():
    storage = FakeStorage()
    rh = RunHistory(storage)
    rh.log_run("pipeline", "plugin", "ok", {"foo": "bar"})
    runs = rh.get_runs("pipeline")
    assert runs and runs[0]["plugin"] == "plugin" and runs[0]["details"]["foo"] == "bar"
