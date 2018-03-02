import pika

from pecan import expose, abort, request, conf
from pecan.secure import secure

from shaman.auth import basic_auth


class BusController(object):

    @expose(generic=True)
    def index(self):
        abort(405)

    @index.when(method='GET')
    def index_get(self):
        abort(405)

    @secure(basic_auth)
    @index.when(method='POST', template='json')
    def index_post(self, channel_name):
        credentials = pika.PlainCredentials(conf.RABBIT_USER, conf.RABBIT_PW)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=conf.RABBIT_HOST,
            credentials=credentials
        ))
        channel = connection.channel()

        channel.queue_bind(queue=channel_name)
        channel.basic_publish(exchange='', routing_key=channel_name, body=request.json)
        connection.close()
        return {}
