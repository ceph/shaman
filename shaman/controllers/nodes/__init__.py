import datetime

from pecan import expose, abort
from pecan.secure import secure

from shaman.models import Node
from shaman.auth import basic_auth
from shaman import models


class NodeController(object):

    def __init__(self, node_url):
        self.url = node_url
        self.node = Node.query.filter_by(url=node_url).first()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        if not self.node:
            abort(404)
        return self.node.__json__()

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        if not self.node:
            self.node = models.get_or_create(Node, url=self.url)
        self.node.last_check = datetime.datetime.now()
        return {}


class NodesController(object):

    @expose(generic=True, template='json')
    def index(self):
        resp = {}
        for node in Node.query.all():
            resp[node.url] = node.__json__()
        return resp

    @expose()
    def _lookup(self, node_url, *remainder):
        return NodeController(node_url), remainder
