import requests
import datetime
import logging

from pecan import conf
from sqlalchemy import asc

from shaman import models


logger = logging.getLogger(__name__)


def get_next_node():
    """
    Retrieves the next chacra node in
    the rotation and returns it.
    """
    nodes = models.Node.query.filter_by(healthy=True).order_by(
        asc(models.Node.last_used),
    )
    for node in nodes:
        if is_node_healthy(node):
            node.last_used = datetime.datetime.utcnow()
            models.commit()
            logger.info("node: %s was chosen as the next in rotation", node.host)
            return node
    return None


def is_node_healthy(node):
    """
    Pings the chacra node's health check endpoint
    to verify it is healthy and ready for use.

    If it fails the health check, the node's ``down_count``
    will be incremented. If the ``down_count`` reaches the
    value set for ``health_check_retries`` it will be
    marked down and removed from the pool.
    """
    check_url = "https://{}/health/".format(node.host)
    r = requests.get(check_url)
    node.last_check = datetime.datetime.utcnow()
    models.commit()
    if r.status_code == 200:
        return True
    else:
        node.down_count = node.down_count + 1
        logger.warning("node: %s has failed a health check. current count: %s", node.host, node.down_count)
        if node.down_count == getattr(conf, 'health_check_retries', 3):
            logger.warning("node: %s has reached the limit for health check retires and will marked down", node.host)
            node.healthy = False
        models.commit()

    return False
