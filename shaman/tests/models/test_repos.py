from shaman.models import Repo, Project, Arch, commit


class TestRepo(object):

    def setup_method(self):
        self.p = Project("ceph")
        self.data = dict(
            distro="ubuntu",
            distro_version="trusty",
        )

    def test_can_create(self, app):
        Repo(self.p, **self.data)
        commit()
        repo = Repo.get(1)
        assert repo.project.name == "ceph"
        assert repo.distro == "ubuntu"
        assert repo.distro_version == "trusty"
        assert repo.flavor == "default"

    def test_can_create_with_extra(self, app):
        r = Repo(self.p, **self.data)
        r.extra = dict(version="10.2.2")
        commit()
        repo = Repo.get(1)
        assert repo.extra['version'] == "10.2.2"

    def test_sets_modified(self, app):
        repo = Repo(self.p, **self.data)
        commit()
        assert repo.modified.timetuple()

    def test_update_changes_modified(self, app):
        repo = Repo(self.p, **self.data)
        initial_timestamp = repo.modified.time()
        commit()
        repo.distro = "centos"
        commit()
        assert initial_timestamp < repo.modified.time()

    def test_can_create_with_arch(self, app):
        repo = Repo(self.p, **self.data)
        arch = Arch(name="x86_64", repo=repo)
        commit()
        repo = Repo.get(1)
        assert arch in repo.archs

    def test_can_create_with_many_archs(self, app):
        repo = Repo(self.p, **self.data)
        arch1 = Arch(name="x86_64", repo=repo)
        arch2 = Arch(name="arm64", repo=repo)
        commit()
        repo = Repo.get(1)
        assert arch1 in repo.archs
        assert arch2 in repo.archs

    def test_delete_will_delete_arch(self, app):
        repo = Repo(self.p, **self.data)
        Arch(name="x86_64", repo=repo)
        commit()
        repo = Repo.get(1)
        repo.delete()
        commit()
        assert not Repo.query.first()
        assert not Arch.query.first()
