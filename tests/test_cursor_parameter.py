import k_ctds as ctds

from .base import TestExternalDatabase

class TestCursorParameter(TestExternalDatabase):
    '''Unit tests related to the Cursor.Parameter attribute.
    '''

    def test___doc__(self):
        self.assertEqual(
            ctds.Cursor.Parameter.__doc__,
            '''\
Convenience method to :py:class:`k_ctds.Parameter`.

:return: A new Parameter object.
:rtype: k_ctds.Parameter
'''
        )

    def test_type(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                self.assertEqual(ctds.Parameter, cursor.Parameter)

    def test_call(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                value = 1234
                param = cursor.Parameter(value)
                self.assertEqual(id(param.value), id(value))
