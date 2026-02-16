Executing SQL Statements
========================

*cTDS* implements both the :py:meth:`k_ctds.Cursor.execute` and
:py:meth:`k_ctds.Cursor.executemany` methods for executing SQL statements.
Both are implemented using the `sp_executesql`_ `SQL Server`_ stored procedure.
This allows optimizations when running batches using
:py:meth:`k_ctds.Cursor.executemany`.

.. note::

    `sp_executesql`_ support requires `FreeTDS`_ 1.0 or later, which is
    the minimum version supported by `k-cTDS`.

Passing Parameters
------------------

Parameters may be passed to the :py:meth:`k_ctds.Cursor.execute` and
:py:meth:`k_ctds.Cursor.executemany` methods using the **numeric** parameter
style as defined in :pep:`0249#paramstyle`.

.. note::
   Passing parameters using the **numeric** `paramstyle` assumes an initial
   index of 0.

.. code-block:: python

    cursor.execute(
        'SELECT * FROM MyTable WHERE Id = :0 AND OtherId = :1',
        (1234, 5678)
    )

    cursor.executemany(
        '''
        INSERT (Id, OtherId, Name, Birthday) INTO MyTable
        VALUES (:0, :1, :2, :3)
        ''',
        (
            (1, 2, 'John Doe', datetime.date(2001, 1, 1)),
            (2000, 22, 'Jane Doe', datetime.date(1974, 12, 11)),
        )
    )



Parameter Types
^^^^^^^^^^^^^^^

Parameter SQL types are inferred from the Python object type. If desired,
the SQL type can be explicitly specified using a
:doc:`type wrapper class <types>`. For example, this is necessary when passing
:py:obj:`None` for a `BINARY` column.

.. code-block:: python

    cursor.execute(
        '''
        INSERT (Id, BinaryValue) INTO MyTable
        VALUES (:0, :1)
        ''',
        (
            (1, cursor.SqlBinary(None)),
        )
    )

.. note::

    Timezone-aware :py:class:`datetime.datetime` objects are automatically
    mapped to the SQL ``DATETIMEOFFSET`` type when using TDS 7.3+.
    Naive datetimes continue to map to ``DATETIME``/``DATETIME2``.



Limitations
-----------

Due to the implementation of :py:meth:`k_ctds.Cursor.execute` and
:py:meth:`k_ctds.Cursor.executemany`, any SQL code which defines parameters
cannot be used with execute parameters. For example, the following is **not**
supported:

.. code-block:: python

    # Parameters passed from python are not supported with SQL '@'
    # parameters.
    cursor.execute(
        '''
        CREATE PROCEDURE Increment
            @value INT OUTPUT
        AS
            SET @value = @value + :0;
        ''',
        (1,)
    )


.. warning::

    Currently `FreeTDS`_ does not support passing empty string parameters.
    Empty strings are converted to `NULL` values internally before being
    transmitted to the database.


.. _FreeTDS: https://www.freetds.org
.. _SQL Server: https://www.microsoft.com/sql-server
.. _sp_executesql: https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-executesql-transact-sql
