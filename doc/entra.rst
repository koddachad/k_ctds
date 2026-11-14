Microsoft Entra ID Authentication
=================================

`k_ctds` can authenticate to Azure SQL Database and Azure SQL Managed
Instance with a Microsoft Entra ID (formerly Azure Active Directory) access
token instead of a SQL login. The pre-built wheels bundle a FreeTDS build
that carries the required federated-authentication support.

.. versionadded:: 2.3

There are two ways to supply the token to :py:func:`k_ctds.connect`:

``credential``
    Any object with a ``get_token(scope)`` method, such as the credential
    classes in the `azure-identity`_ package. `k_ctds` requests a token for
    the Azure SQL scope every time a new physical connection is opened. This
    is the recommended option for long-running processes and connection
    pools, because the credential object caches and refreshes tokens before
    they expire.

``access_token``
    A token string you already hold. Tokens are valid for roughly an hour, so
    this form suits short scripts or callers that manage token refresh
    themselves.

The two arguments are mutually exclusive. When either is given, ``user`` and
``password`` are ignored and the connection uses TDS 7.4, which is the
default.

Install the optional dependency for the credential helpers with:

.. code-block:: console

    pip install k-ctds[entra]

Service principal
-----------------

.. code-block:: python

    import k_ctds
    from k_ctds import entra

    credential = entra.service_principal(
        tenant_id='00000000-0000-0000-0000-000000000000',
        client_id='11111111-1111-1111-1111-111111111111',
        client_secret='...',
    )

    with k_ctds.connect('myserver.database.windows.net',
                        database='mydb',
                        credential=credential) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT SUSER_SNAME()')
            print(cursor.fetchone()[0])

This is equivalent to ``Authentication=ActiveDirectoryServicePrincipal`` in
other drivers. The helper returns an ``azure.identity.ClientSecretCredential``;
any other `azure-identity`_ credential, such as ``ManagedIdentityCredential``
or ``DefaultAzureCredential``, can be passed in the same way.

Token string
------------

.. code-block:: python

    import subprocess

    token = subprocess.check_output([
        'az', 'account', 'get-access-token',
        '--resource', 'https://database.windows.net/',
        '--query', 'accessToken', '-o', 'tsv',
    ]).decode().strip()

    connection = k_ctds.connect('myserver.database.windows.net',
                                database='mydb',
                                access_token=token)

Connection pools
----------------

Put the credential in the connection parameters. The pool calls
:py:func:`k_ctds.connect` for every new physical connection, which requests
a fresh token each time:

.. code-block:: python

    from k_ctds.pool import ConnectionPool

    pool = ConnectionPool(k_ctds, {
        'server': 'myserver.database.windows.net',
        'database': 'mydb',
        'credential': credential,
    })

Token lifetime
--------------

The token is validated only during login. An open connection is not affected
when its token expires, so long-running queries and transactions complete
normally. Only new logins need a current token, which is why the
``credential`` form is preferred wherever connections are re-opened.

Requirements
------------

* The identity must exist in the target database, created with
  ``CREATE USER [name] FROM EXTERNAL PROVIDER`` by an Entra administrator of
  the server.
* The connection must be encrypted. Azure SQL always negotiates TLS, so no
  additional configuration is needed. See :doc:`encryption`.
* A FreeTDS build with the federated-authentication patch. The wheels on PyPI
  include it; when building against your own FreeTDS, apply the patch from
  the ``freetds`` directory of the source distribution, otherwise
  ``access_token`` raises :py:exc:`NotImplementedError`.

Helper reference
----------------

.. autofunction:: k_ctds.entra.service_principal

.. autodata:: k_ctds.ENTRA_SQL_SCOPE

.. _azure-identity: https://pypi.org/project/azure-identity/
