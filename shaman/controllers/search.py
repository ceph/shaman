from pecan import expose, abort
from shaman.models import Repo, Project
from shaman import util
from sqlalchemy import desc, or_, and_


class SearchController(object):

    def __init__(self):
        self.filters = {
            # TODO: figure out archs
            # 'arch': Repo.arch,
            'ref': Repo.ref,
            'sha1': Repo.sha1,
            'flavor': Repo.flavor,
            'status': Repo.status,
        }

    @expose('json')
    def index(self, **kw):
        """
        Supported query args:
        distros: distro/distro_version or distro/distro_codename
        sha1: actual sha1 or "latest"
        ref: limit by ref
        flavor: limit by flavor
        status: limit by status
        """
        query = self.apply_filters(kw)
        if not query:
            return []
        filtered_repos = query.order_by(desc(Repo.modified))
        if kw.get('sha1', '') == 'latest':
            # get all the sha1s, latest first:
            sha1s = set([r.sha1 for r in filtered_repos])
            matching_repo_count = filtered_repos.count()
            # find the sha1 that is available for all the other repos
            for sha1 in sha1s:
                common_repos = filtered_repos.filter_by(sha1=sha1)
                if common_repos.count() == matching_repo_count:
                    return common_repos.all()
            return []
        return filtered_repos.all()

    def apply_filters(self, filters):
        # TODO: allow operators
        try:
            project = Project.filter_by(name=filters.pop('project')).first()
            query = Repo.filter_by(project=project)
        except KeyError:
            query = Repo.query
        if filters.get("distros", None):
            # TODO: we'll need some sort of schema validation here
            distro_list = util.parse_distro_query(filters.pop("distros"))
            distro_filter_list = []
            for distro in distro_list:
                # for deb-based distros we store codename in the db as version
                version_filter = distro["distro_codename"]
                if not distro["distro_codename"]:
                    # we do not use codenames for rpm-based distros
                    version_filter = distro["distro_version"]
                distro_filter_list.append(and_(Repo.distro == distro["distro"], Repo.distro_version == version_filter))
            query = query.filter(or_(*distro_filter_list))
        for k, v in filters.items():
            if k not in self.filters:
                # TODO: improve error reporting
                # 'invalid query params: %s' % k
                abort(400)
            if k in self.filters:
                query = self.filter_repo(k, v, query)
        return query

    def filter_repo(self, key, value, query=None):
        filter_obj = self.filters[key]

        if key == 'sha1' and value == 'latest':
            # we parse this elsewhere
            return query
        # query will exist if multiple filters are being applied, e.g. by name
        # and by distro but otherwise it will be None
        if query:
            return query.filter(filter_obj == value)
        return Repo.query.filter(filter_obj == value)
