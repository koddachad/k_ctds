"""
Integration tests for bulk_insert with auto_encode=True.

These tests require a running SQL Server instance and exercise the full
round-trip: create table, bulk insert with auto_encode, read back and
verify data integrity.
"""
import datetime
from decimal import Decimal


from .base import TestExternalDatabase
from .compat import unicode_


class TestBulkInsertAutoEncode(TestExternalDatabase):

    def test_varchar_latin1_collation(self):
        """VARCHAR column with SQL_Latin1_General_CP1_CI_AS (code page 1252)."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Value VARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS
                        )
                        '''.format(self.test_varchar_latin1_collation.__name__)
                    )

                # U+00BD = ½, single byte 0xBD in cp1252
                value = unicode_(b'\xc2\xbd', encoding='utf-8')
                inserted = connection.bulk_insert(
                    self.test_varchar_latin1_collation.__name__,
                    [(value,)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT Value FROM {0}'.format(
                            self.test_varchar_latin1_collation.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(value,)])

            finally:
                connection.rollback()

    def test_nvarchar_unicode(self):
        """NVARCHAR column with Unicode data."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Value NVARCHAR(100)
                        )
                        '''.format(self.test_nvarchar_unicode.__name__)
                    )

                # Japanese katakana ホ (U+30DB)
                value = unicode_(b'\xe3\x83\x9b', encoding='utf-8')
                inserted = connection.bulk_insert(
                    self.test_nvarchar_unicode.__name__,
                    [(value,)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT Value FROM {0}'.format(
                            self.test_nvarchar_unicode.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(value,)])

            finally:
                connection.rollback()

    def test_mixed_column_types(self):
        """Table with VARCHAR, NVARCHAR, INT, DATETIME, DECIMAL, VARBINARY."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Id         INT NOT NULL PRIMARY KEY,
                            Name       NVARCHAR(100),
                            Code       VARCHAR(50) COLLATE SQL_Latin1_General_CP1_CI_AS,
                            Created    DATETIME,
                            Amount     DECIMAL(7,3),
                            Data       VARBINARY(100),
                            Flag       BIT
                        )
                        '''.format(self.test_mixed_column_types.__name__)
                    )

                name = unicode_(b'\xe3\x83\x9b\xe3\x83\x9b', encoding='utf-8')
                code = unicode_(b'caf\xc3\xa9', encoding='utf-8')
                dt = datetime.datetime(2025, 6, 15, 10, 30, 0)
                amount = Decimal('123.456')
                data = b'\x01\x02\x03'

                inserted = connection.bulk_insert(
                    self.test_mixed_column_types.__name__,
                    [(1, name, code, dt, amount, data, True)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0}'.format(
                            self.test_mixed_column_types.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(len(rows), 1)
                    row = rows[0]
                    self.assertEqual(row[0], 1)
                    self.assertEqual(row[1], name)
                    self.assertEqual(row[2], code)
                    self.assertEqual(row[3], dt)
                    self.assertEqual(row[4], amount)
                    self.assertEqual(row[5], data)
                    self.assertEqual(row[6], True)

            finally:
                connection.rollback()

    def test_mixed_column_types_dict_rows(self):
        """Same as test_mixed_column_types but with dict-based rows."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Id         INT NOT NULL PRIMARY KEY,
                            Name       NVARCHAR(100),
                            Code       VARCHAR(50) COLLATE SQL_Latin1_General_CP1_CI_AS,
                            Created    DATETIME,
                            Amount     DECIMAL(7,3)
                        )
                        '''.format(self.test_mixed_column_types_dict_rows.__name__)
                    )

                name = unicode_(b'\xe3\x83\x9b\xe3\x83\x9b', encoding='utf-8')
                code = unicode_(b'caf\xc3\xa9', encoding='utf-8')
                dt = datetime.datetime(2025, 6, 15, 10, 30, 0)
                amount = Decimal('99.500')

                inserted = connection.bulk_insert(
                    self.test_mixed_column_types_dict_rows.__name__,
                    [
                        {
                            'Id': 1,
                            'Name': name,
                            'Code': code,
                            'Created': dt,
                            'Amount': amount,
                        }
                    ],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0}'.format(
                            self.test_mixed_column_types_dict_rows.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(1, name, code, dt, amount)])

            finally:
                connection.rollback()

    def test_multiple_varchar_collations(self):
        """Two VARCHAR columns with different collations on the same table."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Latin1  VARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS,
                            Latin2  VARCHAR(100) COLLATE Polish_CI_AS
                        )
                        '''.format(self.test_multiple_varchar_collations.__name__)
                    )

                # U+00E9 (é): exists in both cp1252 (0xE9) and cp1250 (0xE9)
                value = unicode_(b'\xc3\xa9', encoding='utf-8')

                inserted = connection.bulk_insert(
                    self.test_multiple_varchar_collations.__name__,
                    [(value, value)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0}'.format(
                            self.test_multiple_varchar_collations.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(value, value)])

            finally:
                connection.rollback()


    def test_multiple_rows(self):
        """Bulk insert many rows with auto_encode."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Id      INT NOT NULL PRIMARY KEY,
                            Name    NVARCHAR(100),
                            Code    VARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS
                        )
                        '''.format(self.test_multiple_rows.__name__)
                    )

                num_rows = 100
                inserted = connection.bulk_insert(
                    self.test_multiple_rows.__name__,
                    (
                        (ix, 'row {}'.format(ix), 'code {}'.format(ix))
                        for ix in range(num_rows)
                    ),
                    auto_encode=True
                )
                self.assertEqual(inserted, num_rows)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(1) FROM {0}'.format(
                            self.test_multiple_rows.__name__
                        )
                    )
                    self.assertEqual(cursor.fetchone()[0], num_rows)

            finally:
                connection.rollback()

    def test_with_batch_size(self):
        """auto_encode works with batch_size parameter."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Id      INT NOT NULL PRIMARY KEY,
                            Name    NVARCHAR(100)
                        )
                        '''.format(self.test_with_batch_size.__name__)
                    )

                num_rows = 50
                inserted = connection.bulk_insert(
                    self.test_with_batch_size.__name__,
                    (
                        (ix, 'name {}'.format(ix))
                        for ix in range(num_rows)
                    ),
                    batch_size=10,
                    auto_encode=True
                )
                self.assertEqual(inserted, num_rows)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT COUNT(1) FROM {0}'.format(
                            self.test_with_batch_size.__name__
                        )
                    )
                    self.assertEqual(cursor.fetchone()[0], num_rows)

            finally:
                connection.rollback()

    def test_with_null_strings(self):
        """None values in string columns should pass through unchanged."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Id      INT NOT NULL PRIMARY KEY,
                            Name    NVARCHAR(100) NULL,
                            Code    VARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS NULL
                        )
                        '''.format(self.test_with_null_strings.__name__)
                    )

                inserted = connection.bulk_insert(
                    self.test_with_null_strings.__name__,
                    [(1, None, None), (2, 'hello', None), (3, None, 'world')],
                    auto_encode=True
                )
                self.assertEqual(inserted, 3)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT * FROM {0} ORDER BY Id'.format(
                            self.test_with_null_strings.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [
                        (1, None, None),
                        (2, 'hello', None),
                        (3, None, 'world'),
                    ])

            finally:
                connection.rollback()

    def test_nonexistent_table(self):
        """auto_encode should raise ValueError for a table that doesn't exist."""
        with self.connect(autocommit=False) as connection:
            with self.assertRaises(ValueError) as ctx:
                connection.bulk_insert(
                    'this_table_does_not_exist_at_all',
                    [('hello',)],
                    auto_encode=True
                )
            self.assertIn('this_table_does_not_exist_at_all', str(ctx.exception))

    def test_without_auto_encode_unchanged(self):
        """Passing auto_encode=False (default) uses original behavior."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Value VARCHAR(100) COLLATE SQL_Latin1_General_CP1_CI_AS
                        )
                        '''.format(self.test_without_auto_encode_unchanged.__name__)
                    )

                # Without auto_encode, bare str produces the existing warning.
                import warnings
                with warnings.catch_warnings(record=True) as warns:
                    connection.bulk_insert(
                        self.test_without_auto_encode_unchanged.__name__,
                        [('hello',)]
                    )

                self.assertTrue(
                    any('bulk insert' in str(w.message).lower() for w in warns)
                )

            finally:
                connection.rollback()

    def test_schema_qualified_table(self):
        """auto_encode works with schema-qualified table names."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE dbo.{0}
                        (
                            Id      INT NOT NULL PRIMARY KEY,
                            Name    NVARCHAR(100)
                        )
                        '''.format(self.test_schema_qualified_table.__name__)
                    )

                value = unicode_(b'\xe3\x83\x9b', encoding='utf-8')
                inserted = connection.bulk_insert(
                    'dbo.{}'.format(self.test_schema_qualified_table.__name__),
                    [(1, value)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT Name FROM dbo.{0}'.format(
                            self.test_schema_qualified_table.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(value,)])

            finally:
                connection.rollback()

    def test_catalog_schema_qualified_table(self):
        """auto_encode works with three-part database.schema.table names."""
        with self.connect(autocommit=False) as connection:
            try:
                database = self.get_option('database')

                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}.dbo.{1}
                        (
                            Id      INT NOT NULL PRIMARY KEY,
                            Name    NVARCHAR(100),
                            Code    VARCHAR(50) COLLATE SQL_Latin1_General_CP1_CI_AS
                        )
                        '''.format(database, self.test_catalog_schema_qualified_table.__name__)
                    )

                name = unicode_(b'\xe3\x83\x9b', encoding='utf-8')
                code = unicode_(b'caf\xc3\xa9', encoding='utf-8')
                inserted = connection.bulk_insert(
                    '{}.dbo.{}'.format(database, self.test_catalog_schema_qualified_table.__name__),
                    [(1, name, code)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT Name, Code FROM {0}.dbo.{1}'.format(
                            database, self.test_catalog_schema_qualified_table.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(name, code)])

            finally:
                connection.rollback()

    def test_nvarchar_repeated_katakana(self):
        """
        Reproduce the exact pattern from existing tests: 100 repeated
        katakana characters into NVARCHAR, verifying auto_encode produces
        the same result as the manual SqlVarChar(encode('utf-16le')) approach.
        """
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Value NVARCHAR(200)
                        )
                        '''.format(self.test_nvarchar_repeated_katakana.__name__)
                    )

                value = unicode_(b'\xe3\x83\x9b', encoding='utf-8') * 100
                inserted = connection.bulk_insert(
                    self.test_nvarchar_repeated_katakana.__name__,
                    [(value,)],
                    auto_encode=True
                )
                self.assertEqual(inserted, 1)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT Value FROM {0}'.format(
                            self.test_nvarchar_repeated_katakana.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [(value,)])

            finally:
                connection.rollback()

    def test_identity_column(self):
        """auto_encode works with tables that have IDENTITY columns."""
        with self.connect(autocommit=False) as connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE {0}
                        (
                            Id      INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
                            Name    NVARCHAR(100),
                            Code    VARCHAR(50) COLLATE SQL_Latin1_General_CP1_CI_AS
                        )
                        '''.format(self.test_identity_column.__name__)
                    )

                inserted = connection.bulk_insert(
                    self.test_identity_column.__name__,
                    [
                        {'Name': '\u00e9\u00e8\u00ea', 'Code': '\u00a9\u00ae\u00bf'},
                        {'Name': '\u30db\u30c6\u30eb', 'Code': '\u00fc\u00f1\u00e4'},
                        {'Name': '\U0001f600\U0001f4a1', 'Code': '\u00d8\u00c6\u00e5'},
                    ],
                    auto_encode=True
                )
                self.assertEqual(inserted, 3)

                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT Name, Code FROM {0} ORDER BY Id'.format(
                            self.test_identity_column.__name__
                        )
                    )
                    rows = [tuple(row) for row in cursor.fetchall()]
                    self.assertEqual(rows, [
                        ('\u00e9\u00e8\u00ea', '\u00a9\u00ae\u00bf'),
                        ('\u30db\u30c6\u30eb', '\u00fc\u00f1\u00e4'),
                        ('\U0001f600\U0001f4a1', '\u00d8\u00c6\u00e5'),
                    ])

            finally:
                connection.rollback()
