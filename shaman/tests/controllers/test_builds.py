from shaman.models import Build, Project, commit


def get_build_data(**kw):
    ref= kw.get('ref', "main")
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

    def test_list_ref_by_id(self, session):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='main')
        Build(build_id=2, project=project, ref='main')
        Build(build_id=100, project=project, ref='main')
        commit()
        result = session.app.get('/builds/ceph/main/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'

    def test_list_builds_by_id(self, session):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='main')
        Build(build_id=2, project=project, ref='main')
        Build(build_id=100, project=project, ref='main')
        commit()
        result = session.app.get('/builds/ceph/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'

    def test_list_sha1s_by_id(self, session):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='main', sha1='1234')
        Build(build_id=2, project=project, ref='main', sha1='1234')
        Build(build_id=100, project=project, ref='main', sha1='1234')
        commit()
        result = session.app.get('/builds/ceph/main/1234/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'

    def test_list_flavors_by_id(self, session):
        project = Project(name='ceph')
        Build(build_id=1, project=project, ref='main', sha1='1234', flavor='default')
        Build(build_id=2, project=project, ref='main', sha1='1234', flavor='default')
        Build(build_id=100, project=project, ref='main', sha1='1234', flavor='default')
        commit()
        result = session.app.get('/builds/ceph/main/1234/default/')
        assert result.namespace['builds'][0].build_id == '100'
        assert result.namespace['builds'][1].build_id == '2'
        assert result.namespace['builds'][2].build_id == '1'


class TestApiProjectController(object):

    def setup(self):
        self.data = get_build_data()

    def test_create_a_build(self, session):
        result = session.app.post_json('/api/builds/ceph/', params=self.data)
        assert result.status_int == 200
        build = Build.get(1)
        assert build.ref == "main"
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

    def test_update_build_same_url_different_sha1(self, session):
        # this tests the situation where a new jenkins instance
        # is spun up at the same URL and the jenkins urls are
        # now duplicating
        session.app.post_json('/api/builds/ceph/', params=self.data)
        data = self.data.copy()
        data['sha1'] = "new-sha1"
        result = session.app.post_json('/api/builds/ceph/', params=data)
        assert result.status_int == 200
        assert len(Build.query.all()) == 2

    def test_update_queued_build_creates_single_object(self, session):
        data = get_build_data(status='queued', url='jenkins.ceph.com/trigger')
        session.app.post_json('/api/builds/ceph/', params=data)
        data = get_build_data(status='completed')
        session.app.post_json('/api/builds/ceph/', params=data)
        assert len(Build.query.all()) == 1

    def test_update_queued_build_is_completed(self, session):
        data = get_build_data(status='queued', url='jenkins.ceph.com/trigger')
        session.app.post_json('/api/builds/ceph/', params=data)
        data = get_build_data(status='completed')
        session.app.post_json('/api/builds/ceph/', params=data)
        assert Build.get(1).status == 'completed'

    def test_lists_refs(self, session):
        session.app.post_json('/api/builds/ceph/', params=self.data)
        result = session.app.get('/api/builds/ceph/')
        assert "main" in result.json


class TestProjectsAPIController(object):

    def test_lists_projects_with_ref(self, session):
        session.app.post_json('/api/builds/ceph/', params=get_build_data())
        result = session.app.get('/api/builds/')
        assert 'ceph' in result.json
        assert result.json['ceph'][0] == "main"


class TestRefsAPIController(object):

    def test_lists_sha1s(self, session):
        session.app.post_json('/api/builds/ceph/', params=get_build_data())
        result = session.app.get('/api/builds/ceph/main/')
        assert 'sha1' in result.json


class TestSHA1APIController(object):

    def test_lists_builds(self, session):
        session.app.post_json('/api/builds/ceph/', params=get_build_data())
        result = session.app.get('/api/builds/ceph/main/sha1/')
        assert len(result.json) == 1
        assert result.json[0]["ref"] == "main"
        assert result.json[0]["sha1"] == "sha1"
