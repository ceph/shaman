from pecan import request, expose, abort
from shaman.models import Project, Repo
from sqlalchemy import desc
from shaman.controllers.api.repos import distros


class SHA1Controller(object):

    def __init__(self, sha1_name, *args):
        self.sha1_name = sha1_name
        self.ref_name = request.context['ref']
        self.project = Project.query.get(request.context['project_id'])
        self.repos = Repo.query.filter_by(project=self.project, ref=self.ref_name)
        if sha1_name != 'latest':
            self.repos = self.repos.filter_by(sha1=sha1_name).all()
            request.context['sha1'] = sha1_name
        else:
            # if the url contains distro and distro_version we want
            # to filter by that as well. This avoids a bug where a sha1
            # would be used for a distro/distro_version that might not have a
            # ready repo, resulting in the further controllers giving a 504
            if len(args) >= 2:
                flavor = "default"
                if 'flavors' in args:
                    flavor = args[3]
                self.repos = Repo.query.filter_by(
                    project=self.project,
                    ref=self.ref_name,
                    distro=args[0],
                    distro_version=args[1],
                    flavor=flavor,
                )
            latest_repo = self.repos.filter_by(status='ready').order_by(desc(Repo.modified)).first()
            if not latest_repo:
                abort(504, "no repository is ready for: %s/%s" % (self.project.name, self.ref_name))
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
