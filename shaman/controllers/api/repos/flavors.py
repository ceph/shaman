from pecan import request, expose, abort
from shaman.models import Project, Repo
from sqlalchemy import desc


class FlavorController(object):

    def __init__(self, flavor_name):
        self.flavor_name = flavor_name
        self.project = Project.query.get(request.context['project_id'])
        self.repos = Repo.query.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=request.context['sha1'],
            distro=request.context['distro'],
            distro_version=request.context['distro_version'],
            flavor=flavor_name).order_by(desc(Repo.modified)).all()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return [r for r in self.repos]


class FlavorsController(object):

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        project = Project.get(request.context['project_id'])
        repos = Repo.query.filter_by(
            project=project,
            ref=request.context['ref'],
            sha1=request.context['sha1'],
            distro=request.context['distro'],
            distro_version=request.context['distro_version']).all()

        return [r.flavor for r in repos]

    @expose()
    def _lookup(self, flavor, *remainder):
        return FlavorController(flavor), remainder
