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
