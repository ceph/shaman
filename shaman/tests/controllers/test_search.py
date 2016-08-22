def base_repo_data(**kw):
    return dict(
        ref="jewel",
        sha1="45107e21c568dd033c2f0a3107dec8f0b0e58374",
        flavor="default",
        distro=kw.get("distro", "ubuntu"),
        distro_version=kw.get("distro_version", "xenial"),
        chacra_url="chacra.ceph.com/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/{}/{}/".format(
            kw.get("distro", "ubuntu"),
            kw.get("distro_version", "xenial"),
        ),
        status="requested",
    )


class TestSearchController(object):

    def test_get_no_repos(self, session):
        result = session.app.get('/api/search/', params={'project': 'ceph'})
        assert result.json == []

    def test_get_existing_repo(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/search/', params={'project': 'ceph'})
        assert result.json[0]['sha1'] == "45107e21c568dd033c2f0a3107dec8f0b0e58374"
        assert result.json[0]['ref'] == "jewel"

    def test_get_no_matching_repo_for_ref(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/search/', params={'project': 'ceph', 'ref': 'frufru'})
        assert result.json == []

    def test_project_can_be_omitted(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/search/', params={'ref': 'jewel'})
        assert result.json[0]['sha1'] == "45107e21c568dd033c2f0a3107dec8f0b0e58374"
        assert result.json[0]['ref'] == "jewel"

    def test_filter_by_single_distro(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        centos_data = base_repo_data(distro="centos", distro_version="7")
        centos_data["chacra_url"] = "centos"
        session.app.post_json('/api/repos/ceph/', params=centos_data)
        result = session.app.get('/api/search/', params={'distros': 'ubuntu/xenial'})
        assert len(result.json) == 1
        assert result.json[0]["distro"] == "ubuntu"
        assert result.json[0]["distro_codename"] == "xenial"

    def test_filter_by_multiple_distros(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        centos_data = base_repo_data(distro="centos", distro_version="7")
        session.app.post_json('/api/repos/ceph/', params=centos_data)
        jessie_data = base_repo_data(distro="debian", distro_version="jessie")
        session.app.post_json('/api/repos/ceph/', params=jessie_data)
        result = session.app.get('/api/search/', params={'distros': 'ubuntu/xenial,centos/7'})
        assert len(result.json) == 2
        assert result.json[0]["distro"] == "centos"
        assert result.json[0]["distro_version"] == "7"
        assert result.json[1]["distro"] == "ubuntu"
        assert result.json[1]["distro_codename"] == "xenial"
