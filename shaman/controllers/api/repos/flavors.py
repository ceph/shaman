from pecan import request, expose, abort, redirect
from shaman.models import Project, Repo
from shaman.util import get_repo_url
from sqlalchemy import desc


class FlavorController(object):

    def __init__(self, flavor_name):
        self.flavor_name = flavor_name
        self.project = Project.query.get(request.context['project_id'])
        self.ref_name = request.context['ref']
        self.repo_query = Repo.query.filter_by(
            project=self.project,
            ref=self.ref_name,
            sha1=request.context['sha1'],
            distro=request.context['distro'],
            distro_version=request.context['distro_version'],
            flavor=flavor_name).order_by(desc(Repo.modified))
        self.repos = self.repo_query.all()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return [r for r in self.repos]

    @expose()
    def repo(self, **kw):
        repo_url = get_repo_url(
            self.repo_query,
            kw.get('arch'),
        )
        if not repo_url:
            abort(504, "no repository is ready for: %s/%s" % (self.project.name, self.ref_name))
        redirect(repo_url)

    @expose()
    def _default(self, arch, *args):
        directory = None
        if args:
            directory = args[0]
        repo_url = get_repo_url(
            self.repo_query,
            arch,
            directory=directory,
            repo_file=False,
        )
        if not repo_url:
            abort(504, "no repository is ready for: %s/%s" % (self.project.name, self.ref_name))
        redirect(repo_url)


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
