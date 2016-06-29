from pecan import expose, abort, request

from shaman.models import Project
from shaman import models


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
            elif request.method == 'POST':
                self.project = models.get_or_create(Project, name=project_name)
        request.context['project_id'] = self.project.id

    @expose('json')
    def index(self):
        return self.project

    @expose()
    def _lookup(self, name, *remainder):
        pass


class ProjectsController(object):

    @expose('json')
    def index(self):
        resp = {}
        for project in Project.query.all():
            resp[project.name] = dict(
                refs=project.refs,
                sha1s=project.sha1s,
            )
        return resp

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder
