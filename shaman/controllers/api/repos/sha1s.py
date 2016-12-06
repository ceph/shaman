from pecan import request, expose, abort
from shaman.models import Project, Repo
from sqlalchemy import desc
from shaman.controllers.api.repos import distros


class SHA1Controller(object):

    def __init__(self, sha1_name):
        self.sha1_name = sha1_name
        self.project = Project.query.get(request.context['project_id'])
        self.repos = Repo.query.filter_by(project=self.project, ref=request.context['ref'])
        if sha1_name != 'latest':
            self.repos = self.repos.filter_by(sha1=sha1_name).all()
            request.context['sha1'] = sha1_name
        else:
            latest_repo = self.repos.order_by(desc(Repo.modified)).first()
            self.repos = [latest_repo]
            request.context['sha1'] = latest_repo.sha1

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return list(set([r.distro for r in self.repos]))

    @expose()
    def _lookup(self, distro_name, *remainder):
        return distros.DistroController(distro_name), remainder
