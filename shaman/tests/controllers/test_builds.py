from shaman.models import Build


def get_build_data(**kw):
    ref= kw.get('ref', "master")
    sha1= kw.get('sha1', "sha1")
    url= kw.get('url', "jenkins.ceph.com/build")
    log_url= kw.get('log_url', "jenkins.ceph.com/build/console")
    build_id= kw.get('build_id', "250")
    status= kw.get('status', "started")
    extra=kw.get('extra', dict(version="10.2.2"))
    return dict(
        ref=ref,
        sha1=sha1,
        url=url,
        log_url=log_url,
        build_id=build_id,
        status=status,
        extra=extra,
    )


class TestProjectController(object):

    def setup(self):
        self.data = get_build_data()

    def test_create_a_build(self, session):
        result = session.app.post_json('/api/builds/ceph/', params=self.data)
        assert result.status_int == 200
        build = Build.get(1)
        assert build.ref == "master"
        assert build.project.name == "ceph"
        assert build.flavor == "default"
        assert build.sha1 == "sha1"
        assert build.url == "jenkins.ceph.com/build"
        assert build.log_url == "jenkins.ceph.com/build/console"
        assert build.extra["version"] == "10.2.2"
        assert not build.distro

    def test_update_build(self, session):
        session.app.post_json('/api/builds/ceph/', params=self.data)
        data = self.data.copy()
        data['status'] = "completed"
        result = session.app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        build = Build.get(1)
        assert build.status == "completed"
        assert build.completed

    def test_update_queued_build_creates_single_object(self, session):
        data = get_build_data(status='queued', url='jenkins.ceph.com/trigger')
        session.app.post_json('/api/builds/ceph/', params=data)
        data = get_build_data(status='completed')
        result = session.app.post_json('/api/builds/ceph/', params=data)
        assert len(Build.query.all()) == 1

    def test_update_queued_build_is_completed(self, session):
        data = get_build_data(status='queued', url='jenkins.ceph.com/trigger')
        session.app.post_json('/api/builds/ceph/', params=data)
        data = get_build_data(status='completed')
        result = session.app.post_json('/api/builds/ceph/', params=data)
        assert Build.get(1).status == 'completed'

    def test_lists_refs(self, session):
        session.app.post_json('/api/builds/ceph/', params=self.data)
        result = session.app.get('/api/builds/ceph/')
        assert "master" in result.json


class TestProjectsAPIController(object):

    def test_lists_projects_with_ref(self, session):
        session.app.post_json('/api/builds/ceph/', params=get_build_data())
        result = session.app.get('/api/builds/')
        assert 'ceph' in result.json
        assert result.json['ceph'][0] == "master"


class TestRefsAPIController(object):

    def test_lists_sha1s(self, session):
        session.app.post_json('/api/builds/ceph/', params=get_build_data())
        result = session.app.get('/api/builds/ceph/master/')
        assert 'sha1' in result.json


class TestSHA1APIController(object):

    def test_lists_builds(self, session):
        session.app.post_json('/api/builds/ceph/', params=get_build_data())
        result = session.app.get('/api/builds/ceph/master/sha1/')
        assert len(result.json) == 1
        assert result.json[0]["ref"] == "master"
        assert result.json[0]["sha1"] == "sha1"
