Connection Pooling
==================

Many applications will desire some form of connection pooling for improved
performance. As of version 1.2, *cTDS* does provide a simple connection pool
implementation: :py:class:`k_ctds.pool.ConnectionPool`. It can also be used with
3rd party implementation, such as `antipool <http://furius.ca/antiorm/>`_.

.. note::

    Whatever connection pooling solution is used, it is important to
    remember that :py:class:`k_ctds.Connection` and :py:class:`k_ctds.Cursor`
    objects must **not** be shared across threads.


k_ctds.pool Example
-------------------

.. code-block:: python

    import k_ctds
    import k_ctds.pool
    import pprint

    config = {
        'server': 'my-host',
        'database': 'MyDefaultDatabase',
        'user': 'my-username',
        'password': 'my-password',
        'appname': 'ctds-doc-pooling-example',
        'timeout': 5,
        'login_timeout': 5,
        'autocommit': True
    }

    pool = k_ctds.pool.ConnectionPool(
        ctds,
        config
    )

    with pool.connection() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute('SELECT @@VERSION;')
                rows = cursor.fetchall()
                print([c.name for c in cursor.description])
                pprint.pprint([tuple(row) for row in rows])
            except k_ctds.Error as ex:
                print(ex)

    # Explicitly cleanup the connection pool.
    pool.finalize()


