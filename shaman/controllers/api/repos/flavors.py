import os
from pecan import request, expose, abort, redirect
from shaman.models import Project, Repo, Arch
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
        arch = kw.get('arch')
        # requires the repository to be fully available on a remote chacra
        # instance for a proper redirect. Otherwise it will fail explicitly
        repo = self.repo_query.filter_by(status='ready').first()
        if arch:
            repo = self.repo_query.filter_by(status='ready').join(Arch).filter(Arch.name == arch).first()
        if not repo:
            abort(504, "no repository is ready for: %s/%s" % (self.project.name, self.ref_name))
        redirect(
            os.path.join(repo.chacra_url, 'repo')
        )


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
