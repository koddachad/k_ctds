Bulk Insert
===========

`cTDS` supports `BULK INSERT`_ for efficiently inserting large amounts of data
into a table using :py:meth:`k_ctds.Connection.bulk_insert()`.

Parameters
^^^^^^^^^^

.. list-table::
   :widths: 20 15 65
   :header-rows: 1

   * - Parameter
     - Default
     - Description
   * - ``table``
     - (required)
     - The name of the table to insert into. Supports multi-part names
       (e.g. ``dbo.MyTable``, ``MyCatalog.dbo.MyTable``).
   * - ``rows``
     - (required)
     - An iterable of data rows. Each row can be a sequence (tuple/list)
       or a :py:class:`dict` mapping column names to values (v1.9+).
   * - ``batch_size``
     - ``None``
     - Number of rows per batch. When ``None``, all rows are sent before
       validation. Set this to catch errors earlier in large imports.
   * - ``tablock``
     - ``False``
     - When ``True``, acquires a bulk-update table-level lock (the SQL
       Server ``TABLOCK`` hint). This can improve throughput for large
       inserts by reducing lock contention.
   * - ``auto_encode``
     - ``False``
     - When ``True``, queries ``INFORMATION_SCHEMA.COLUMNS`` to determine
       each column's type and collation, then automatically encodes
       Python ``str`` values before insertion. NVARCHAR/NCHAR/NTEXT
       columns are encoded to UTF-16LE; VARCHAR/CHAR/TEXT columns are
       encoded to the column's collation code page (e.g. ``cp1252``).
       This eliminates the need to manually wrap values with
       :py:class:`k_ctds.SqlVarChar` or :py:class:`k_ctds.SqlNVarChar`.
       See `Automatic Encoding`_ below.

       .. versionadded:: 2.0.0

       .. note::
          ``auto_encode`` does not support temporary tables (e.g.
          ``#TempTable``) because they are not visible in
          ``INFORMATION_SCHEMA.COLUMNS``.

Example
^^^^^^^

A bulk insert is done by providing an :ref:`iterator <python:typeiter>` of
rows to insert and the name of the table to insert the rows into. The iterator
should return a sequence containing the values for each column in the table.

.. code-block:: python

    import k_ctds
    with k_ctds.connect('host') as connection:
        connection.bulk_insert(
            'MyExampleTable',
            # A generator of the rows.
            (
                # The row values can be any python sequence type
                (i, 'hello world {0}'.format(i))
                for i in range(0, 100)
            )
        )

        # Version 1.9 supports passing dict rows.
        connection.bulk_insert(
            'MyExampleTable',
            # A generator of the rows.
            (
                {
                    'IntColumn': i,
                    'TextColumn': 'hello world {0}'.format(i)
                }
                for i in range(0, 100)
            )
        )


Inserting from a CSV File
^^^^^^^^^^^^^^^^^^^^^^^^^

This example illustrates how to import data from a *CSV* file.

.. code-block:: python

    import k_ctds
    import csv

    with open('BulkInsertExample.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        with k_ctds.connect('host') as connection:
            connection.bulk_insert(
                'BulkInsertExample',
                iter(csvreader)
            )

    # ctds 1.9 supports passing rows as dict objects, mapping column name
    # to value. This is useful if the table contains NULLable columns
    # not present in the CSV file. 
    with open('BulkInsertExample.csv', 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',')
        with k_ctds.connect('host') as connection:
            connection.bulk_insert(
                'BulkInsertExample',
                iter(csvreader)
            )



Batch Size
^^^^^^^^^^

By default, :py:meth:`k_ctds.Connection.bulk_insert()` will push all data to the
database before it is actually validated against the table's schema. If any of
the data is invalid, the entire `BULK INSERT`_ operation would fail. The
`batch_size` parameter of :py:meth:`k_ctds.Connection.bulk_insert()` can be used
to control how many rows should be copied before validating them.


Text Columns
^^^^^^^^^^^^

Data specified for bulk insertion into text columns (e.g. **VARCHAR**,
**NVARCHAR**, **TEXT**) is not encoded on the client in any way by FreeTDS.
Because of this behavior it is possible to insert textual data with an invalid
encoding and cause the column data to become corrupted.

To prevent this, it is recommended the caller explicitly wrap the the object
with either :py:class:`k_ctds.SqlVarChar` (for **CHAR**, **VARCHAR** or **TEXT**
columns) or :py:class:`k_ctds.SqlNVarChar` (for **NCHAR**, **NVARCHAR** or
**NTEXT** columns). For non-Unicode columns, the value should be first encoded
to column's encoding (e.g. `latin-1`). By default :py:class:`k_ctds.SqlVarChar`
will encode :py:class:`str` objects to `utf-8`, which is likely incorrect for
most SQL Server configurations.

.. code-block:: python

    import k_ctds
    with k_ctds.connect('host') as connection:
        connection.bulk_insert(
            #
            # Assumes a table with the following schema:
            #
            # CREATE TABLE MyExampleTableWithVarChar (
            #     Latin1Column VARCHAR(100) COLLATE
            #         SQL_Latin1_General_CP1_CI_AS,
            #     UnicodeColumn NVARCHAR(100)
            # )
            #

            'MyExampleTableWithVarChar',
            [
                (
                    # Note the value passed to SqlVarChar is first encoded to
                    # match the server's encoding.
                    k_ctds.SqlVarChar(
                        b'a string with latin-1 -> \xc2\xbd'.decode(
                            'utf-8'
                        ).encode('latin-1')
                    ),
                    # SqlNVarChar handles the UTF-16LE encoding automatically
                    # for bulk insert.
                    k_ctds.SqlNVarChar(
                        b'a string with Unicode -> \xe3\x83\x9b'.decode(
                            'utf-8'
                        )
                    ),  
              )
            ]
        )

Automatic Encoding
^^^^^^^^^^^^^^^^^^

.. versionadded:: 2.0.0

The ``auto_encode`` parameter simplifies inserting text data by
automatically encoding Python ``str`` values based on the target
column's type and collation. This replaces the manual wrapping
described in the `Text Columns`_ section above.

.. code-block:: python

    import k_ctds

    #
    # Assumes a table with the following schema:
    #
    # CREATE TABLE MyExampleTableWithVarChar (
    #     Latin1Column VARCHAR(100) COLLATE
    #         SQL_Latin1_General_CP1_CI_AS,
    #     UnicodeColumn NVARCHAR(100)
    # )
    #

    rows = [
        ('café résumé', 'こんにちは世界'),
        ('naïve', '🎉 Unicode works'),
    ]

    with k_ctds.connect('host') as connection:
        connection.bulk_insert(
            'MyExampleTableWithVarChar',
            rows,
            auto_encode=True
        )

With ``auto_encode=True``, ``'café résumé'`` is encoded to ``cp1252``
bytes for the ``VARCHAR`` column, and ``'こんにちは世界'`` is encoded to
UTF-16LE bytes for the ``NVARCHAR`` column — no manual wrapping needed.

**Using dict rows with auto_encode:**

.. code-block:: python

    with k_ctds.connect('host') as connection:
        connection.bulk_insert(
            'MyExampleTableWithVarChar',
            [
                {
                    'Latin1Column': 'café',
                    'UnicodeColumn': 'hello'
                },
                {
                    'Latin1Column': 'naïve',
                    'UnicodeColumn': '日本語'
                },
            ],
            auto_encode=True
        )

**Combining all parameters:**

.. code-block:: python

    with k_ctds.connect('host') as connection:
        connection.bulk_insert(
            'dbo.LargeImportTable',
            row_generator(),
            batch_size=5000,
            tablock=True,
            auto_encode=True
        )

.. note::

    ``auto_encode`` does not support temporary tables (e.g.
    ``#TempTable``), because temporary tables are not visible in
    ``INFORMATION_SCHEMA.COLUMNS``. For temporary tables, use the
    manual wrapping approach described in `Text Columns`_.

Table Lock Hint
^^^^^^^^^^^^^^^

The ``tablock`` parameter tells SQL Server to acquire a bulk-update
table-level lock for the duration of the insert. This can significantly
improve throughput when inserting large volumes of data, especially
when no other concurrent writers need the table.

.. code-block:: python

    with k_ctds.connect('host') as connection:
        connection.bulk_insert(
            'MyLargeTable',
            large_row_generator(),
            batch_size=10000,
            tablock=True
        )

Handling Warnings
^^^^^^^^^^^^^^^^^

Warnings raised during bulk insert (e.g. data truncation, implicit conversions)
are reported as standard Python :py:exc:`warnings.Warning` instances. The warning
message text contains the SQL Server message description.

.. code-block:: python

    import k_ctds
    import warnings

    with k_ctds.connect('host') as connection:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            connection.bulk_insert('MyTable', rows)

            for w in caught:
                print('Warning: {0}'.format(w.message))

.. note::

    Due to how SQL Server processes bulk insert data, warnings are reported
    per-batch and do not identify the specific row or column that triggered
    the issue. Structured message metadata (e.g. message number, severity,
    state) is available via the ``connection.messages`` property.

.. _BULK INSERT: https://learn.microsoft.com/en-us/sql/t-sql/statements/bulk-insert-transact-sql
