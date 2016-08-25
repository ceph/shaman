import datetime

from shaman import util
from shaman.models import Node

import py.test
from mock import patch


class TestIsNodeHealthy(object):

    @patch("shaman.util.requests.get")
    def test_node_is_healthy(self, m_get, session):
        m_get.return_value.ok = True
        node = Node("chacra.ceph.com")
        session.commit()
        assert util.is_node_healthy(node)

    @patch("shaman.util.requests.get")
    def test_last_check_is_updated(self, m_get, session):
        m_get.return_value.ok = True
        node = Node("chacra.ceph.com")
        last_check = datetime.datetime.now()
        node.last_check = datetime.datetime.now()
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert node.last_check.time() > last_check.time()

    @patch("shaman.util.requests.get")
    def test_down_count_is_cleared_when_healthy(self, m_get, session):
        m_get.return_value.ok = True
        node = Node("chacra.ceph.com")
        node.down_count = 2
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert node.down_count == 0

    @patch("shaman.util.requests.get")
    def test_node_is_not_healthy(self, m_get, session):
        m_get.return_value.ok = False
        node = Node("chacra.ceph.com")
        session.commit()
        assert not util.is_node_healthy(node)

    @patch("shaman.util.requests.get")
    def test_down_count_is_incremented(self, m_get, session):
        m_get.return_value.ok = False
        node = Node("chacra.ceph.com")
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert node.down_count == 1

    @patch("shaman.util.requests.get")
    def test_node_exceeds_down_count_limit(self, m_get, session):
        m_get.return_value.ok = False
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


class TestParseDistroRelease(object):

    @py.test.mark.parametrize('version,codename', [('14.04', 'trusty'), ('16.04', 'xenial'), ('16.10', 'yakkety')])
    def test_ubuntu_version_gets_both_parsed(self, version, codename):
        c, v = util.parse_distro_release(version, 'ubuntu')
        assert v == version
        assert c == codename

    @py.test.mark.parametrize('version,codename', [('14.04', 'trusty'), ('16.04', 'xenial'), ('16.10', 'yakkety')])
    def test_ubuntu_codename_gets_both_parsed(self, version, codename):
        c, v = util.parse_distro_release(codename, 'ubuntu')
        assert v == version
        assert c == codename

    def test_centos_gets_version_parsed(self):
        codename, version = util.parse_distro_release('7', 'centos')
        assert version == '7'
        assert codename is None

    def test_debian_gets_version_parsed(self):
        codename, version = util.parse_distro_release('wheezy', 'debian')
        assert version == '7'
        assert codename == 'wheezy'

    def test_unknown_alphabetic_gets_parsed(self):
        codename, version = util.parse_distro_release('peru', 'linux')
        assert version is None
        assert codename == 'peru'

    def test_unknown_numeric_gets_parsed(self):
        codename, version = util.parse_distro_release('100', 'linux')
        assert version == '100'
        assert codename is None


class TestParseDistroQuery(object):

    def test_parses_ubuntu_with_codename(self):
        result = util.parse_distro_query('ubuntu/xenial')
        assert result[0]['distro'] == 'ubuntu'
        assert result[0]['distro_codename'] == 'xenial'
        assert result[0]['distro_version'] == '16.04'

    def test_parses_with_arch(self):
        result = util.parse_distro_query('ubuntu/xenial/x86_64')
        assert result[0]['arch'] == "x86_64"

    def test_parses_without_arch(self):
        result = util.parse_distro_query('ubuntu/xenial')
        assert result[0]['arch'] is None

    def test_parses_ubuntu_with_version(self):
        result = util.parse_distro_query('ubuntu/14.04')
        assert result[0]['distro'] == 'ubuntu'
        assert result[0]['distro_codename'] == 'trusty'
        assert result[0]['distro_version'] == '14.04'

    def test_parses_centos_version_no_codename(self):
        result = util.parse_distro_query('centos/7')
        assert result[0]['distro'] == 'centos'
        assert result[0]['distro_codename'] is None
        assert result[0]['distro_version'] == '7'

    def test_parses_both_ubuntu_and_centos(self):
        result = util.parse_distro_query('ubuntu/xenial,centos/7')
        assert result[0]['distro'] == 'ubuntu'
        assert result[0]['distro_codename'] == 'xenial'
        assert result[0]['distro_version'] == '16.04'

        assert result[1]['distro'] == 'centos'
        assert result[1]['distro_codename'] is None
        assert result[1]['distro_version'] == '7'

    def test_barfs_when_no_slash(self):
        result = util.parse_distro_query('ubuntu/xenial,centos7')
        assert result[0]['distro'] == 'ubuntu'
        assert result[0]['distro_codename'] == 'xenial'
        assert result[0]['distro_version'] == '16.04'

        assert result[1]['distro'] == 'centos7'
        assert result[1]['distro_codename'] is None
        assert result[1]['distro_version'] is None
