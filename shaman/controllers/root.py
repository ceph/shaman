import datetime
from pecan import expose

from shaman.controllers import health
from shaman.controllers import builds as _builds
from shaman.controllers import search as _search

from shaman.controllers import api
from shaman.models import Project, Repo, Build
from sqlalchemy import and_

description = "shaman is the source of truth for the state of repositories on chacra nodes."


class APIController(object):
    @expose('json')
    def index(self):
        return dict(
            repos=[p.name for p in Project.query.all()],
        )

    repos = api.repos.ProjectsController()
    nodes = api.nodes.NodesController()
    search = _search.SearchController()
    builds = api.builds.ProjectsAPIController()


class RootController(object):

    @expose('jinja:index.html')
    def index(self):
        documentation = "https://github.com/ceph/shaman#shaman"
        projects = Project.query.all()
        now = datetime.datetime.utcnow()
        # five days worth of data
        periods = [
            (now - datetime.timedelta(days=day-1), now - datetime.timedelta(days=day+1))
            for day in range(1, 6)
        ]
        area_data = []

        for upper_range, lower_range in periods:
            day = lower_range + datetime.timedelta(days=1)
            day_data = {'period': day.strftime("%Y-%m-%d")}
            for project in projects:
                repository_count = Repo.filter_by(
                    project=project).filter(Repo.status == "ready").filter(
                        and_(Repo.modified > lower_range),
                        and_(Repo.modified < upper_range)
                    ).count()
                day_data[str(project.name)] = repository_count
            area_data.append(day_data)

        latest_repos = Repo.query.limit(10).all()
        latest_builds = Build.query.limit(10).all()

        return dict(
            description=description,
            documentation=documentation,
            area_data=str(area_data),
            projects=[str(p.name) for p in projects],
            latest_repos=latest_repos,
            latest_builds=latest_builds,
        )

    api = APIController()
    builds = _builds.BuildsController()
    _health = health.HealthController()
