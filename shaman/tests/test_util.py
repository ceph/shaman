import datetime
import requests
from requests.exceptions import BaseHTTPError, RequestException

from shaman import util
from shaman.models import Node, Repo, Project, Arch

import pytest
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
    def test_healthy_is_true_when_rejoining_pool(self, m_get, session):
        """
        Tests the scenario where a node has been marked down,
        but is now up again and needs to rejoin the pool.
        """
        m_get.return_value.ok = True
        node = Node("chacra.ceph.com")
        node.down_count = 3
        node.healthy = False
        session.commit()
        util.is_node_healthy(node)
        node = Node.get(1)
        assert node.down_count == 0
        assert node.healthy

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


class RequestsResponse(object):

    def __init__(self, ok=True):
        self.ok = ok


def request_exception(exc=RequestException):
    raise exc


class TestCheckNodeHealth(object):

    def test_healthy(self, session, monkeypatch):
        response = RequestsResponse()
        monkeypatch.setattr(requests, "get", lambda *a, **kw: response)
        healthy = util.check_node_health(Node("chacra.ceph.com"))
        assert healthy is True

    def test_unhealthy(self, session, monkeypatch):
        response = RequestsResponse(ok=False)
        monkeypatch.setattr(requests, "get", lambda *a, **kw: response)
        healthy = util.check_node_health(Node("chacra.ceph.com"))
        assert healthy is False

    @pytest.mark.parametrize('exc', [BaseHTTPError, RequestException])
    def test_node_raises_requests_exception(self, exc, session, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **kw: request_exception(exc))
        healthy = util.check_node_health(Node("chacra.ceph.com"))
        assert healthy is False


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

    @pytest.mark.parametrize('version,codename', [('14.04', 'trusty'), ('16.04', 'xenial'), ('16.10', 'yakkety')])
    def test_ubuntu_version_gets_both_parsed(self, version, codename):
        c, v = util.parse_distro_release(version, 'ubuntu')
        assert v == version
        assert c == codename

    @pytest.mark.parametrize('version,codename', [('14.04', 'trusty'), ('16.04', 'xenial'), ('16.10', 'yakkety')])
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


def base_repo_data(**kw):
    distro = kw.get('distro', 'ubuntu')
    distro_version = kw.get('distro_version', 'xenial')
    sha1 = kw.get('sha1', '45107e21c568dd033c2f0a3107dec8f0b0e58374')
    status = kw.get('status', 'ready')
    ref = kw.get('ref', 'jewel')
    flavor = kw.get('flavor', 'default')
    return dict(
        ref=ref,
        sha1=sha1,
        flavor=flavor,
        distro=distro,
        distro_version=distro_version,
        chacra_url="chacra.ceph.com/repos/ceph/{ref}/{sha1}/{distro}/{distro_version}/flavors/{flavor}".format(
            sha1=sha1,
            distro=distro,
            distro_version=distro_version,
            flavor=flavor,
            ref=ref,
        ),
        url="chacra.ceph.com/r/ceph/{ref}/{sha1}/{distro}/{distro_version}/flavors/{flavor}".format(
            sha1=sha1,
            distro=distro,
            distro_version=distro_version,
            flavor=flavor,
            ref=ref,
        ),
        status=status,
    )


class TestGetRepoUrl(object):

    def setup_method(self):
        self.p = Project("ceph")
        self.data = base_repo_data()
        self.repo = Repo(self.p, **self.data)
        Arch(name="x86_64", repo=self.repo)

    def test_repo_file_is_true(self, session):
        session.commit()
        query = Repo.query.filter_by(status='ready')
        result = util.get_repo_url(query, 'x86_64', repo_file=True)
        assert result.endswith("/repo")

    def test_repo_file_is_false(self, session):
        session.commit()
        query = Repo.query.filter_by(status='ready')
        result = util.get_repo_url(query, 'x86_64', repo_file=False)
        assert result.startswith("chacra.ceph.com/r/")

    def test_arch_is_none(self, session):
        session.commit()
        query = Repo.query.filter_by(status='ready')
        result = util.get_repo_url(query, None, repo_file=False)
        assert result.startswith("chacra.ceph.com/r/")

    def test_repo_not_found(self, session):
        session.commit()
        query = Repo.query.filter_by(status='queued')
        result = util.get_repo_url(query, None, repo_file=False)
        assert not result

    def test_redirect_to_a_directory(self, session):
        session.commit()
        query = Repo.query.filter_by(status='ready')
        result = util.get_repo_url(query, 'x86_64', path=["SRPMS"], repo_file=False)
        assert result.endswith("/SRPMS")

    def test_redirect_to_a_directory_path(self, session):
        session.commit()
        query = Repo.query.filter_by(status='ready')
        result = util.get_repo_url(query, 'x86_64', path=["SRPMS", "repodata", "repomd.xml"], repo_file=False)
        assert result.endswith("/SRPMS/repodata/repomd.xml")
