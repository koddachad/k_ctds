:mod: `k_ctds`

Connection
==========

.. autoclass:: k_ctds.Connection
    :members:
    :special-members:

String Representation
---------------------

``repr(connection)`` returns a human-readable summary useful for
debugging:

.. code-block:: pycon

    >>> conn = k_ctds.connect('localhost', user='sa', password='secret')
    >>> repr(conn)
    "<k_ctds.Connection database='master' spid=54>"
    >>> conn.close()
    >>> repr(conn)
    '<k_ctds.Connection (closed)>'

.. versionadded:: 2.1.0
