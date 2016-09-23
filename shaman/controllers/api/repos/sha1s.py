from pecan import request, expose, abort
from shaman.models import Project, Repo
from shaman.controllers.api.repos import distros


class SHA1Controller(object):

    def __init__(self, sha1_name):
        self.sha1_name = sha1_name
        request.context['sha1'] = sha1_name
        self.project = Project.query.get(request.context['project_id'])
        self.repos = Repo.query.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=sha1_name).all()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return [r.distro for r in self.repos]

    @expose()
    def _lookup(self, distro_name, *remainder):
        return distros.DistroController(distro_name), remainder
