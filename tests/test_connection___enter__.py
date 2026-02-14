import k_ctds as ctds

from .base import TestExternalDatabase

class TestConnectionEnter(TestExternalDatabase):

    def test___doc__(self):
        self.assertEqual(
            ctds.Connection.__enter__.__doc__,
            '''\
__enter__()

Enter the connection's runtime context. On exit, the connection is
closed automatically.

:return: The connection object.
:rtype: k_ctds.Connection
'''
        )
