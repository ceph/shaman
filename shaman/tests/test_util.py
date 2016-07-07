import datetime

from shaman import util
from shaman.models import Node

from mock import patch


class TestIsNodeHealthy(object):

    @patch("shaman.util.requests.get")
    def test_node_is_healthy(self, m_get, session):
        m_get.return_value.status_code = 200
        node = Node("chacra.ceph.com")
        session.commit()
        assert util.is_node_healthy(node)

    @patch("shaman.util.requests.get")
    def test_last_check_is_updated(self, m_get, session):
        m_get.return_value.status_code = 200
        node = Node("chacra.ceph.com")
        last_check = datetime.datetime.now()
        node.last_check = datetime.datetime.now()
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert node.last_check.time() > last_check.time()

    @patch("shaman.util.requests.get")
    def test_node_is_not_healthy(self, m_get, session):
        m_get.return_value.status_code = 500
        node = Node("chacra.ceph.com")
        session.commit()
        assert not util.is_node_healthy(node)

    @patch("shaman.util.requests.get")
    def test_down_count_is_incremented(self, m_get, session):
        m_get.return_value.status_code = 500
        node = Node("chacra.ceph.com")
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert node.down_count == 1

    @patch("shaman.util.requests.get")
    def test_node_exceeds_down_count_limit(self, m_get, session):
        m_get.return_value.status_code = 500
        node = Node("chacra.ceph.com")
        node.down_count = 2
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert not node.healthy


class TestGetNextNode(object):

    def test_no_nodes(self, session):
        assert not util.get_next_node()

    def test_finds_a_node(self, session, monkeypatch):
        monkeypatch.setattr(util, "is_node_healthy", lambda node: True)
        node = Node("chacra.ceph.com")
        session.commit()
        next_node = util.get_next_node()
        assert next_node == node

    def test_sets_last_used_on_selection(self, session, monkeypatch):
        monkeypatch.setattr(util, "is_node_healthy", lambda node: True)
        node = Node("chacra.ceph.com")
        session.commit()
        last_used = node.last_used
        next_node = util.get_next_node()
        assert next_node.last_used.time() > last_used.time()

    def test_no_healthy_nodes(self, session):
        node = Node("chacra.ceph.com")
        node.healthy = False
        session.commit()
        assert not util.get_next_node()

    def test_use_newly_added_node(self, session, monkeypatch):
        monkeypatch.setattr(util, "is_node_healthy", lambda node: True)
        n1 = Node("chacra01.ceph.com")
        n1.last_used = datetime.datetime.now()
        n2 = Node("chacra02.ceph.com")
        session.commit()
        assert n2 == util.get_next_node()

    def test_pick_last_used_node(self, session, monkeypatch):
        monkeypatch.setattr(util, "is_node_healthy", lambda node: True)
        n1 = Node("chacra01.ceph.com")
        n1.last_used = datetime.datetime.now() - datetime.timedelta(days=1)
        n2 = Node("chacra02.ceph.com")
        n2.last_used = datetime.datetime.now()
        session.commit()
        assert n1 == util.get_next_node()
