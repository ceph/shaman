import datetime

from pecan import expose, abort, request
from pecan.secure import secure

from shaman.models import Project, Build
from shaman.auth import basic_auth
from shaman.controllers.api.builds import refs
from shaman import models


class ProjectAPIController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = Project.query.filter_by(name=project_name).first()
        if not self.project:
            if request.method != 'POST':
                abort(404)
        else:
            request.context['project_id'] = self.project.id

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return self.project.build_refs

    #TODO: we need schema validation on this method
    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        if not self.project:
            self.project = models.get_or_create(Project, name=self.project_name)
        url = request.json["url"]
        build = models.Build.query.filter_by(url=url).first()
        data = dict(
            project=self.project,
            ref=request.json["ref"],
            sha1=request.json["sha1"],
            flavor=request.json.get("flavor", "default"),
            extra=request.json.get('extra', dict()),
            distro=request.json.get('distro'),
            distro_version=request.json.get('distro_version'),
            url=request.json.get("url"),
            log_url=request.json.get("log_url"),
            build_id=request.json.get("build_id"),
            status=request.json.get("status"),
            distro_arch=request.json.get("distro_arch"),
        )
        if request.json["status"] == "completed":
            data["completed"] = datetime.datetime.utcnow()
        if not build:
            build = models.get_or_create(Build, **data)
        else:
            build.update_from_json(data)
        return {}

    @expose()
    def _lookup(self, ref_name, *remainder):
        return refs.RefAPIController(ref_name), remainder


class ProjectsAPIController(object):

    @expose('json')
    def index(self):
        resp = {}
        for project in Project.query.all():
            resp[project.name] = project.build_refs
        return resp

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectAPIController(project_name), remainder
