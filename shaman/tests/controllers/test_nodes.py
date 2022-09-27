from shaman.models import Node
from shaman.controllers.api import nodes


class TestNodeController(object):

    def test_get_no_nodes(self, session):
        result = session.app.get("/api/nodes/")
        assert result.status_int == 200
        assert result.json == {}

    def test_get_one_node(self, session):
        Node("chacra.ceph.com")
        session.commit()
        result = session.app.get("/api/nodes/")
        assert list(result.json.keys()) == ["chacra.ceph.com"]

    def test_get_multiple_nodes(self, session):
        Node("chacra01.ceph.com")
        Node("chacra02.ceph.com")
        session.commit()
        result = session.app.get("/api/nodes/")
        assert set(result.json.keys()) == set(["chacra01.ceph.com", "chacra02.ceph.com"])


def mock_check_node_health(healthy):
    def _check_node_health(node):
        return healthy

    return _check_node_health


class TestNodesContoller(object):

    def test_node_not_created(self, session):
        result = session.app.get("/api/nodes/chacra.ceph.com/", expect_errors=True)
        assert result.status_int == 404

    def test_create_node(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.host == "chacra.ceph.com"

    def test_node_fails_initial_check(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(False))
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.host == "chacra.ceph.com"
        assert not n.healthy

    def test_updates_last_check_time(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        last_check = n.last_check.time()
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.last_check.time() > last_check

    def test_updates_down_count(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        n.down_count = 2
        session.commit()
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.down_count == 0

    def test_updates_healthy(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        n.healthy = False
        session.commit()
        session.app.post("/api/nodes/chacra.ceph.com/")
        n = Node.get(1)
        assert n.healthy

    def test_get_next_node_succeeds(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        Node("chacra.ceph.com")
        session.commit()

        def _get_next_node():
            node = Node.get(1)
            return node

        monkeypatch.setattr(nodes, "get_next_node", _get_next_node)
        result = session.app.get("/api/nodes/next/")
        assert result.body.decode() == "https://chacra.ceph.com/"

    def test_get_next_node_fails(self, session, monkeypatch):
        monkeypatch.setattr(nodes, "check_node_health", mock_check_node_health(True))
        Node("chacra.ceph.com")
        session.commit()

        def _get_next_node():
            return None

        monkeypatch.setattr(nodes, "get_next_node", _get_next_node)
        result = session.app.get("/api/nodes/next/", expect_errors=True)
        assert result.status_int == 404
