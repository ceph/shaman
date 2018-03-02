from pecan.hooks import TransactionHook, RequestViewerHook
from shaman import models


# Server Specific Configurations
server = {
    'port': '8080',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'shaman.controllers.root.RootController',
    'modules': ['shaman'],
    'default_renderer': 'json',
    'guess_content_type_from_ext': False,
    'template_path': '%(confdir)s/../shaman/templates',
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
        RequestViewerHook(),
    ],
    'debug': True,
}

logging = {
    'loggers': {
        'root': {'level': 'INFO', 'handlers': ['console']},
        'shaman': {'level': 'DEBUG', 'handlers': ['console']},
        'pecan': {'level': 'DEBUG', 'handlers': ['console']},
        'pecan.commands.serve': {'level': 'DEBUG', 'handlers': ['console']},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        }
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
            '__force_dict__': True
        }
    }
}

sqlalchemy_w = {
    'url': 'sqlite:///dev.db',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}

sqlalchemy_ro = {
    'url': 'sqlite:///dev.db',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}

# Basic HTTP Auth credentials
api_user = 'admin'
api_key = 'secret'

# The amount of times a chacra node's health
# check can fail before being marked down and taken
# out of the pool.
health_check_retries = 3

# if this file exists the check at /_health/ will fail
fail_check_trigger_path = "/tmp/fail_check"

RABBIT_HOST = "localhost"
RABBIT_USER = "guest"
RABBIT_PW = "guest"
