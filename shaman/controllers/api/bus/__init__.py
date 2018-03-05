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
    def index_post(self, project, topic):
        credentials = pika.PlainCredentials(conf.RABBIT_USER, conf.RABBIT_PW)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=conf.RABBIT_HOST,
            credentials=credentials
        ))
        channel = connection.channel()
        routing_key = "{}.{}".format(project, topic)
        channel.exchange_declare(
            exchange="shaman",
            exchange_type="topic",
        )

        properties = pika.BasicProperties(content_type='application/json')
        channel.basic_publish(
            exchange="shaman",
            routing_key=routing_key,
            body=json.dumps(request.json),
            properties=properties,
        )
        connection.close()
        return {}
