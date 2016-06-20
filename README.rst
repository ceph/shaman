shaman
======
A REST API that serves as the source of truth for the state of
repositories on chacra nodes. It can be queried to get information
on what branches and sha1's are built and available for ceph.

It also acts as an orchestration service for a pool of chacra nodes,
allowing for horizontal scalability.


Configuration
=============

To define which chacra nodes should be included in the pool, provide a list
of urls with the ``chacra_nodes`` configuration option::

    chacra_nodes = ["https://chacra01.ceph.com", "https://chacra02.ceph.com"]


API Endpoints
=============

GET /repos/
---------------

Returns a list of projects that shaman has repo
information about.

POST /repos/(project)/
--------------------

Used to add / update repos for a given project::

    {
        "distro": "Ubuntu",
        "distro_version": "Trusty",
        "ref": "jewel",
        "sha1": "45107e21c568dd033c2f0a3107dec8f0b0e58374",
        "url": "https://chacra.ceph.com/r/ceph/jewel/ubuntu/trusty/",
        "arch": "x86_64",
    }

# TODO: figure out how status will work on a repo. created, building, built, failed, succeeded, etc.
# This might want to be a different endpoint?

GET /repos/(project)/(ref|sha1)/
--------------------------------

This endpoint is used to query for repos by ref or sha1. It will return metadata about
the latest built repository or repositories that matches your search criteria. 

A GET to ``/repos/ceph/master/?distros=ubuntu/trusty,centos/7,ubuntu/xenial``
would return the following if a common repo is find matching the critera::

    {
        "ref": "master",
        "sha1": "8d48f5413564b418a8016b6a344b517282a0f0fa", 
        "ubuntu": {
                    "trusty": {
                        "url": "https://chacra.ceph.com/r/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/trusty/"
                     },
                     "xenial": {
                        "url": "https://chacra.ceph.com/r/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/xenial/"
                     },
                  },
        "centos": {
                    "7": {
                        "url": "https://chacra.ceph.com/r/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/centos/7/",
                    },
                  },
    }

Matching the criteria in this case means that a repo was found available across all the distros given at a common ref and
sha1 combination.

If no repos are found that match the criteria, an empty dictionary will be returned.


GET /nodes/
-----------

Returns a list of the chacra nodes available in the pool::

    ["https://chacra01.ceph.com", "https://chacra02.ceph.com"]

GET /nodes/next/
----------------

Returns the url for the next chacra node in the rotation::

    {"url": "https://chacra02.ceph.com"}
