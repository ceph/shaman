from shaman import models
import datetime


class TestRootController(object):

    def test_gets_five_days_of_area_data(self, session):
        result = session.app.get('/')
        # this is super naive but the list is really all a string
        # so JS can consume it
        assert len(result.namespace['area_data'].split(',')) == 10

    def test_gets_no_projects_by_defaut(self, session):
        result = session.app.get('/')
        assert result.namespace['projects'] == []

    def test_no_latest_repos(self, session):
        result = session.app.get('/')
        assert result.namespace['latest_repos'] == []

    def test_no_latest_builds(self, session):
        result = session.app.get('/')
        assert result.namespace['latest_builds'] == []

    def test_repos_from_today(self, session):
        models.Repo(
            project=models.Project(name='ceph'),
            distro="ubuntu",
            distro_version="xenial",
            status="ready")
        models.commit()
        result = session.app.get('/')
        now = datetime.datetime.now(datetime.timezone.utc)
        today_str = now.strftime('%Y-%m-%d')
        assert "'ceph': 1" in result.namespace['area_data']
        assert today_str in result.namespace['area_data']

    def test_no_builds_from_today(self, session):
        # create a build, no repos
        models.Build(project=models.Project(name='ceph'), status="ready")
        models.commit()
        result = session.app.get('/')
        assert "'ceph': 0" not in result.namespace['area_data']
