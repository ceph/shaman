shaman
======
A REST API that serves as the source of truth for the state of
repositories on chacra nodes. It can be queried to get information
on what branches and sha1's are built and available for ceph.

It also acts as an orchestration service for a pool of chacra nodes,
allowing for horizontal scalability.


Configuration
=============

credentials
-----------
The POST and DELETE HTTP methods are protected by default using basic HTTP
authentication. The credentials must be defined in the configuration file for
the service as follows::

    api_user = 'username'
    api_key = 'secret'

chacra health checks
--------------------
To configure the amount of times a chacra node can fail it's health
check before being marked down set the following::

    health_check_retries = 3


API Endpoints
=============

The parent endpoint for any API interaction is ``/api/``.

Shaman has three top level endpoints:

- ``repos``
  This endpoint is used to view and add/update repositories.

- ``search``
  This endpoint is used to perform searches against repositories.

- ``nodes``
  This endpoint is used to list the available chacra nodes as well
  as retrieve the next chacra node in the rotation.

GET /api/repos/
---------------

Returns a list of projects that shaman has repo
information about.

POST /api/repos/(project)/
--------------------------

Used to add and update a repo for a given project.

When adding a repo, you must POST a json object with
the following data::

    {
        "distro": "Ubuntu",
        "distro_version": "Trusty",
        "ref": "jewel",
        "sha1": "45107e21c568dd033c2f0a3107dec8f0b0e58374",
        "url": "https://chacra.ceph.com/r/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/trusty/",
        "chacra_url": "https://chacra.ceph.com/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/trusty/",
        "status": "requested"
    }

The ``status`` and ``url`` fields are available for updating. You
need to include the ``chacra_url`` as the unique identifier for the repo
when updating. For example, to change a repo's ``status`` to "ready" POST
with the following::

    {
        "chacra_url": "https://chacra.ceph.com/repos/ceph/jewel/45107e21c568dd033c2f0a3107dec8f0b0e58374/ubuntu/trusty/",
        "status": "ready"
    }

GET /api/search/
----------------

This endpoint is used to query for repos. It will return metadata about
the latest built repository or repositories that matches your search criteria.

Search results are returned as a list of Repo objects and ordered by
the date they were built in descending order. For example::

   [
     {
       "ref": "master",
       "sha1": "8d48f5413564b418a8016b6a344b517282a0f0fa",
       "distro": "ubuntu",
       "distro_codename": "trusty",
       "distro_version": "14.04",
       "url": "https://chacra.ceph.com/r/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/trusty/",
       "chacra_url": "https://chacra.ceph.com/repos/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/trusty/",
       "modified" "2016-06-15 14:04:54.671504",
       "status": "building",
       "flavor": "default"
     },
     {
       "ref": "master",
       "sha1": "8d48f5413564b418a8016b6a344b517282a0f0fa",
       "distro": "ubuntu",
       "distro_codename": "xenial",
       "distro_version": "16.04",
       "url": "",
       "chacra_url": "https://chacra.ceph.com/repos/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/xenial/"
       "modified" "2016-06-15 14:04:54.671504",
       "status": "queued",
       "flavor": "notcmalloc"
     },
     ...
   ]

Repo Metadata
^^^^^^^^^^^^^

The following metadata is returned for a Repo object when searching.

- ``ref``
  The ref or branch the repo was built for.

- ``sha1``
  The sha1 for the built repo.

- ``distro``
  The distro the repo was built for.

- ``distro_codename``
  The codename of the distro the repo was built for.

- ``distro_version``
  The version of the distro the repo was built for.

- ``url``
  The url to the actual repo files.

- ``chacra_url``
  The url that represents this repo in chacra. This is also used as the
  unique identifer for a repo in shaman.

- ``modified``
  The date this repo was last modified.

- ``status``
  The status of the repo in chacra. Available values are: requested, queued, building, and ready.

- ``flavor``
  The flavor of the binaries in the repo. Available values are:  default, notcmalloc, and blkin.

Search Filters
^^^^^^^^^^^^^^

The following querystring parameters are supported.

- ``distros``
  A list of distros in ``distro/distro_version`` or ``distro/distro_codename`` format.
  i.e. ``?distros=ubuntu/xenial,centos/7``

- ``sha1``
  Pass a sha1 to limit the results by that sha1. Optionally, you can use
  the special keyword ``latest`` to only return Repo objects that are built
  for the latest built ``sha1``. If you provide multiple ``distros`` and also
  use ``?sha1=latest`` it will be the latest ``sha1`` that is common across
  all of the provided distros. If there is no latest common ``sha1`` for the
  given distros then no results will be returned.

- ``ref``
  Limit the search results to the given ``ref``.

- ``flavor``
  Limit the search results to the given ``flavor``.

- ``status``
  Limit the search results to the given ``status``.

For example, to find the latest sha1 built for the jewel branch of ceph for
all ubuntu xenial and centos7 you would do the following: ``?distros=ubuntu/xenial,centos/7&ref=jewel&sha1=latest``

GET /api/nodes/
---------------

Returns a dict containing info on all the chacra nodes available in the pool::

    {"chacra01.ceph.com", {
        "host": "chacra01.ceph.com",
        "last_used": "2016-07-07 22:08:13.112633",
        "last_check": "2016-07-07 22:08:13.112633",
        "healthy": true,
        "down_count": 0
    },
    {"chacra02.ceph.com", {
        "host": "chacra02.ceph.com",
        "last_used": "2016-07-05 22:08:13.112633",
        "last_check": "2016-07-07 22:08:13.112633",
        "healthy": false,
        "down_count": 3
    }

GET /api/nodes/(node_host)/
---------------------------

Returns a JSON object representing the requested node::

    {
      "host": "chacra02.ceph.com",
      "last_used": "2016-07-05 22:08:13.112633",
      "last_check": "2016-07-07 22:08:13.112633",
      "healthy": false,
      "down_count": 3
    }


POST /api/nodes/(node_host)/
----------------------------

This endpoint is used to add a new chacra node to the pool.

No JSON body is needed for this endpoint, ``node_host`` will
be used as the new node's ``host``.

If the node already exists, this endpoint acts as a health
check and it's ``last_check`` field will be reset back
to zero.


GET /api/nodes/next/
--------------------

Returns the url for the next chacra node in the rotation,
in plain text::

    "https://chacra02.ceph.com/"
