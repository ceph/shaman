from shaman.controllers import health


class TestHealthController(object):

    def test_passes_health_check(self, app, monkeypatch):
        monkeypatch.setattr(health.checks, "is_healthy", lambda: True)
        result = app.get("/_health/")
        assert result.status_int == 204

    def test_fails_health_check(self, app, monkeypatch):
        monkeypatch.setattr(health.checks, "is_healthy", lambda: False)
        result = app.get("/_health/", expect_errors=True)
        assert result.status_int == 500
