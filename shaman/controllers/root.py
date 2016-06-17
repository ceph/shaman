from pecan import expose

description = "shaman is the source of truth for the state of repositories on chacra nodes."


class RootController(object):

    @expose('json')
    def index(self):
        documentation = "https://github.com/ceph/shaman#shaman"
        return dict(
            description=description,
            documentation=documentation,
        )

