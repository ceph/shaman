from shaman import models
from sqlalchemy.exc import OperationalError
import logging
import os

from pecan import conf


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


def fail_health_check():
    """
    Checks for the existance of a file and if that file exists it fails
    the check. This is used to manually take a node out of rotation for
    maintenance.
    """
    check_file_path = getattr(conf, "fail_check_trigger_path", "/tmp/fail_check")
    if os.path.exists(check_file_path):
        raise SystemCheckError("%s was found, failing health check" % check_file_path)


system_checks = (
    database_connection,
    fail_health_check,
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
