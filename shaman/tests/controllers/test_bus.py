import hmac
from hashlib import sha1


class TestBusApiController(object):

    def test_post_index_basic_auth(self, session):
        result = session.app.post_json('/api/bus/ceph/test', params={})
        assert result.status_int == 200

    def test_post_index_github_auth_fails(self, session):
        result = session.app.post_json(
            '/api/bus/ceph/test',
            headers={'X-Hub-Signature': 'fail'},
            params={},
            expect_errors=True
        )
        assert result.status_int == 401

    def test_post_index_github_auth_succeeds(self, session):
        signature = hmac.new('secret', '{}', sha1).hexdigest()
        result = session.app.post_json(
            '/api/bus/ceph/test',
            headers={'X-Hub-Signature': signature},
            params={},
            expect_errors=True
        )
        assert result.status_int == 401
