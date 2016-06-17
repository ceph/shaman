shaman
======
A REST API that serves as the source of truth for the state of
repositories on chacra nodes. It can be queried to get information
on what branches and sha1's are built and available for ceph.

It also acts as an orchestration service for a pool of chacra nodes,
allowing for horizontal scalability.
