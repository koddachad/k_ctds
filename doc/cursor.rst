:mod: `k_ctds`

Cursor
======

.. autoclass:: k_ctds.Cursor
    :members:
    :special-members:

    **String representation**

    ``repr(cursor)`` shows whether the cursor is open or closed, and
    the column count when a result set is active:

    .. code-block:: pycon

        >>> cursor = conn.cursor()
        >>> repr(cursor)
        '<k_ctds.Cursor (open)>'
        >>> cursor.execute('SELECT 1 AS a, 2 AS b')
        >>> repr(cursor)
        '<k_ctds.Cursor (open, 2 columns)>'
        >>> cursor.close()
        >>> repr(cursor)
        '<k_ctds.Cursor (closed)>'

    .. versionadded:: 2.1.0
