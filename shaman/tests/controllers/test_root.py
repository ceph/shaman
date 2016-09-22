

class TestRootController(object):

    def test_gets_five_days_of_area_data(self, session):
        result = session.app.get('/')
        # this is super naive but the list is really all a string
        # so JS can consume it
        assert len(result.namespace['area_data'].split(',')) == 5

    def test_gets_no_projects_by_defaut(self, session):
        result = session.app.get('/')
        assert result.namespace['projects'] == []

    def test_no_latest_repos(self, session):
        result = session.app.get('/')
        assert result.namespace['latest_repos'] == []

    def test_no_latest_builds(self, session):
        result = session.app.get('/')
        assert result.namespace['latest_builds'] == []
