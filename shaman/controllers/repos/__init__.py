from pecan import expose, request, abort
from shaman.models import Repo, Project
from sqlalchemy import desc


class RepoController(object):

    def __init__(self, _id):
        self.project = Project.get(request.context['project_id'])
        self.repo = Repo.get(_id)
        if not self.project:
            # TODO: nice project not found error template
            abort(404, 'project not found')
        if not self.repo:
            # TODO: nice project not found error template
            abort(404, 'build not found')

    @expose('jinja:build.html')
    def index(self):
        return dict(
            project_name=self.project.name,
            build=self.repo,
            section="Repos",
            breadcrumb="> {} > {} > {}".format(self.repo.ref, self.repo.sha1, self.repo.flavor),
        )


class FlavorController(object):

    def __init__(self, flavor_name):
        self.flavor_name = flavor_name
        self.project = Project.get(request.context['project_id'])
        if not self.project:
            # TODO: nice project not found error template
            abort(404, 'project not found')
        request.context['flavor'] = flavor_name

    @expose('jinja:builds.html')
    def index(self):
        repos = Repo.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=request.context['sha1'],
            flavor=self.flavor_name
        ).order_by(desc(Repo.modified)).all()

        return dict(
            project_name=self.project.name,
            builds=repos,
            breadcrumb="> {} > {} > {}".format(request.context['ref'], request.context['sha1'], self.flavor_name),
            section="Repos",
        )

    @expose()
    def _lookup(self, build_id, *remainder):
        return RepoController(build_id), remainder


class SHA1Controller(object):

    def __init__(self, sha1_name):
        self.sha1_name = sha1_name
        self.project = Project.get(request.context['project_id'])
        if not self.project:
            # TODO: nice project not found error template
            abort(404, 'project not found')
        request.context['sha1'] = sha1_name

    @expose('jinja:builds.html')
    def index(self):
        repos = Repo.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=self.sha1_name
        ).order_by(desc(Repo.modified)).all()

        distinct = {
            "flavors": list(set([r.flavor for r in repos]))
        }

        return dict(
            project_name=self.project.name,
            distinct=distinct,
            builds=repos,
            breadcrumb="> {} > {}".format(request.context['ref'], self.sha1_name),
            section="Repos",
        )

    @expose()
    def _lookup(self, flavor_name, *remainder):
        return FlavorController(flavor_name), remainder


class RefController(object):

    def __init__(self, ref_name):
        self.ref_name = ref_name
        self.project = Project.get(request.context['project_id'])
        if not self.project:
            # TODO: nice project not found error template
            abort(404, 'project not found')
        request.context['ref'] = ref_name

    @expose('jinja:builds.html')
    def index(self):
        repos = Repo.filter_by(
            project=self.project,
            ref=self.ref_name
        ).order_by(desc(Repo.modified)).all()

        distinct = {
            "sha1s": list(set([r.sha1 for r in repos]))
        }

        return dict(
            project_name=self.project.name,
            distinct=distinct,
            builds=repos,
            breadcrumb="> {}".format(self.ref_name),
            section="Repos",
        )

    @expose()
    def _lookup(self, sha1_name, *remainder):
        return SHA1Controller(sha1_name), remainder


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(name=project_name).first()
        if not self.project:
            # TODO: nice project not found error template
            abort(404, 'project not found: %s' % project_name)
        else:
            request.context['project_id'] = self.project.id

    @expose('jinja:builds.html')
    def index(self):
        repos = Repo.filter_by(project=self.project).order_by(desc(Repo.modified)).all()
        distinct = {
            "refs": list(set([b.ref for b in repos]))
        }

        return dict(
            project_name=self.project_name,
            distinct=distinct,
            builds=repos,
            section="Repos",
        )

    @expose()
    def _lookup(self, ref_name, *remainder):
        return RefController(ref_name), remainder


class ReposController(object):

    @expose('jinja:builds.html')
    def index(self):
        repos = Repo.query.order_by(desc(Repo.modified)).all()
        distinct = {
            "projects": list(set([r.project.name for r in repos]))
        }
        return dict(
            builds=repos,
            distinct=distinct,
            section="Repos",
        )

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder
