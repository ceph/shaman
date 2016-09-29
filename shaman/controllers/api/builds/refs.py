from pecan import request, expose, abort
from shaman.models import Project, Build
from shaman.controllers.api.builds import sha1s


class RefAPIController(object):

    def __init__(self, ref_name):
        self.ref_name = ref_name
        self.project = Project.query.get(request.context['project_id'])
        self.builds = Build.query.filter_by(project=self.project, ref=ref_name).all()
        request.context['ref'] = ref_name

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        return list(
            set([r.sha1 for r in self.builds])
        )

    @expose()
    def _lookup(self, sha1_name, *remainder):
        return sha1s.SHA1APIController(sha1_name), remainder
