from shaman.models import Build


def get_build_data():
    return dict(
        ref="master",
        sha1="sha1",
        url="jenkins.ceph.com/build",
        log_url="jenkins.ceph.com/build/console",
        build_id="250",
        status="started",
        extra=dict(version="10.2.2"),
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
