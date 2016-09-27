import datetime

from pecan import expose, abort
from pecan.secure import secure
from pecan.decorators import transactional

from shaman.models import Node
from shaman.auth import basic_auth
from shaman.util import get_next_node
from shaman import models


class NodeController(object):

    def __init__(self, host):
        self.host = host
        self.node = Node.query.filter_by(host=host).first()

    @expose(generic=True, template='json')
    def index(self):
        abort(405)

    @index.when(method='GET', template='json')
    def index_get(self):
        if not self.node:
            abort(404)
        return self.node

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self):
        if not self.node:
            self.node = models.get_or_create(Node, host=self.host)
        self.node.last_check = datetime.datetime.utcnow()
        self.node.down_count = 0
        self.node.healthy = True
        return {}


class NodesController(object):

    @expose(template='json')
    def index(self):
        resp = {}
        for node in Node.query.all():
            resp[node.host] = node.__json__()
        return resp

    @secure(basic_auth)
    @transactional()
    @expose(content_type="text/plain")
    def next(self):
        next_node = get_next_node()
        if not next_node:
            abort(404, "There are no healthy chacra nodes available.")
        return "https://{}/".format(next_node.host)

    @expose()
    def _lookup(self, host, *remainder):
        return NodeController(host), remainder
