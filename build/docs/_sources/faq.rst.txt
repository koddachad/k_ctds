Frequently Asked Questions
==========================

Why can't I pass an empty string to :py:meth:`k_ctds.Cursor.callproc`?
----------------------------------------------------------------------

The definition of the `dblib` API implemented by `FreeTDS` does
not define a way to specify a **(N)VARCHAR** with length *0*. This
is a known deficiency of the `dblib` API. String parameters with
length *0* are interpreted as `NULL` by the `dblib` API.


Why doesn't `RAISERROR` raise a Python exception?
-------------------------------------------------

A Python exception is raised only if the last SQL operation resulted in an
error. For example, the following will not raise a
:py:class:`k_ctds.ProgrammingError` exception because the last statement does not
result in an error.

.. code-block:: SQL

    RAISERROR (N'some custom error', 10, -1);

    /* This statement does not fail, hence a Python exception is not raised. */
    SELECT 1 AS Column1;

The error `some custom error` is reported as a :py:obj:`k_ctds.Warning`.

In `cTDS` v1.3.0 and later, this warning can be turned into an exception using
the :py:mod:`warnings` module.

.. code-block:: python

    import warnings
    import k_ctds

    warnings.simplefilter('error', k_ctds.Warning)

    with k_ctds.connect() as connection:
        with connection.cursor() as cursor:
            # The following will raise a `k_ctds.Warning` exception.
            cursor.execute(
                "RAISERROR (N'this will become a python exception', 16, -1);"
            )


In `cTDS` v1.14.0 and later, all `SQL Server errors`_ with **severity > 10**
are translated to :py:obj:`k_ctds.DatabaseError` or more appropriate subclass of
it. Errors and messages with a severity of 10 or less are still translated to a
:py:obj:`k_ctds.Warning`.


What does the `Unicode codepoint U+1F4A9 is not representable...` warning mean?
-------------------------------------------------------------------------------

Until `FreeTDS`_ **1.00**, the default encoding used on the connection to
the database was *UCS-2*. FreeTDS requires all text data be encodable in the
connection's encoding. Therefore `cTDS` would replace non *UCS-2* characters in
strings and generate a warning before sending the data to the database. Once
support was added for configuring the connection to use *UTF-16* in `FreeTDS`_
**1.00**, this behavior was no longer necessary.

Upgrading the version of `FreeTDS`_ will resolve this warning and unicode
codepoints outside the *UCS-2* range will no longer be replaced.

.. note::

   FreeTDS versions prior to 1.0 had limited *UTF-16* support that
   required manual configuration via *freetds.conf*. These versions
   are no longer supported by `k-cTDS`.

How do I work with ``DATETIMEOFFSET`` columns?
----------------------------------------------

`cTDS` automatically maps between Python timezone-aware
:py:class:`datetime.datetime` objects and SQL Server ``DATETIMEOFFSET``
columns. This requires `FreeTDS`_ **0.95+** and TDS protocol version **7.3+**.

**Reading:** ``DATETIMEOFFSET`` values are returned as timezone-aware
:py:class:`datetime.datetime` objects with the offset preserved from
SQL Server.

**Writing:** Pass a timezone-aware :py:class:`datetime.datetime` to
:py:meth:`k_ctds.Cursor.execute` or :py:meth:`k_ctds.Cursor.executemany`.
`cTDS` will automatically use ``DATETIMEOFFSET`` as the SQL type.

.. code-block:: python

    import k_ctds
    from datetime import datetime, timezone, timedelta

    eastern = timezone(timedelta(hours=-5))
    dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=eastern)

    with k_ctds.connect('myserver', user='user', password='pass') as conn:
        with conn.cursor() as cursor:
            # Writing
            cursor.execute(
                'INSERT INTO Events (event_time) VALUES (:0)',
                (dt,)
            )

            # Reading
            cursor.execute('SELECT event_time FROM Events')
            row = cursor.fetchone()
            # row[0] is a timezone-aware datetime

**Bulk insert:** Timezone-aware datetimes also work with
:py:meth:`k_ctds.Connection.bulk_insert`.

.. note::

    Naive (timezone-unaware) :py:class:`datetime.datetime` objects continue
    to map to ``DATETIME`` or ``DATETIME2`` as before. Only timezone-aware
    datetimes use ``DATETIMEOFFSET``.

.. note::

    Python's :py:class:`datetime.datetime` has microsecond precision (6
    digits). SQL Server ``DATETIMEOFFSET`` supports up to 7 digits
    (100-nanosecond precision). The 7th digit is truncated when reading
    from SQL Server and is not available when writing.

.. _FreeTDS: https://www.freetds.org
.. _SQL Server errors: https://learn.microsoft.com/en-us/sql/relational-databases/errors-events/database-engine-events-and-errors
