from pecan.hooks import TransactionHook
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
    'static_root': '%(confdir)s/public',
    'hooks': [
        TransactionHook(
            models.start,
            models.start_read_only,
            models.commit,
            models.rollback,
            models.clear
        ),
    ],
    'debug': True,
}

logging = {
    'loggers': {
        'root': {'level': 'INFO', 'handlers': ['console']},
        'shaman': {'level': 'DEBUG', 'handlers': ['console']},
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

sqlalchemy = {
    # You may use SQLite for testing
    'url': 'sqlite:///dev.db',
    # When you set up PostreSQL, it will look more like:
    #'url': 'postgresql+psycopg2://USER:PASSWORD@DB_HOST/DB_NAME',
    'echo':          True,
    'echo_pool':     True,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}

# Basic HTTP Auth credentials
api_user = 'admin'
api_key = 'secret'
