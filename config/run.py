import os
from os.path import dirname
import cherrypy
from cheroot.wsgi import Server as CherryPyWSGIServer
from cheroot.wsgi import PathInfoDispatcher as WSGIPathInfoDispatcher

from pecan.deploy import deploy

simpleapp_wsgi_app = deploy('config/dev.py')

current_dir = os.path.abspath(dirname(__file__))
base_dir = dirname(current_dir)
public_path = os.path.abspath(os.path.join(base_dir, 'public'))


# A dummy class for our Root object
# necessary for some CherryPy machinery
class Root(object):
    pass


def make_static_config(static_dir_name):
    """
    All custom static configurations are set here, since most are common, it
    makes sense to generate them just once.
    """
    static_path = os.path.join('/', static_dir_name)
    configuration = {
        static_path: {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': public_path
        }
    }
    print(configuration)
    return cherrypy.tree.mount(Root(), '/', config=configuration)


# Assuming your app has media on different paths, like 'css', and 'images'
application = WSGIPathInfoDispatcher({
    '/': simpleapp_wsgi_app,
    '/static': make_static_config('static')
    }
)

server = CherryPyWSGIServer(('0.0.0.0', 8080), application, server_name='simpleapp')

try:
    server.start()
except KeyboardInterrupt:
    print("Terminating server...")
    server.stop()
