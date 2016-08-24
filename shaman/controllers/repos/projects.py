from pecan import expose, abort, request
from pecan.secure import secure

from shaman.models import Project, Repo, Arch
from shaman.controllers.repos import refs
from shaman.auth import basic_auth
from shaman import models


class ProjectController(object):

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
        return list(
            set([r.ref for r in self.project.repos])
        )

    #TODO: we need schema validation on this method
    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        if not self.project:
            self.project = models.get_or_create(Project, name=self.project_name)
        chacra_url = request.json["chacra_url"]
        repo = Repo.query.filter_by(chacra_url=chacra_url).first()
        if not repo:
            data = dict(
                project=self.project,
                ref=request.json["ref"],
                sha1=request.json["sha1"],
                flavor=request.json["flavor"],
                distro=request.json["distro"],
                distro_version=request.json["distro_version"],
                chacra_url=chacra_url,
            )
            repo = models.get_or_create(Repo, **data)
        if request.json["status"] == "deleted":
            repo.delete()
            return {}
        update_data = dict(
            status=request.json["status"],
            url=request.json.get("url", ""),
        )
        repo.update_from_json(update_data)
        archs = request.json.get("archs", [])
        for arch in archs:
            data = dict(name=arch, repo=repo)
            models.get_or_create(Arch, **data)
        return {}

    @expose()
    def _lookup(self, ref_name, *remainder):
        return refs.RefController(ref_name), remainder


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
