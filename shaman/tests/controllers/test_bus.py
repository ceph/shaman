import hmac
from hashlib import sha1


class TestBusApiController(object):

    def test_post_index_basic_auth(self, app):
        result = app.post_json('/api/bus/ceph/test', params={})
        assert result.status_int == 200

    def test_post_index_github_auth_fails(self, app):
        result = app.post_json(
            '/api/bus/ceph/test',
            headers={'X-Hub-Signature': 'fail'},
            params={},
            expect_errors=True
        )
        assert result.status_int == 401

    def test_post_index_github_auth_succeeds(self, app):
        signature = "sha1={}".format(hmac.new(b'secret', b'{}', sha1).hexdigest())
        result = app.post_json(
            '/api/bus/ceph/test',
            headers={'X-Hub-Signature': signature},
            params={},
        )
        assert result.status_int == 200
