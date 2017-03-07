from pecan import request, expose, abort, redirect
from shaman.models import Project, Repo
from shaman.util import get_repo_url
from sqlalchemy import desc
from shaman.controllers.api.repos import flavors as _flavors


class DistroVersionController(object):

    def __init__(self, distro_version_name):
        self.distro_version_name = distro_version_name
        request.context['distro_version'] = distro_version_name
        self.project = Project.query.get(request.context['project_id'])
        self.ref_name = request.context['ref']
        self.repo_query = Repo.query.filter_by(
            project=self.project,
            ref=self.ref_name,
            sha1=request.context['sha1'],
            distro=request.context['distro'],
            distro_version=distro_version_name,
            flavor='default').order_by(desc(Repo.modified))
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

    flavors = _flavors.FlavorsController()


class DistroController(object):

    def __init__(self, distro_name):
        self.distro_name = distro_name
        request.context['distro'] = distro_name
        self.project = Project.query.get(request.context['project_id'])
        self.repos = Repo.query.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=request.context['sha1'],
            distro=distro_name).all()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return list(
            set([r.distro_version for r in self.repos])
        )

    @expose()
    def _lookup(self, distro_version_name, *remainder):
        return DistroVersionController(distro_version_name), remainder
