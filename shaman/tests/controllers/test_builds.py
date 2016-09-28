from shaman.models import Project, Build


class TestProjectController(object):

    def setup(self):
        self.data = dict(
            ref="master",
            sha1="sha1",
            url="jenkins.ceph.com/build",
            log_url="jenkins.ceph.com/build/console",
            build_id="250",
            status="started",
            extra=dict(version="10.2.2"),
        )

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
