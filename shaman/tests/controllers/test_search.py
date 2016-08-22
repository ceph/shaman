def base_repo_data(**kw):
    ref = kw.get('ref', "jewel")
    sha1 = kw.get('sha1', "45107e21c568dd033c2f0a3107dec8f0b0e58374")
    distro = kw.get('distro', "ubuntu")
    distro_version = kw.get('distro_version', "xenial")
    return dict(
        ref=ref,
        sha1=sha1,
        flavor=kw.get('flavor', "default"),
        distro=distro,
        distro_version=distro_version,
        chacra_url=kw.get(
            'chacra_url',
            "chacra.ceph.com/repos/ceph/%s/%s/%s/%s/" % (
                ref, sha1, distro, distro_version
            )
        ),
        status=kw.get('status', "requested"),

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

    def test_filter_no_matching_distro(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get('/api/search/', params={'distros': 'centos/7'})
        assert result.json == []


class TestLatestSha1(object):

    def test_single_repo_is_returned(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get(
            '/api/search/',
            params={'project': 'ceph', 'sha1': 'latest'},
        )
        assert result.json[0]['sha1'] == "45107e21c568dd033c2f0a3107dec8f0b0e58374"

    def test_one_repo_does_not_match(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(sha1='111000'))
        result = session.app.get(
            '/api/search/',
            params={'project': 'ceph', 'sha1': 'latest'},
        )
        # this is fully enforcing, so we expect to get an empty list back
        assert len(result.json) == 1
        assert result.json[0]['sha1'] == '111000'

    def test_all_repos_match(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(distro_version='trusty'))
        result = session.app.get(
            '/api/search/',
            params={'project': 'ceph', 'sha1': 'latest'},
        )
        assert len(result.json) == 2

    def test_foo_distinct_repos_match(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(ref='master'))
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(distro='jessie'))
        session.app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = session.app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial', 'sha1': 'latest'},
        )
        assert len(result.json) == 1
        assert result.json[0]['ref'] == 'jewel'

    def test_distinct_repos_match_actual_sha1(self, session):
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(ref='master'))
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(distro='jessie'))
        session.app.post_json('/api/repos/ceph/', params=base_repo_data(sha1='aaaa'))
        result = session.app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial', 'sha1': 'aaaa'},
        )
        assert len(result.json) == 1
        assert result.json[0]['sha1'] == 'aaaa'

    def test_different_distros_match_latest_sha1(self, session):
        for sha1 in range(0, 3):
            session.app.post_json('/api/repos/ceph/', params=base_repo_data(sha1=str(sha1)))
            session.app.post_json(
                '/api/repos/ceph/',
                params=base_repo_data(
                    distro='solaris',
                    distro_version='10',
                    sha1=str(sha1))
            )
            session.app.post_json(
                '/api/repos/ceph/',
                params=base_repo_data(distro='centos', distro_version='7', sha1=str(sha1))
            )

        result = session.app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial,centos/7', 'sha1': 'latest'},
        )
        assert len(result.json) == 2
