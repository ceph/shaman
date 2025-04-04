def base_repo_data(**kw):
    ref = kw.get('ref', "jewel")
    sha1 = kw.get('sha1', "45107e21c568dd033c2f0a3107dec8f0b0e58374")
    distro = kw.get('distro', "ubuntu")
    distro_version = kw.get('distro_version', "xenial")
    archs = kw.get('archs', ["x86_64"])
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
        archs=archs,
    )


class TestSearchController(object):

    def test_get_no_repos(self, app):
        result = app.get('/api/search/', params={'project': 'ceph'})
        assert result.json == []

    def test_get_existing_repo(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/search/', params={'project': 'ceph'})
        assert result.json[0]['sha1'] == "45107e21c568dd033c2f0a3107dec8f0b0e58374"
        assert result.json[0]['ref'] == "jewel"

    def test_get_no_matching_repo_for_ref(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/search/', params={'project': 'ceph', 'ref': 'frufru'})
        assert result.json == []

    def test_project_can_be_omitted(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/search/', params={'ref': 'jewel'})
        assert result.json[0]['sha1'] == "45107e21c568dd033c2f0a3107dec8f0b0e58374"
        assert result.json[0]['ref'] == "jewel"

    def test_filter_by_single_distro(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        centos_data = base_repo_data(distro="centos", distro_version="7")
        centos_data["chacra_url"] = "centos"
        app.post_json('/api/repos/ceph/', params=centos_data)
        result = app.get('/api/search/', params={'distros': 'ubuntu/xenial'})
        assert len(result.json) == 1
        assert result.json[0]["distro"] == "ubuntu"
        assert result.json[0]["distro_codename"] == "xenial"

    def test_filter_by_single_distro_and_arch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        centos_data = base_repo_data(distro="centos", distro_version="7")
        centos_data["chacra_url"] = "centos"
        app.post_json('/api/repos/ceph/', params=centos_data)
        result = app.get('/api/search/', params={'distros': 'ubuntu/xenial/x86_64'})
        assert len(result.json) == 1
        assert result.json[0]["distro"] == "ubuntu"
        assert result.json[0]["distro_codename"] == "xenial"
        assert result.json[0]["archs"] == ["x86_64"]

    def test_filter_by_same_distro_with_different_archs(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        app.post_json('/api/repos/ceph/', params=base_repo_data(archs=["arm64"], chacra_url="1"))
        result = app.get('/api/search/', params={'distros': 'ubuntu/xenial/x86_64'})
        assert len(result.json) == 1
        assert result.json[0]["distro"] == "ubuntu"
        assert result.json[0]["distro_codename"] == "xenial"
        assert result.json[0]["archs"] == ["x86_64"]

    def test_filter_by_single_distro_with_multiple_archs(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(archs=["x86_64", "arm64"]))
        centos_data = base_repo_data(distro="centos", distro_version="7")
        centos_data["chacra_url"] = "centos"
        app.post_json('/api/repos/ceph/', params=centos_data)
        result = app.get('/api/search/', params={'distros': 'ubuntu/xenial/x86_64'})
        assert len(result.json) == 1
        assert result.json[0]["distro"] == "ubuntu"
        assert result.json[0]["distro_codename"] == "xenial"
        assert "x86_64" in result.json[0]["archs"]

    def test_filter_by_multiple_distros(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        centos_data = base_repo_data(distro="centos", distro_version="7")
        app.post_json('/api/repos/ceph/', params=centos_data)
        jessie_data = base_repo_data(distro="debian", distro_version="jessie")
        app.post_json('/api/repos/ceph/', params=jessie_data)
        result = app.get('/api/search/', params={'distros': 'ubuntu/xenial,centos/7'})
        assert len(result.json) == 2
        assert result.json[0]["distro"] == "centos"
        assert result.json[0]["distro_version"] == "7"
        assert result.json[1]["distro"] == "ubuntu"
        assert result.json[1]["distro_codename"] == "xenial"

    def test_filter_by_multiple_distros_with_arch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        centos_data = base_repo_data(distro="centos", distro_version="7", archs=["arm64"])
        app.post_json('/api/repos/ceph/', params=centos_data)
        jessie_data = base_repo_data(distro="debian", distro_version="jessie")
        app.post_json('/api/repos/ceph/', params=jessie_data)
        result = app.get('/api/search/', params={'distros': 'ubuntu/xenial,centos/7/arm64'})
        assert len(result.json) == 2
        assert result.json[0]["distro"] == "centos"
        assert result.json[0]["distro_version"] == "7"
        assert result.json[0]["archs"] == ["arm64"]
        assert result.json[1]["distro"] == "ubuntu"
        assert result.json[1]["distro_codename"] == "xenial"

    def test_filter_no_matching_distro(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/search/', params={'distros': 'centos/7'})
        assert result.json == []

    def test_invalid_distros_query(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get('/api/search/', params={'distros': 'centos7,frufru'}, expect_errors=True)
        assert "Invalid version or codename for distro: centos7" in result.text


class TestLatestSha1(object):

    def test_single_repo_is_returned(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'sha1': 'latest'},
        )
        assert result.json[0]['sha1'] == "45107e21c568dd033c2f0a3107dec8f0b0e58374"

    def test_one_repo_does_not_match(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        app.post_json('/api/repos/ceph/', params=base_repo_data(sha1='111000'))
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'sha1': 'latest'},
        )
        # this is fully enforcing, so we expect to get an empty list back
        assert len(result.json) == 1
        assert result.json[0]['sha1'] == '111000'

    def test_all_repos_match(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        app.post_json('/api/repos/ceph/', params=base_repo_data(distro_version='trusty'))
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'sha1': 'latest'},
        )
        assert len(result.json) == 2

    def test_foo_distinct_repos_match(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(ref='master'))
        app.post_json('/api/repos/ceph/', params=base_repo_data(distro='jessie'))
        app.post_json('/api/repos/ceph/', params=base_repo_data())
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial', 'sha1': 'latest'},
        )
        assert len(result.json) == 1
        assert result.json[0]['ref'] == 'jewel'

    def test_distinct_repos_match_with_arch(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(archs=["x86_64"]))
        app.post_json('/api/repos/ceph/', params=base_repo_data(archs=["arm64"], chacra_url="1"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(archs=["foo"], chacra_url="2"))
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial/x86_64', 'sha1': 'latest'},
        )
        assert len(result.json) == 1
        assert result.json[0]['archs'] == ['x86_64']

    def test_distinct_repos_match_actual_sha1(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(ref='master'))
        app.post_json('/api/repos/ceph/', params=base_repo_data(distro='jessie'))
        app.post_json('/api/repos/ceph/', params=base_repo_data(sha1='aaaa'))
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial', 'sha1': 'aaaa'},
        )
        assert len(result.json) == 1
        assert result.json[0]['sha1'] == 'aaaa'

    def test_different_distros_match_latest_sha1(self, app):
        for sha1 in range(0, 3):
            app.post_json('/api/repos/ceph/', params=base_repo_data(sha1=str(sha1)))
            app.post_json(
                '/api/repos/ceph/',
                params=base_repo_data(
                    distro='solaris',
                    distro_version='10',
                    sha1=str(sha1))
            )
            app.post_json(
                '/api/repos/ceph/',
                params=base_repo_data(distro='centos', distro_version='7', sha1=str(sha1))
            )

        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial,centos/7', 'sha1': 'latest'},
        )
        assert len(result.json) == 2
        assert result.json[0]["sha1"] == '2'

    def test_does_not_find_common_sha1_across_distros(self, app):
        app.post_json('/api/repos/ceph/', params=base_repo_data(ref='master'))
        app.post_json('/api/repos/ceph/', params=base_repo_data(distro='centos', distro_version="7"))
        app.post_json('/api/repos/ceph/', params=base_repo_data(sha1="aaa"))
        result = app.get(
            '/api/search/',
            params={'project': 'ceph', 'distros': 'ubuntu/xenial,centos/7', 'sha1': 'latest', 'ref': 'jewel'},
        )
        assert result.json == []
