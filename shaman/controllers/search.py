from copy import deepcopy
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
        # order all the results by their modified time, descending (newest first)
        latest_modified_repos = query.order_by(desc(Repo.modified))
        distro_list = util.parse_distro_query(kw.get("distros"))
        if kw.get('sha1', '') == 'latest':
            seen_sha1s = []

            # go through all the sha1s in the repositories left from the
            # filtering, skipping the ones already queried for. We don't use
            # `set` here because it alters the ordering on `modified` from the
            # initial query
            for r in latest_modified_repos:
                if r.sha1 in seen_sha1s:
                    continue
                seen_sha1s.append(r.sha1)
                latest = []
                if not distro_list:
                    return latest_modified_repos.filter_by(sha1=r.sha1).all()

                for distro in distro_list:
                    version_filter = distro["distro_codename"] or distro['distro_version']
                    latest_repo = latest_modified_repos.filter_by(
                        sha1=r.sha1,
                        distro_version=version_filter
                    ).order_by(desc(Repo.modified)).first()
                    if latest_repo:
                        latest.append(latest_repo)
                if latest:
                    return latest
            return []
        elif kw.get('sha1'):
            common = []
            for distro in distro_list:
                version_filter = distro["distro_codename"] or distro['distro_version']
                common_repo = latest_modified_repos.filter_by(
                    sha1=kw.get('sha1'),
                    distro_version=version_filter
                ).order_by(desc(Repo.modified)).first()
                if common_repo:
                    common.append(common_repo)
            return common

        return latest_modified_repos.all()

    def apply_filters(self, filters):
        # TODO: allow operators
        filters = deepcopy(filters)
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
                # for deb-based distros we store codename in the db as version,
                # so try first with the codename, but fallback to
                # distro_version otherwise
                version_filter = distro["distro_codename"] or distro['distro_version']
                distro_filter_list.append(
                    and_(Repo.distro == distro["distro"], Repo.distro_version == version_filter)
                )
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
