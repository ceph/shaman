from shaman.models import Repo, Project


class TestRepo(object):

    def setup(self):
        self.p = Project("ceph")
        self.data = dict(
            distro="ubuntu",
            distro_version="trusty",
        )

    def test_can_create(self, session):
        Repo(self.p, **self.data)
        session.commit()
        repo = Repo.get(1)
        assert repo.project.name == "ceph"
        assert repo.distro == "ubuntu"
        assert repo.distro_version == "trusty"
        assert repo.flavor == "default"

    def test_sets_modified(self, session):
        repo = Repo(self.p, **self.data)
        session.commit()
        assert repo.modified.timetuple()

    def test_update_changes_modified(self, session):
        repo = Repo(self.p, **self.data)
        initial_timestamp = repo.modified.time()
        session.commit()
        repo.distro = "centos"
        session.commit()
        assert initial_timestamp < repo.modified.time()
