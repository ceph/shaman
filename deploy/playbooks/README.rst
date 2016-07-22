Deploying ``shaman`` applications
=================================
The current (original) architecture of ``shaman`` is meant to have two
applications running, each with a PostgreSQL database.

One of the app servers will have the master database while the other one will
be configured with a *"hot standby"* database.

All playbooks and roles for deployment are meant to accommodate this use case
primarily.


SSL support
===========
All ``shaman`` apps are deployed with SSL by default. There is no way to easily
deploy without it. For development purposes, there is a script to generate
self-signed wild-card certificates, and for production environments it is fully
automated via the awesome letsencrypt.


development
-----------
The self-signed ssl certificates can be generated manually or using the
``generate.sh`` script (located in ``files/ssl/dev/generate.sh``). The
playbooks can consume the self-signed certs from anywhere, but the example
playbooks will default to the following paths:

* ``files/ssl/dev/ssl.crt``
* ``files/ssl/dev/ssl.key``

Those are also the files that the ``generate.sh`` script will output.

The advantage of using the ``generate.sh`` script for the self-signed certs is
that they issue a wild card SSL cert for a local domain and TLD. This defaults
to: ``node.a`` but can be easily generated for anything else *as long as it is
not a single TLD*. These are valid domains to generate wild card certs:

* dev.local
* node.local

But these are not (it is not allowed to create wild card ssl certs for TLDs):

* local
* dev

Using a single ssl certificate and key for all development needs make it easier
to ignore/except in browsers once (like Firefox) or at an OS system (Chrome
will adhere to an OS-level certificate trust).

.. note:: To signal the plabyooks that self-signed SSL certs are to be used,
          the ``development_server`` playbook variable must be set to ``true``

production
----------
When deploying to production, (with ``development_server: false``) all
certificates will be taken care of by letsencrypt.

letsencrypt has different ways to generate these certificates but they mostly
require to initiate the request for an SSL certificate to originate from the
server that requires the certificate.

This is done to issue SSL certs that match the requested domain *and* server.

The workflow for creating an SSL cert via letsencrypt is roughly:

#. Ensure a filesystem path that maps to the domain being requested exists. For
   example `/var/www/1.shaman.ceph.com` (this is the location where the
   letsencrypt command will place a temporary key for validation)
#. Configure the webserver to accept requests to `/.well-known/acme-challenge/`
   on port 80 (this is where letsencrypt will request for the current domain,
   searching for the key placed in the initial step)
#. Upon validation of the domain, the pem files will be placed on
   ``/etc/letsencrypt/live/{{ fqdn }}/``

For initial deployments (if SSL certs have never been issued before), it is
a bit tricky because the Nginx configuration cannot contain paths to an SSL
cert that doesn't exist (it will refuse to run), so a temporary Nginx
configuration for the fqdn being configured must be put into place that only
accepts non-ssl traffic so that the ACME validation can happen.

Once that validation happens on the temporary Nginx file, the actual production
configuration file for the domain gets linked (and the temporary one
destroyed).

The production configuration file will contain the following directive so that
renewals can work unattended::

    location '/.well-known/acme-challenge' {
        root /var/www/{{ fqdn }}
        ...

At the end of the process, the playbooks will ensure that a crontab entry for
the configured FQDN exists, to request a re-validation of the certificate.

.. note:: The playbooks use the following guide as the main implementation reference
          https://certbot.eff.org/#ubuntuxenial-Nginx
