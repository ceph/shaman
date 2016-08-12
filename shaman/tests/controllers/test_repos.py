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

    def test_get_project_repos_is_empty(self, session):
        Project("ceph")
        session.commit()
        result = session.app.get('/api/repos/ceph/')
        assert result.json == []

    def test_get_project_with_a_repo(self, session):
        session.app.post_json('/api/repos/ceph/', params=self.repo_data)
        result = session.app.get('/api/repos/ceph/')
        assert result.json == ["jewel"]

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


def base_repo_data():
    return dict(
        ref="jewel",
        sha1="45107e21c568dd033c2f0a3107dec8f0b0e58374",
        flavor="default",
        distro="ubuntu",
        distro_version="xenial",
        chacra_url="chacra.ceph.com/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/",
        status="requested",
    )


class TestRefController(object):

    def test_get_existing_ref(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/repos/ceph/jewel/')
        assert result.json == ["45107e21c568dd033c2f0a3107dec8f0b0e58374"]

    def test_same_refs_show_once(self, session):
        repo_1 = base_repo_data()
        repo_2 = base_repo_data()
        repo_2['chacra_url'] = 'https://localhost/'
        session.app.post_json('/api/repos/ceph/', params=repo_1)
        session.app.post_json('/api/repos/ceph/', params=repo_2)
        result = session.app.get('/api/repos/ceph/jewel/')
        assert result.json == ["45107e21c568dd033c2f0a3107dec8f0b0e58374"]

class TestSHA1Controller(object):

    def test_get_existing_sha1(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/')
        assert result.json == ["ubuntu"]


class TestDistroController(object):

    def test_get_existing_sha1(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/')
        assert result.json == ["xenial"]


class TestDistroVersionController(object):

    def test_get_existing_sha1(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/')
        assert result.json[0]['distro_version'] == 'xenial'
        assert result.json[0]['flavor'] == 'default'


class TestFlavorsController(object):

    def test_get_existing_sha1(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/flavors/')
        assert result.json == ["default"]


class TestFlavorController(object):

    def test_get_existing_sha1(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/flavors/default/')
        assert result.json[0]['distro_version'] == 'xenial'
        assert result.json[0]['status'] == 'requested'
        assert result.json[0]['distro'] == 'ubuntu'
        assert result.json[0]['ref'] == 'jewel'
        assert result.json[0]['sha1'] == '45107e21c568dd033c2f0a3107dec8f0b0e58374'
