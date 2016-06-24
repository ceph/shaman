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

Shaman has three top level endpoints:

- ``repos``
  This endpoint is used to view and add/update repositories.

- ``search``
  This endpoint is used to perform searches against repositories.

- ``nodes``
  This endpoint is used to list the available chacra nodes as well
  as retrieve the next chacra node in the rotation.

GET /repos/
---------------

Returns a list of projects that shaman has repo
information about.

GET /repos/(project)/
---------------------

Returns a list of refs for the given project.

POST /repos/(project)/
----------------------

Used to add / update repos for a given project. You must
POST a json object with the following data::

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

GET /repos/(project)/(ref)/
--------------------------

Returns a list of sha1s that have built repos for the given project and ref.

GET /repos/(project)/(ref)/(sha1)/
----------------------------------

Returns a list of distros that have built repos for the given project, ref and sha1.

GET /repos/(project)/(ref)/(sha1)/(distro)/
-------------------------------------------

Returns a list of distro versions that have built repos for the given project, ref, sha1 and distro.

GET /repos/(project)/(ref)/(sha1)/(distro)/(distro_version)/
------------------------------------------------------------

Returns a list of architectures that have built repos for the given project, ref, sha1,
distro and distro_version.

GET /repos/(project)/(ref)/(sha1)/(distro)/(distro_version)/(arch)/
-------------------------------------------------------------------

Returns a list of repo objects that are built for the given project, ref, sha1,
distro, distro_version and architecture.

GET /search/(project)/(ref|sha1)/
--------------------------------

This endpoint is used to query for repos by ref or sha1. It will return metadata about
the latest built repository or repositories that matches your search criteria. 

A GET to ``/repos/ceph/master/`` would return the a list of all repos
for the ``master`` ref::

   [
     {
       "ref": "master",
       "sha1": "8d48f5413564b418a8016b6a344b517282a0f0fa",
       "distro": "ubuntu",
       "distro_version": "trusty",
       "url": "https://chacra.ceph.com/r/ceph/master/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/trusty/",
       "arch": "x86_64",
     },
     {
       "ref": "master",
       "sha1": "8d48f5413564b418a8016b6a344b517282a0f0fa",
       "distro": "ubuntu",
       "distro_version": "xenial",
       "url": "https://chacra.ceph.com/r/ceph/jewel/8d48f5413564b418a8016b6a344b517282a0f0fa/ubuntu/xenial/",
       "arch": "x86_64",
     },
     ...
   ]

The following querystring parameters are supported.

- ``distros``
  A list of distros in ``distro.distro_version`` or ``distro`` format.
  i.e. ``?distros=ubuntu, centos.7``

- ``arch``
  Filter by architecture. i.e. ``?arch=x86_64``

- ``common_sha1``
  Requires that the repos return be built for a common sha1
  across all given distros. If a common built sha1 is not found
  for distros then no results are returned.
  i.e. ``?common_sha1=True&distros=centos/7,ubuntu/xenial``


GET /nodes/
-----------

Returns a list of the chacra nodes available in the pool::

    ["https://chacra01.ceph.com", "https://chacra02.ceph.com"]

GET /nodes/next/
----------------

Returns the url for the next chacra node in the rotation::

    {"url": "https://chacra02.ceph.com"}
