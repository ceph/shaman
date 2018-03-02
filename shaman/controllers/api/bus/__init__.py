import pika
import json

from pecan import expose, abort, request, conf
from pecan.secure import secure

from shaman.auth import github_basic_auth


class BusController(object):

    @expose(generic=True)
    def index(self):
        abort(405)

    @index.when(method='GET')
    def index_get(self):
        abort(405)

    @secure(github_basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self, project, queue):
        credentials = pika.PlainCredentials(conf.RABBIT_USER, conf.RABBIT_PW)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=conf.RABBIT_HOST,
            credentials=credentials
        ))
        channel = connection.channel()
        queue = "{}/{}".format(project, queue)
        channel.queue_declare(
            queue,
            auto_delete=True,
        )

        properties = pika.BasicProperties(content_type='application/json')
        channel.basic_publish(
            routing_key=queue,
            body=json.dumps(request.json),
            properties=properties,
        )
        connection.close()
        return {}
