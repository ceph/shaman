from shaman import models
from sqlalchemy.exc import OperationalError
import logging


logger = logging.getLogger(__name__)


class SystemCheckError(Exception):

    def __init__(self, message):
        self.message = message


def database_connection():
    """
    A very simple connection that should succeed if there is a good/correct
    database connection.
    """
    try:
        models.Project.get(1)
    except OperationalError as exc:
        raise SystemCheckError(
            "Could not connect or retrieve information from the database: %s" % exc.message)


system_checks = (
    database_connection
)


def is_healthy():
    """
    Perform all the registered system checks and detect if anything fails so
    that the system can send a callback indicating an OK status
    """
    for check in system_checks:
        try:
            check()
        except Exception:
            logger.exception('system is unhealthy')
            return False
        return True
