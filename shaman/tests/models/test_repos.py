from shaman.models import Repo, Project, Arch


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

    def test_can_create_with_arch(self, session):
        repo = Repo(self.p, **self.data)
        arch = Arch(name="x86_64", repo=repo)
        session.commit()
        repo = Repo.get(1)
        assert arch in repo.archs

    def test_can_create_with_many_archs(self, session):
        repo = Repo(self.p, **self.data)
        arch1 = Arch(name="x86_64", repo=repo)
        arch2 = Arch(name="arm64", repo=repo)
        session.commit()
        repo = Repo.get(1)
        assert arch1 in repo.archs
        assert arch2 in repo.archs

    def test_delete_will_delete_arch(self, session):
        repo = Repo(self.p, **self.data)
        Arch(name="x86_64", repo=repo)
        session.commit()
        repo = Repo.get(1)
        repo.delete()
        session.commit()
        assert not Repo.query.first()
        assert not Arch.query.first()
