from shaman.models import Node, commit
from shaman.controllers.api import nodes


class TestNodeController(object):

    def test_get_no_nodes(self, app):
        result = app.get("/api/nodes/")
        assert result.status_int == 200
        assert result.json == {}

    def test_get_one_node(self, app):
        Node("chacra.ceph.com")
        commit()
        result = app.get("/api/nodes/")
        assert list(result.json.keys()) == ["chacra.ceph.com"]

    def test_get_multiple_nodes(self, app):
        Node("chacra01.ceph.com")
        Node("chacra02.ceph.com")
        commit()
        result = app.get("/api/nodes/")
        assert set(result.json.keys()) == set(["chacra01.ceph.com", "chacra02.ceph.com"])


def mock_check_node_health(healthy):
    def _check_node_health(node):
        return healthy

    return _check_node_health


class TestNodesContoller(object):

    def test_node_not_created(self, app):
        result = app.get("/api/nodes/chacra.ceph.com/", expect_errors=True)
        assert result.status_int == 404

    def test_create_node(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.host == "chacra.ceph.com"

    def test_node_fails_initial_check(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(False))
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.host == "chacra.ceph.com"
        assert not n.healthy

    def test_updates_last_check_time(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        last_check = n.last_check.time()
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.last_check.time() > last_check

    def test_updates_down_count(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        n.down_count = 2
        commit()
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.down_count == 0

    def test_updates_healthy(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        n.healthy = False
        commit()
        app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.healthy

    def test_get_next_node_succeeds(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        Node("chacra.ceph.com")
        commit()

        def _get_next_node():
            node = Node.get(1)
            return node

        monkeypatch.setattr(nodes, "get_next_node", _get_next_node)
        result = app.get("/api/nodes/next/")
        assert result.body.decode() == "https://chacra.ceph.com/"

    def test_get_next_node_fails(self, app, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        Node("chacra.ceph.com")
        commit()

        def _get_next_node():
            return None

        monkeypatch.setattr(nodes, "get_next_node", _get_next_node)
        result = app.get("/api/nodes/next/", expect_errors=True)
        assert result.status_int == 404
