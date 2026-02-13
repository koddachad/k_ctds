TLS/SSL Encryption
==================

`cTDS` relies on `FreeTDS`_ for all network communication, including
TLS/SSL encryption. Encryption is configured through the FreeTDS
configuration file (``freetds.conf``), not through the
:py:func:`ctds.connect` call. This page explains how to set up
encrypted connections for common scenarios.

.. note::

    FreeTDS must be compiled with OpenSSL (or GnuTLS) support for
    encryption to work. If you built FreeTDS from source, make sure you
    used the ``--with-openssl`` flag. See :doc:`install` for details.


Encryption Modes
----------------

FreeTDS supports four encryption modes, set via the ``encryption``
directive in ``freetds.conf``:

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Mode
     - Behavior
   * - ``off``
     - Encryption is disabled. The connection will fail if the server
       requires encryption.
   * - ``request``
     - Encryption is used if the server supports it. This is the
       **default** for TDS versions 7.1 and above.
   * - ``require``
     - Encryption is mandatory. The connection will fail if the server
       does not support encryption.
   * - ``strict``
     - Like ``require``, but uses TDS 8.0 and forces certificate
       validation regardless of other settings. Requires FreeTDS 1.4+.


Basic Encrypted Connection
--------------------------

For most SQL Server instances that support (but do not require)
encryption, the default ``request`` mode is sufficient and no
configuration changes are needed.

To explicitly require encryption, add the ``encryption`` directive to
your server entry in ``freetds.conf``:

.. code-block:: ini

    [myserver]
    host = db.example.com
    port = 1433
    tds version = 7.4
    encryption = require

Then connect normally:

.. code-block:: python

    import ctds

    with ctds.connect('myserver', user='myuser', password='mypassword') as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT encrypt_option FROM sys.dm_exec_connections "
                "WHERE session_id = @@SPID"
            )
            print(cursor.fetchone()[0])  # Should print 'TRUE'


Connecting to Azure SQL Database
--------------------------------

Azure SQL Database requires encrypted connections. Add the following
to your ``freetds.conf``:

.. code-block:: ini

    [azure]
    host = yourserver.database.windows.net
    port = 1433
    tds version = 7.4
    encryption = require

Then connect as usual:

.. code-block:: python

    import ctds

    with ctds.connect(
        'azure',
        user='youruser@yourserver',
        password='yourpassword',
        database='yourdatabase'
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            print(cursor.fetchone()[0])


Certificate Validation
----------------------

By default, FreeTDS does **not** validate the server's TLS
certificate. This means any certificate (including self-signed) is
accepted. For production environments, you should enable certificate
validation.

.. code-block:: ini

    [myserver]
    host = db.example.com
    port = 1433
    tds version = 7.4
    encryption = require
    ca file = /etc/ssl/certs/ca-certificates.crt
    check certificate hostname = yes

The following certificate-related options are available:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Option
     - Description
   * - ``ca file``
     - Path to a PEM file containing root CA certificates used to
       validate the server certificate. Set to ``system`` to use the
       operating system's default trust store. When omitted, any
       certificate is accepted.
   * - ``crl file``
     - Path to a certificate revocation list file. Only used when
       ``ca file`` is also set.
   * - ``check certificate hostname``
     - Whether to verify the server hostname matches the certificate.
       Defaults to ``yes`` when ``ca file`` is set.
   * - ``certificate hostname``
     - Override the expected hostname in the certificate. Only used
       when ``ca file`` is set. Defaults to the ``host`` value.

.. note::

    If the server uses a self-signed certificate (common in development
    environments), omit the ``ca file`` directive to skip validation.
    Never do this in production.


Legacy Servers (TLS 1.0)
------------------------

Some older servers (such as Windows Server 2008) only support TLS 1.0,
which is disabled by default in modern FreeTDS builds. To connect to
these servers:

.. code-block:: ini

    [legacy-server]
    host = oldbox.example.com
    port = 1433
    tds version = 7.1
    encryption = require
    enable tls v1 = yes

.. warning::

    TLS 1.0 has known security vulnerabilities and should not be used
    in production. Upgrade the server if at all possible.


Configuration File Locations
----------------------------

FreeTDS searches for its configuration file in the following order:

1. The path set by the ``FREETDSCONF`` environment variable
2. ``~/.freetds.conf`` (user-specific)
3. The system-wide ``freetds.conf`` (typically ``/usr/local/etc/freetds.conf``
   or ``/etc/freetds/freetds.conf``, depending on how FreeTDS was installed)

You can use the ``FREETDSCONF`` environment variable to point to a
custom configuration file without modifying system files:

.. code-block:: bash

    export FREETDSCONF=/path/to/my/freetds.conf
    python myapp.py


Verifying Encryption
--------------------

To confirm that your connection is encrypted, query the
``sys.dm_exec_connections`` system view:

.. code-block:: python

    import ctds

    with ctds.connect('myserver', user='myuser', password='mypassword') as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT encrypt_option, protocol_type, auth_scheme "
                "FROM sys.dm_exec_connections "
                "WHERE session_id = @@SPID"
            )
            row = cursor.fetchone()
            print(f"Encrypted: {row[0]}")       # TRUE or FALSE
            print(f"Protocol: {row[1]}")         # TSQL
            print(f"Auth scheme: {row[2]}")      # SQL or NTLM

.. note::

    Access to ``sys.dm_exec_connections`` requires the
    ``VIEW SERVER STATE`` permission. If you do not have this
    permission, ask your database administrator.


Troubleshooting
---------------

**Connection fails with "Read from SQL server failed"**
    The server requires encryption but FreeTDS was not compiled with
    OpenSSL support, or the ``encryption`` setting is ``off``. Rebuild
    FreeTDS with ``--with-openssl`` and set ``encryption = require``.

**Connection fails with a certificate error**
    The ``ca file`` directive points to a CA bundle that does not
    contain the issuing CA for the server's certificate. Verify the
    server certificate chain and update the CA file, or remove the
    ``ca file`` directive to skip validation (not recommended for
    production).

**Connection hangs or times out**
    Some TDS protocol versions have issues with certain encryption
    configurations. Try setting ``tds version = 7.3`` if you are
    currently using ``7.4``.

**Verifying FreeTDS has TLS support**
    Use ``tsql -C`` to check the build configuration. Look for
    ``OpenSSL: yes`` or ``GnuTLS: yes`` in the output.

.. code-block:: bash

    $ tsql -C
    Compile-time settings (established with the "configure" script)
                                Version: freetds v1.4.10
                 freetds.conf directory: /usr/local/etc
         ...
                        OpenSSL: yes
                         GnuTLS: no


.. _FreeTDS: https://www.freetds.org
