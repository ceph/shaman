from shaman.models import Project, Repo


class TestApiController(object):

    def test_get_index_no_projects(self, session):
        result = session.app.get('/api/')
        assert result.status_int == 200
        assert result.json == {'repos': []}

    def test_get_index_shows_projects(self, session):
        Project("ceph")
        session.commit()
        result = session.app.get('/api/')
        assert result.status_int == 200
        assert result.json == {'repos': ['ceph']}


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

    def setup(self):
        self.repo_data = dict(
            ref="jewel",
            sha1="45107e21c568dd033c2f0a3107dec8f0b0e58374",
            flavor="default",
            distro="ubuntu",
            distro_version="xenial",
            chacra_url="chacra.ceph.com/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/",
            status="requested",
        )

    def test_get_project_metadata(self, session):
        Project("ceph")
        session.commit()
        result = session.app.get('/api/repos/ceph/')
        assert result.json == {'name': 'ceph'}

    def test_create_a_repo(self, session):
        result = session.app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        repo = Repo.get(1)
        assert repo.ref == "jewel"
        assert repo.project.name == "ceph"
        assert repo.flavor == "default"

    def test_update_a_repo_status(self, session):
        result = session.app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        assert Repo.get(1).status == "requested"
        new_data = self.repo_data.copy()
        new_data["status"] = "ready"
        result = session.app.post_json('/api/repos/ceph/', params=new_data)
        assert Repo.get(1).status == "ready"

    def test_update_a_repo_url(self, session):
        result = session.app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        assert not Repo.get(1).url
        new_data = self.repo_data.copy()
        new_data["url"] = "chacra.ceph.com/r/ceph/jewel/"
        result = session.app.post_json('/api/repos/ceph/', params=new_data)
        assert Repo.get(1).url == "chacra.ceph.com/r/ceph/jewel/"
