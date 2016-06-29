from pecan import expose

description = "shaman is the source of truth for the state of repositories on chacra nodes."


class APIController(object):
    @expose('json')
    def index(self):
        return dict()


class RootController(object):

    @expose('json')
    def index(self):
        documentation = "https://github.com/ceph/shaman#shaman"
        return dict(
            description=description,
            documentation=documentation,
        )

    api = APIController()
