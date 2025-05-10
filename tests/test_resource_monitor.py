"""
Unit tests for services.resource_monitor
"""

from services.resource_monitor import ResourceMonitor


def test_resource_monitor_metrics():
    rm = ResourceMonitor()
    stats = rm.get_stats()
    assert isinstance(stats, dict)
    assert (
        "cpu" in stats
        and "memory" in stats
        and "disk" in stats
        and "db_health" in stats
    )


def test_get_db_health_error(monkeypatch):
    class BadClient:
        class admin:
            @staticmethod
            def command(arg):
                raise Exception("fail")

    monkeypatch.setattr(
        "services.resource_monitor.MongoClient", lambda uri, **kw: BadClient
    )
    mon = ResourceMonitor()
    result = mon._get_db_health()
    assert result["ok"] is False
    assert "fail" in result["error"]
