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
