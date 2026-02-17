import warnings

import k_ctds as ctds

from .base import TestExternalDatabase

class TestCursorFetchAll(TestExternalDatabase):
    '''Unit tests related to the Cursor.fetchall() method.
    '''
    def test___doc__(self):
        self.assertEqual(
            ctds.Cursor.fetchall.__doc__,
            '''\
fetchall()

Fetch all (remaining) rows of a query result, returning them as a
sequence of sequences.

:pep:`0249#fetchall`

:return: A sequence of result rows.
:rtype: k_ctds.RowList
'''
        )

    def test_closed(self):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.close()
            try:
                cursor.fetchall()
            except ctds.InterfaceError as ex:
                self.assertEqual(str(ex), 'cursor closed')
            else:
                self.fail('.fetchall() did not fail as expected') # pragma: nocover

    def test_closed_connection(self):
        connection = self.connect()
        with connection.cursor() as cursor:
            connection.close()
            try:
                cursor.fetchall()
            except ctds.InterfaceError as ex:
                self.assertEqual(str(ex), 'connection closed')
            else:
                self.fail('.fetchall() did not fail as expected') # pragma: nocover

    def test_premature(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                self.assertRaises(ctds.InterfaceError, cursor.fetchall)

    def test_fetchall(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                        DECLARE @{0} TABLE(i INT);
                        INSERT INTO @{0}(i) VALUES (1),(2),(3);
                        SELECT * FROM @{0};
                        SELECT i * 2 FROM @{0};
                    '''.format(self.test_fetchall.__name__)
                )
                self.assertEqual([tuple(row) for row in cursor.fetchall()], [(1,), (2,), (3,)])
                self.assertEqual(list(cursor.fetchall()), [])
                self.assertEqual(cursor.nextset(), True)
                self.assertEqual([tuple(row) for row in cursor.fetchall()], [(2,), (4,), (6,)])
                self.assertEqual(list(cursor.fetchall()), [])
                self.assertEqual(cursor.nextset(), None)
                self.assertRaises(ctds.InterfaceError, cursor.fetchall)

    def test_empty_resultset(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                        DECLARE @{0} TABLE(i INT);
                        INSERT INTO @{0}(i) VALUES (1),(2),(3);
                        SELECT i FROM @{0} WHERE i < 0;
                    '''.format(self.test_empty_resultset.__name__)
                )
                self.assertEqual(list(cursor.fetchall()), [])
                self.assertEqual(cursor.nextset(), None)

    def test_multiple_resultsets(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''
                        DECLARE @{0} TABLE(i INT);
                        INSERT INTO @{0}(i) VALUES (1),(2),(3);
                        SELECT i FROM @{0} WHERE i < 0;
                        SELECT i AS j FROM @{0} WHERE i > 2;
                        SELECT i AS k FROM @{0} WHERE i > 3;
                        SELECT i AS ii FROM @{0};
                    '''.format(self.test_multiple_resultsets.__name__)
                )
                self.assertEqual(list(cursor.fetchall()), [])
                self.assertEqual(cursor.nextset(), True)
                self.assertEqual([tuple(row) for row in cursor.fetchall()], [(3,)])
                self.assertEqual(list(cursor.fetchall()), [])
                self.assertEqual(cursor.nextset(), True)
                self.assertEqual(list(cursor.fetchall()), [])
                self.assertEqual(cursor.nextset(), True)
                self.assertEqual([tuple(row) for row in cursor.fetchall()], [(1,), (2,), (3,)])
                self.assertEqual(cursor.nextset(), None)

class TestCursorFetchallWarningAsError(TestExternalDatabase):
    """Regression test for Cursor_fetchrows row-buffer leak (warning-as-error)."""

    def test_fetchrows_warning_as_error(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                sproc = self.test_fetchrows_warning_as_error.__name__
                with self.stored_procedure(
                    cursor,
                    sproc,
                    '''
                    AS
                        SELECT 1 AS col1, 'hello' AS col2;
                        RAISERROR (N'fetchrows leak test warning', 10, 1) WITH NOWAIT;
                    '''
                ):
                    with warnings.catch_warnings():
                        warnings.simplefilter('error', ctds.Warning)
                        cursor.callproc(sproc, ())

                        try:
                            cursor.fetchall()
                            self.fail('.fetchall() did not raise as expected')  # pragma: nocover
                        except ctds.Warning as ex:
                            self.assertIn('fetchrows leak test warning', str(ex))

