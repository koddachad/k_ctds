import k_ctds as ctds

from .base import TestExternalDatabase

class TestCursor(TestExternalDatabase):

    def test___doc__(self):
        self.assertEqual(
            ctds.Cursor.__doc__,
            '''\
A database cursor used to manage the context of a fetch operation.

:pep:`0249#cursor-objects`
'''
        )

    def test_typeerror(self):
        self.assertRaises(TypeError, ctds.Cursor)

    def test___repr___open(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                r = repr(cursor)
                self.assertEqual(r, '<k_ctds.Cursor (open)>')

    def test___repr___open_with_results(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1 AS a, 2 AS b, 3 AS c')
                r = repr(cursor)
                self.assertEqual(r, '<k_ctds.Cursor (open, 3 columns)>')

    def test___repr___closed(self):
        with self.connect() as connection:
            cursor = connection.cursor()
            cursor.close()
            self.assertEqual(repr(cursor), '<k_ctds.Cursor (closed)>')
