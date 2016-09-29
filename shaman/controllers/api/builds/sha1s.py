from pecan import request, expose, abort
from shaman.models import Project, Build
from sqlalchemy import desc


class SHA1APIController(object):

    def __init__(self, sha1_name):
        self.sha1_name = sha1_name
        request.context['sha1'] = sha1_name
        self.project = Project.query.get(request.context['project_id'])
        self.builds = Build.query.filter_by(
            project=self.project,
            ref=request.context['ref'],
            sha1=sha1_name).order_by(desc(Build.modified)).all()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return self.builds
