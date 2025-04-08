from shaman.models import Build, Project, commit


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

    def setup_method(self):
        self.data = get_build_data()

    def test_list_ref_by_id(self, app):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='master')
        Build(build_id=2, project=project, ref='master')
        Build(build_id=100, project=project, ref='master')
        commit()
        result = app.get('/builds/ceph/master/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'

    def test_list_builds_by_id(self, app):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='master')
        Build(build_id=2, project=project, ref='master')
        Build(build_id=100, project=project, ref='master')
        commit()
        result = app.get('/builds/ceph/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'

    def test_list_sha1s_by_id(self, app):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='master', sha1='1234')
        Build(build_id=2, project=project, ref='master', sha1='1234')
        Build(build_id=100, project=project, ref='master', sha1='1234')
        commit()
        result = app.get('/builds/ceph/master/1234/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'

    def test_list_flavors_by_id(self, app):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='master', sha1='1234', flavor='default')
        Build(build_id=2, project=project, ref='master', sha1='1234', flavor='default')
        Build(build_id=100, project=project, ref='master', sha1='1234', flavor='default')
        commit()
        result = app.get('/builds/ceph/master/1234/default/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'


class TestApiProjectController(object):
    
    def setup_method(self):
        self.data = get_build_data()

    def test_create_a_build(self, app):
        result = app.post_json('/api/builds/ceph/', params=self.data)
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

    def test_update_build(self, app):
        app.post_json('/api/builds/ceph/', params=self.data)
        data = self.data.copy()
        data['status'] = "completed"
        result = app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        build = Build.get(1)
        assert build.status == "completed"

    def test_update_build_same_url_different_sha1(self, app):
        # this tests the situation where a new jenkins instance
        # is spun up at the same URL and the jenkins urls are
        # now duplicating
        app.post_json('/api/builds/ceph/', params=self.data)
        data = self.data.copy()
        data['sha1'] = "new-sha1"
        result = app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        assert len(Build.query.all()) == 2

    def test_update_build_same_url_different_distro(self, app):
        data = self.data.copy()
        data['distro'] = 'centos'
        data['distro_version'] = '9'
        result = app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        assert len(Build.query.all()) == 1
        build1 = Build.query.all()[0]
        build1_url = build1.url
        assert build1.distro == 'centos'
        assert build1.distro_version == '9'
        data = self.data.copy()
        data['distro'] = 'ubuntu'
        data['distro_version'] = '24.04'
        result = app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        assert len(Build.query.all()) == 2
        build2 = Build.query.all()[1]
        assert build2.distro == 'ubuntu'
        assert build2.distro_version == '24.04'
        assert build1_url == build2.url

    def test_update_build_same_url_different_arch(self, app):
        data = self.data.copy()
        data['distro_arch'] = 'x86_64'
        result = app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        assert len(Build.query.all()) == 1
        build1 = Build.query.all()[0]
        build1_url = build1.url
        assert build1.distro_arch == 'x86_64'
        data = self.data.copy()
        data['distro_arch'] = 'arm64'
        result = app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        assert len(Build.query.all()) == 2
        build2 = Build.query.all()[1]
        assert build2.distro_arch == 'arm64'
        assert build1_url == build2.url

    def test_update_queued_build_creates_single_object(self, app):
        data = get_build_data(status='queued', url='jenkins.ceph.com/trigger')
        app.post_json('/api/builds/ceph/', params=data)
        data = get_build_data(status='completed')
        app.post_json('/api/builds/ceph/', params=data)
        assert len(Build.query.all()) == 1

    def test_update_queued_build_is_completed(self, app):
        data = get_build_data(status='queued', url='jenkins.ceph.com/trigger')
        app.post_json('/api/builds/ceph/', params=data)
        data = get_build_data(status='completed')
        app.post_json('/api/builds/ceph/', params=data)
        assert Build.get(1).status == 'completed'

    def test_lists_refs(self, app):
        app.post_json('/api/builds/ceph/', params=self.data)
        result = app.get('/api/builds/ceph/')
        assert "master" in result.json


class TestProjectsAPIController(object):

    def test_lists_projects_with_ref(self, app):
        app.post_json('/api/builds/ceph/', params=get_build_data())
        result = app.get('/api/builds/')
        assert 'ceph' in result.json
        assert result.json['ceph'][0] == "master"


class TestRefsAPIController(object):

    def test_lists_sha1s(self, app):
        app.post_json('/api/builds/ceph/', params=get_build_data())
        result = app.get('/api/builds/ceph/master/')
        assert 'sha1' in result.json


class TestSHA1APIController(object):

    def test_lists_builds(self, app):
        app.post_json('/api/builds/ceph/', params=get_build_data())
        result = app.get('/api/builds/ceph/master/sha1/')
        assert len(result.json) == 1
        assert result.json[0]["ref"] == "master"
        assert result.json[0]["sha1"] == "sha1"
