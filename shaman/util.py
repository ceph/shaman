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
    verify_ssl = getattr(conf, "chacra_verify_ssl", False)
    r = requests.get(check_url, verify=verify_ssl)
    node.last_check = datetime.datetime.utcnow()
    if not r.ok:
        node.down_count = node.down_count + 1
        logger.warning("node: %s has failed a health check. current count: %s", node.host, node.down_count)
        if node.down_count == getattr(conf, 'health_check_retries', 3):
            logger.warning("node: %s has reached the limit for health check retires and will marked down", node.host)
            node.healthy = False
        models.commit()
        return False

    # reset the down_count when the node is healthy
    node.down_count = 0
    models.commit()
    return True


def parse_distro_release(identifier):
    """
    Back and forth translation for a release identifier, falling back to
    ``None`` when an identifier has no existing mapping.

    For CentOS, an identifier of '7' will return: None, '7'.

    For an identifier of 'xenial', will return: 'xenial', '16.04'

    returns: 2 item tuple (codename, version)
    """
    version_map = {
        'xenial': '16.04',
        'yakkety': '16.10',
        'trusty': '14.04',
    }

    codename_map = dict((v, k) for k, v in version_map.items())

    # if identifier is a codename it will exist in version_map, otherwise, if
    # we get a version (e.g. '14.04') get it from codename_map, and finally
    # fallback to None if it doesn't exist (e.g. '7')
    codename = identifier if identifier in version_map else codename_map.get(identifier)

    return (
        codename,
        # version, fallback to identifier (e.g. '7' for centos7)
        version_map.get(identifier, identifier)
    )


def parse_distro_query(query):
    """
    The search API allows a very specific syntax to refine the search given
    certain distributions. This utility will attempt to get the distinct
    distribution name and release (or version).

    On error, the controller should return an error http status with
    information about the invalid input provided by this utility.
    """
    result = []
    query_parts = query.split(',')
    for part in query_parts:
        distro, identifier = part.split('/')
        codename, version = parse_distro_release(identifier.strip())
        result.append(
            dict(distro=distro, distro_codename=codename, distro_version=version)
        )
    return result
