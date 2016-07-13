from pecan import expose, abort

from shaman import checks


class HealthController(object):

    @expose()
    def index(self):
        if not checks.is_healthy():
            abort(500)
