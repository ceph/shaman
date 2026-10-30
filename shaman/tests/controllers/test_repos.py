import datetime
import logging

from shaman.models import Project, Repo, commit


class TestApiController(object):

    def test_get_index_no_projects(self, app):
        result = app.get('/api/')
        assert result.status_int == 200
        assert result.json == {'repos': []}

    def test_get_index_shows_projects(self, app):
        Project("ceph")
        commit()
        result = app.get('/api/')
        assert result.status_int == 200
        assert result.json == {'repos': ['ceph']}


class TestProjectsController(object):

    def test_get_index_no_projects(self, app):
        result = app.get('/api/repos/')
        assert result.status_int == 200
        assert result.json == {}

    def test_list_a_project(self, app):
        Project("ceph")
        commit()
        result = app.get('/api/repos/')
        assert result.status_int == 200
        assert "ceph" in result.json.keys()

    def test_one_project_list_length(self, app):
        Project("ceph")
        commit()
        result = app.get('/api/repos/')
        assert result.status_int == 200
        assert len(result.json.keys()) == 1

    def test_list_a_few_projects(self, app):
        for p in range(20):
            Project('foo_%s' % p)
        commit()

        result = app.get('/api/repos/')
        assert result.status_int == 200
        assert len(result.json) == 20


class TestProjectController(object):

    def setup_method(self):
        self.repo_data = dict(
            ref="jewel",
            sha1="45107e21c568dd033c2f0a3107dec8f0b0e58374",
            flavor="default",
            distro="ubuntu",
            distro_version="xenial",
            chacra_url="chacra.ceph.com/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/",
            status="requested",
            extra=dict(version="10.2.2"),
        )

    def test_get_project_repos_is_empty(self, app):
        Project("ceph")
        commit()
        result = app.get('/api/repos/ceph/')
        assert result.json == []

    def test_get_project_with_a_repo(self, app):
        app.post_json('/api/repos/ceph/', params=self.repo_data)
        result = app.get('/api/repos/ceph/')
        assert result.json == ["jewel"]

    def test_create_a_repo(self, app):
        result = app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        repo = Repo.get(1)
        assert repo.ref == "jewel"
        assert repo.project.name == "ceph"
        assert repo.flavor == "default"
        assert repo.extra["version"] == "10.2.2"

    def test_create_a_repo_without_extra(self, app):
        data = self.repo_data.copy()
        del data["extra"]
        app.post_json('/api/repos/ceph/', params=data)
        assert Repo.get(1).extra == {}

    def test_update_without_extra_keeps_extra(self, app):
        app.post_json('/api/repos/ceph/', params=self.repo_data)
        new_data = self.repo_data.copy()
        new_data["status"] = "ready"
        del new_data["extra"]
        app.post_json('/api/repos/ceph/', params=new_data)
        repo = Repo.get(1)
        assert repo.status == "ready"
        assert repo.extra["version"] == "10.2.2"

    def test_update_with_extra_replaces_extra(self, app):
        app.post_json('/api/repos/ceph/', params=self.repo_data)
        new_data = self.repo_data.copy()
        new_data["extra"] = dict(version="10.2.3")
        app.post_json('/api/repos/ceph/', params=new_data)
        assert Repo.get(1).extra == {"version": "10.2.3"}

    def test_update_a_repo_status(self, app):
        result = app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        assert Repo.get(1).status == "requested"
        new_data = self.repo_data.copy()
        new_data["status"] = "ready"
        result = app.post_json('/api/repos/ceph/', params=new_data)
        assert Repo.get(1).status == "ready"

    def test_delete_a_repo(self, app):
        result = app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        assert Repo.get(1).status == "requested"
        new_data = self.repo_data.copy()
        new_data["status"] = "deleted"
        result = app.post_json('/api/repos/ceph/', params=new_data)
        commit()
        assert result.status_int == 200
        assert not Repo.get(1)

    def test_update_a_repo_url(self, app):
        result = app.post_json('/api/repos/ceph/', params=self.repo_data)
        assert result.status_int == 200
        assert not Repo.get(1).url
        new_data = self.repo_data.copy()
        new_data["url"] = "chacra.ceph.com/r/ceph/jewel/"
        result = app.post_json('/api/repos/ceph/', params=new_data)
        assert Repo.get(1).url == "chacra.ceph.com/r/ceph/jewel/"

    def test_add_repo_with_archs(self, app):
        data = self.repo_data.copy()
        data["archs"] = ["x86_64", "arm64"]
        app.post_json('/api/repos/ceph/', params=data)
        repo = Repo.get(1)
        assert len(repo.archs) == 2

    def test_update_repo_with_archs(self, app):
        data = self.repo_data.copy()
        data["archs"] = ["x86_64"]
        app.post_json('/api/repos/ceph/', params=data)
        repo = Repo.get(1)
        assert len(repo.archs) == 1
        data["archs"] = ["x86_64", "arm64"]
        app.post_json('/api/repos/ceph/', params=data)
        repo = Repo.get(1)
        assert len(repo.archs) == 2


class TestProjectControllerCallbackOrdering(object):
    """
    chacra posts one callback per status change from independent celery
    tasks, so they can arrive out of order. The repo's chacra 'modified'
    timestamp in the payload decides which update is the most recent.
    """

    def setup_method(self):
        self.repo_data = dict(
            ref="main",
            sha1="45107e21c568dd033c2f0a3107dec8f0b0e58374",
            flavor="default",
            distro="centos",
            distro_version="9",
            chacra_url="chacra.ceph.com/repos/ceph/main/45107e21c568dd033c2f0a3107dec8f0b0e58374/centos/9/flavors/default/",
            url="chacra.ceph.com/r/ceph/main/45107e21c568dd033c2f0a3107dec8f0b0e58374/centos/9/flavors/default/",
            status="requested",
            modified="2026-10-28 13:20:00.000000",
        )

    def post(self, app, **kw):
        data = self.repo_data.copy()
        data.update(kw)
        result = app.post_json('/api/repos/ceph/', params=data)
        assert result.status_int == 200
        return result

    def test_modified_is_stored(self, app):
        self.post(app)
        repo = Repo.get(1)
        assert repo.chacra_modified.replace(tzinfo=None) == datetime.datetime(2026, 10, 28, 13, 20)

    def test_stale_building_does_not_overwrite_ready(self, app):
        self.post(app, status="building", modified="2026-10-28 13:20:00.000000")
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000", archs=["x86_64"])
        self.post(app, status="building", modified="2026-10-28 13:20:00.000000", archs=["noarch"])
        repo = Repo.get(1)
        assert repo.status == "ready"
        assert [a.name for a in repo.archs] == ["x86_64"]
        assert repo.chacra_modified.replace(tzinfo=None) == datetime.datetime(2026, 10, 28, 13, 23, 4)

    def test_stale_queued_and_requested_are_ignored(self, app):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        self.post(app, status="queued", modified="2026-10-28 13:19:00.000000")
        self.post(app, status="requested", modified="2026-10-28 13:18:00.000000")
        assert Repo.get(1).status == "ready"

    def test_newer_update_is_applied(self, app):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        self.post(app, status="requested", modified="2026-10-28 14:00:00.000000")
        self.post(app, status="building", modified="2026-10-28 14:01:00.000000")
        assert Repo.get(1).status == "building"

    def test_same_modified_is_applied(self, app):
        # a new build request carries the modified of the last commit, which
        # is what the previous 'ready' reported
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        self.post(app, status="requested", modified="2026-10-28 13:23:04.000000")
        assert Repo.get(1).status == "requested"

    def test_aware_and_naive_timestamps_compare(self, app):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.123456+00:00")
        self.post(app, status="building", modified="2026-10-28 13:23:04.000000")
        assert Repo.get(1).status == "ready"
        self.post(app, status="requested", modified="2026-10-28 13:23:05.000000")
        assert Repo.get(1).status == "requested"

    def test_update_without_modified_is_applied(self, app):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        data = self.repo_data.copy()
        del data["modified"]
        data["status"] = "building"
        app.post_json('/api/repos/ceph/', params=data)
        repo = Repo.get(1)
        assert repo.status == "building"
        assert repo.chacra_modified.replace(tzinfo=None) == datetime.datetime(2026, 10, 28, 13, 23, 4)

    def test_stored_without_modified_then_with(self, app):
        data = self.repo_data.copy()
        del data["modified"]
        app.post_json('/api/repos/ceph/', params=data)
        assert Repo.get(1).chacra_modified is None
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        repo = Repo.get(1)
        assert repo.status == "ready"
        assert repo.chacra_modified is not None

    def test_unparseable_modified_is_applied(self, app):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        self.post(app, status="building", modified="yesterday")
        assert Repo.get(1).status == "building"

    def test_stale_deleted_still_deletes(self, app):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        self.post(app, status="deleted", modified="2026-10-28 13:20:00.000000")
        commit()
        assert not Repo.get(1)

    def test_ignored_update_is_logged(self, app, caplog):
        self.post(app, status="ready", modified="2026-10-28 13:23:04.000000")
        with caplog.at_level(logging.INFO, logger="shaman.controllers.api.repos.projects"):
            self.post(app, status="building", modified="2026-10-28 13:20:00.000000")
        assert "ignoring stale update" in caplog.text
        assert "'building'" in caplog.text


def base_repo_data(**kw):
    distro = kw.get('distro', 'ubuntu')
    distro_version = kw.get('distro_version', 'xenial')
    sha1 = kw.get('sha1', '45107e21c568dd033c2f0a3107dec8f0b0e58374')
    status = kw.get('status', 'ready')
    ref = kw.get('ref', 'jewel')
    archs = kw.get('archs', ["x86_64", "arm64"])
    flavor = kw.get('flavor', 'default')
    return dict(
        ref=ref,
        sha1=sha1,
        flavor=flavor,
        distro=distro,
        distro_version=distro_version,
        chacra_url="chacra.ceph.com/repos/ceph/jewel/{sha1}/{distro}/{distro_version}/flavors/{flavor}".format(
            sha1=sha1,
            distro=distro,
            distro_version=distro_version,
            flavor=flavor,
        ),
        url="chacra.ceph.com/r/ceph/{ref}/{sha1}/{distro}/{distro_version}/flavors/{flavor}".format(
            sha1=sha1,
            distro=distro,
            distro_version=distro_version,
            flavor=flavor,
            ref=ref,
        ),
        status=status,
        archs=archs,
    )


class TestRefController(object):

    def test_get_existing_ref(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/repos/ceph/jewel/')
        assert result.json == ["45107e21c568dd033c2f0a3107dec8f0b0e58374"]

    def test_same_refs_show_once(self, app):
        repo_1 = base_repo_data()
        repo_2 = base_repo_data()
        repo_2['chacra_url'] = 'https://localhost/'
        app.post_json('/api/repos/ceph/', params=repo_1)
        app.post_json('/api/repos/ceph/', params=repo_2)
        result = app.get('/api/repos/ceph/jewel/')
        assert result.json == ["45107e21c568dd033c2f0a3107dec8f0b0e58374"]


class TestSHA1Controller(object):

    def test_get_existing_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/')
        assert result.json == ["ubuntu"]

    def test_get_latest_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/repos/ceph/jewel/latest/')
        assert result.json == ["ubuntu"]

    def test_get_one_latest_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        app.post_json(
            '/api/repos/ceph/',
            params=base_repo_data(distro='centos', sha1='aaaaa')
        )
        result = app.get('/api/repos/ceph/jewel/latest/')
        assert result.json == ["centos"]

    def test_get_latest_sha1_requested_504s(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='requested'))
        result = app.get('/api/repos/ceph/jewel/latest/', expect_errors=True)
        assert result.status_int == 504


class TestDistroController(object):

    def test_get_existing_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get(
            '/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/'
        )
        assert result.json == ["xenial"]

    def test_same_distro_versions_show_once(self, app):
        repo_1 = base_repo_data()
        repo_2 = base_repo_data()
        repo_2['chacra_url'] = 'https://localhost/'
        app.post_json('/api/repos/ceph/', params=repo_1)
        app.post_json('/api/repos/ceph/', params=repo_2)
        result = app.get(
            '/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/'
        )
        assert result.json == ["xenial"]

    def test_repos_are_distinct(self, app):
        # note the sha1 is different for the only 'ubuntu' build
        repo_1 = base_repo_data(sha1='aaa', distro='ubuntu')
        repo_2 = base_repo_data(distro='debian')
        app.post_json('/api/repos/ceph/', params=repo_1)
        app.post_json('/api/repos/ceph/', params=repo_2)
        result = app.get(
            '/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/'
        )
        assert result.json == []


class TestDistroVersionController(object):

    def test_get_existing_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/')
        assert result.json[0]['distro_version'] == '16.04'
        assert result.json[0]['distro_codename'] == 'xenial'
        assert result.json[0]['flavor'] == 'default'

    def test_get_latest_repo_unavailable(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get(
            '/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/',
            params={'arch': 'i386'},
            expect_errors=True)
        assert result.status_int == 504

    def test_get_latest_repo_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_arch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/x86_64/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_directory_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', distro="centos", distro_version="7"))
        result = app.get('/api/repos/ceph/jewel/latest/centos/7/x86_64/noarch/repodata/repomd.xml', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_not_ready_for_distro(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="0"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="1", distro="test"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', sha1="1"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/?arch=x86_64', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_not_ready_for_flavor(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="1"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', sha1="2"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="2", flavor="notcmalloc"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_not_ready_for_default_flavor(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building'))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', flavor="notcmalloc"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/', expect_errors=True)
        assert result.status_int == 504

    def test_get_latest_repo_sha1_not_ready_for_custom_flavor(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', flavor="notcmalloc"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_ready_noarch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', archs=["noarch"]))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_valid_arch_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/?arch=arm64', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_valid_extra_arch_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/?arch=x86_64', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_invalid_extra_arch_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/repo/?arch=aarch64', expect_errors=True)
        assert result.status_int == 504


class TestFlavorsController(object):

    def test_get_existing_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/flavors/')
        assert result.json == ["default"]


class TestFlavorController(object):

    def test_get_existing_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/xenial/flavors/default/')
        assert result.json[0]['distro_codename'] == 'xenial'
        assert result.json[0]['distro_version'] == '16.04'
        assert result.json[0]['project'] == 'ceph'
        assert result.json[0]['status'] == 'ready'
        assert result.json[0]['distro'] == 'ubuntu'
        assert result.json[0]['ref'] == 'jewel'
        assert result.json[0]['sha1'] == '45107e21c568dd033c2f0a3107dec8f0b0e58374'
        assert sorted(result.json[0]['archs']) == sorted(["arm64", "x86_64"])

    def test_get_latest_repo_unavailable(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='requested'))
        result = app.get(
            '/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/',
            expect_errors=True
        )
        assert result.status_int == 504

    def test_get_latest_repo_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_arch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/x86_64/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_directory_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', distro="centos", distro_version="7"))
        result = app.get('/api/repos/ceph/jewel/latest/centos/7/flavors/default/x86_64/noarch/repodata/repomd.xml', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_not_ready_for_distro(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="0"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="1", distro="test"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', sha1="1"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/?arch=x86_64', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_not_ready_for_flavor(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="1"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', sha1="2"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="2", flavor="notcmalloc"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_ready_for_non_default_flavor(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="1", flavor="notcmalloc"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', sha1="2", flavor="notcmalloc"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', sha1="2"))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/notcmalloc/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_sha1_not_ready_for_non_default_flavor(self, app):
        # this tests for a regression where the latest sha1 that is picked for a distro does not
        # have a ready repo and a 504 is eventually given
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='building', flavor="notcmalloc"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/notcmalloc/repo/', expect_errors=True)
        assert result.status_int == 504

    def test_get_latest_repo_ready_noarch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready', archs=["noarch"]))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_valid_arch_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/?arch=arm64', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_valid_extra_arch_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/?arch=x86_64', expect_errors=True)
        assert result.status_int == 302

    def test_get_latest_repo_invalid_extra_arch_ready(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(status='ready'))
        result = app.get('/api/repos/ceph/jewel/latest/ubuntu/xenial/flavors/default/repo/?arch=aarch64', expect_errors=True)
        assert result.status_int == 504

