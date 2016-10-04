from pecan import expose, request, abort
from shaman.models import Build, Project
from sqlalchemy import desc


class BuildController(object):

    def __init__(self, _id):
        self.project = Project.get(request.context['project_id'])
        self.build = Build.get(_id)
        if not self.project:
            # TODO: nice project not found error template
            abort(404, 'project not found')
        if not self.build:
            # TODO: nice project not found error template
            abort(404, 'build not found')

    @expose('jinja:build.html')
    def index(self):
        return dict(
            project_name=self.project.name,
            build=self.build
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
        builds = Build.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=request.context['sha1'],
            flavor=self.flavor_name
        ).order_by(desc(Build.modified)).all()

        return dict(
            project_name=self.project.name,
            builds=builds,
            breadcrumb="{} > {} > {}".format(request.context['ref'], request.context['sha1'], self.flavor_name),
        )

    @expose()
    def _lookup(self, build_id, *remainder):
        return BuildController(build_id), remainder


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
        builds = Build.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=self.sha1_name
        ).order_by(desc(Build.modified)).all()

        distinct = {
            "flavors": list(set([b.flavor for b in builds]))
        }

        return dict(
            project_name=self.project.name,
            distinct=distinct,
            builds=builds,
            breadcrumb="{} > {}".format(request.context['ref'], self.sha1_name),
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
        builds = Build.filter_by(
            project=self.project,
            ref=self.ref_name
        ).order_by(desc(Build.modified)).all()

        distinct = {
            "sha1s": list(set([b.sha1 for b in builds]))
        }

        return dict(
            project_name=self.project.name,
            distinct=distinct,
            builds=builds,
            breadcrumb="{}".format(self.ref_name),
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
        builds = Build.filter_by(project=self.project).order_by(desc(Build.modified)).all()
        distinct = {
            "refs": list(set([b.ref for b in builds]))
        }

        return dict(
            project_name=self.project_name,
            distinct=distinct,
            builds=builds
        )

    @expose()
    def _lookup(self, ref_name, *remainder):
        return RefController(ref_name), remainder


class BuildsController(object):

    @expose('jinja:builds.html')
    def index(self):
        builds = Build.query.order_by(desc(Build.modified)).all()
        distinct = {
            "projects": list(set([b.project.name for b in builds]))
        }
        return dict(
            builds=builds,
            distinct=distinct,
        )

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder
