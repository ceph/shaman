import json

from pecan import expose, abort, request
from pecan.secure import secure

from shaman.auth import github_basic_auth
from shaman.util import publish_message


class BusController(object):

    @expose(generic=True)
    def index(self):
        abort(405)

    @index.when(method='GET')
    def index_get(self):
        abort(405)

    @secure(github_basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self, project, topic):
        routing_key = "{}.{}".format(project, topic)
        body = json.dumps(request.json)
        publish_message(routing_key, body)
        return {}
