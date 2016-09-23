from pecan import make_app
from shaman import models
from shaman.templates import helpers


def setup_app(config):

    models.init_model()
    app_conf = dict(config.app)

    return make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        extra_template_vars=dict(h=helpers),
        **app_conf
    )
