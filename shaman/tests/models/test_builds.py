from shaman.models import Project, Build, commit


class TestBuild(object):
    def setup_method(self):
        self.p = Project("ceph")
        self.data = dict(
            ref="master",
            sha1="sha1",
            url="jenkins.ceph.com/build",
            log_url="jenkins.ceph.com/build/console",
            build_id="250",
            status="failed",
        )

    def test_can_create(self, app):
        Build(self.p, **self.data)
        commit()
        b = Build.get(1)
        assert b.ref == "master"
        assert b.sha1 == "sha1"
        assert b.url == "jenkins.ceph.com/build"
        assert b.log_url == "jenkins.ceph.com/build/console"
        assert b.build_id == "250"
        assert b.status == "failed"

    def test_distro_can_be_null(self, app):
        Build(self.p, **self.data)
        commit()
        b = Build.get(1)
        assert not b.distro

    def test_distro_version_can_be_null(self, app):
        Build(self.p, **self.data)
        commit()
        b = Build.get(1)
        assert not b.distro_version

    def test_can_create_with_extra(self, app):
        b = Build(self.p, **self.data)
        b.extra = dict(version="10.2.2")
        commit()
        build = Build.get(1)
        assert build.extra['version'] == "10.2.2"

    def test_sets_modified(self, app):
        build = Build(self.p, **self.data)
        commit()
        assert build.modified.timetuple()

    def test_update_changes_modified(self, app):
        build = Build(self.p, **self.data)
        initial_timestamp = build.modified.time()
        commit()
        build.distro = "centos"
        commit()
        assert initial_timestamp < build.modified.time()


class TestBuildUrl(object):

    def setup_method(self):
        self.p = Project("ceph")
        self.data = dict(
            ref="master",
            sha1="sha1",
            url="jenkins.ceph.com/build",
            log_url="jenkins.ceph.com/build/console",
            build_id="250",
            status="failed",
        )

    def test_default_gives_full_url(self, app):
        Build(self.p, **self.data)
        commit()
        result = Build.get(1).get_url()
        assert result == '/builds/ceph/master/sha1/default/1/'

    def test_by_ref(self, app):
        build = Build(self.p, **self.data)
        commit()
        result = build.get_url('ref')
        assert result == '/builds/ceph/master/'

    def test_by_sha1(self, app):
        build = Build(self.p, **self.data)
        commit()
        result = build.get_url('sha1')
        assert result == '/builds/ceph/master/sha1/'

    def test_up_to_project(self, app):
        build = Build(self.p, **self.data)
        commit()
        result = build.get_url('project')
        assert result == '/builds/ceph/'
