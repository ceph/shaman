from shaman.models import Project


class TestProjectsController(object):

    def test_get_index_no_projects(self, session):
        result = session.app.get('/api/repos/')
        assert result.status_int == 200
        assert result.json == {}

    def test_list_a_project(self, session):
        Project("ceph")
        session.commit()
        result = session.app.get('/api/repos/')
        assert result.status_int == 200
        assert "ceph" in result.json.keys()

    def test_one_project_list_length(self, session):
        Project("ceph")
        session.commit()
        result = session.app.get('/api/repos/')
        assert result.status_int == 200
        assert len(result.json.keys()) == 1

    def test_list_a_few_projects(self, session):
        for p in range(20):
            Project('foo_%s' % p)
        session.commit()

        result = session.app.get('/api/repos/')
        assert result.status_int == 200
        assert len(result.json) == 20


class TestProjectController(object):

    def test_get_not_allowed(self, session):
        Project("ceph")
        session.commit()
        result = session.app.get('/api/repos/ceph/', expect_errors=True)
        assert result.status_int == 405
