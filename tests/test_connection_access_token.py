import os
import time
import unittest

try:
    from unittest import mock
except ImportError: # pragma: nocover
    mock = None

import k_ctds as ctds
from k_ctds import entra
from k_ctds.pool import ConnectionPool

from .base import TestExternalDatabase

try:
    import azure.identity # pylint: disable=unused-import
    HAVE_AZURE_IDENTITY = True
except ImportError: # pragma: nocover
    HAVE_AZURE_IDENTITY = False

AZURE_SP_VARS = ('CTDS_AZURE_SERVER', 'AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET')

# Azure SQL returns these while a paused database resumes or is being moved.
# Microsoft's guidance is to retry the connection.
AZURE_TRANSIENT_ERRORS = (40613, 40197, 40501, 49918, 49919, 49920)


def azure_connect(attempts=4, delay=10, **kwargs): # pragma: nocover
    '''Connect to Azure SQL, retrying transient "not currently available" errors.'''
    for attempt in range(attempts):
        try:
            return ctds.connect(**kwargs)
        except ctds.OperationalError as ex:
            message = getattr(ex, 'last_message', None) or {}
            if attempt + 1 == attempts or message.get('number') not in AZURE_TRANSIENT_ERRORS:
                raise
            time.sleep(delay)
    return None # unreachable


class _FakeToken(object): # pylint: disable=too-few-public-methods
    def __init__(self, token):
        self.token = token


class _FakeCredential(object): # pylint: disable=too-few-public-methods
    def __init__(self, token):
        self.token = token
        self.scopes = []

    def get_token(self, *scopes, **kwargs): # pylint: disable=unused-argument
        self.scopes.append(scopes)
        return _FakeToken(self.token)


def _fedauth_supported():
    '''Does the linked FreeTDS carry the federated authentication patch?'''
    try:
        ctds.connect('localhost', port=1, login_timeout=1, access_token='probe')
    except NotImplementedError:
        return False
    except ctds.Error:
        return True
    return True # pragma: nocover


class TestConnectionAccessToken(TestExternalDatabase):

    def test_entra_service_principal_helper(self):
        # Exercise the helper without azure-identity installed by injecting a
        # stand-in module; the real credential class is only used live.
        calls = []

        class FakeClientSecretCredential(object): # pylint: disable=too-few-public-methods
            def __init__(self, *args):
                calls.append(args)

        fake_identity = mock.Mock(ClientSecretCredential=FakeClientSecretCredential)
        with mock.patch.dict('sys.modules', {'azure': mock.Mock(identity=fake_identity),
                                             'azure.identity': fake_identity}):
            credential = entra.service_principal('tenant', 'client', 'secret')

        self.assertIsInstance(credential, FakeClientSecretCredential)
        self.assertEqual(calls, [('tenant', 'client', 'secret')])

    def test_entra_missing_azure_identity(self):
        with mock.patch.dict('sys.modules', {'azure': None, 'azure.identity': None}):
            with self.assertRaises(ImportError) as ctx:
                entra.service_principal('tenant', 'client', 'secret')
        self.assertIn('k-ctds[entra]', str(ctx.exception))

    def test_credential_requests_token_per_connect(self):
        credential = _FakeCredential('fake-token')
        with mock.patch('k_ctds._connect') as connect:
            ctds.connect('server', credential=credential)
            ctds.connect('server', credential=credential, database='db')

        self.assertEqual(credential.scopes, [(ctds.ENTRA_SQL_SCOPE,), (ctds.ENTRA_SQL_SCOPE,)])
        self.assertEqual(
            connect.call_args_list,
            [
                mock.call('server', access_token='fake-token'),
                mock.call('server', database='db', access_token='fake-token'),
            ]
        )

    def test_credential_none_passes_through(self):
        with mock.patch('k_ctds._connect') as connect:
            ctds.connect('server', user='u', password='p', credential=None)
        self.assertEqual(connect.call_args_list, [mock.call('server', user='u', password='p')])

    def test_credential_and_access_token(self):
        with mock.patch('k_ctds._connect') as connect:
            self.assertRaises(
                ctds.InterfaceError,
                ctds.connect, 'server', access_token='x', credential=_FakeCredential('y')
            )
        self.assertFalse(connect.called)

    def test_access_token_type(self):
        self.assertRaises(TypeError, ctds.connect, 'server', access_token=123)

    def test_access_token_requires_tds74(self):
        if not _fedauth_supported():
            self.skipTest('FreeTDS build does not support federated authentication')
        self.assertRaises(
            ctds.InterfaceError,
            ctds.connect, 'localhost', port=1, access_token='x', tds_version='7.3'
        )

    def test_access_token_login(self):
        # A bogus token must be rejected by the login, never raise a TypeError
        # or be silently ignored. Builds without the FreeTDS patch report the
        # feature as unsupported instead.
        try:
            with self.connect(access_token='not-a-real-token'):
                self.fail('connect() did not fail as expected') # pragma: nocover
        except NotImplementedError:
            if _fedauth_supported(): # pragma: nocover
                self.fail('NotImplementedError from a build that supports access_token')
        except ctds.Error:
            self.assertTrue(_fedauth_supported())

    @unittest.skipUnless(
        os.environ.get('CTDS_AZURE_SERVER') and os.environ.get('CTDS_AZURE_TOKEN'),
        'CTDS_AZURE_SERVER and CTDS_AZURE_TOKEN not set'
    )
    def test_azure_access_token(self): # pragma: nocover
        '''
        Live check against Azure SQL. Mint a token with
        `az account get-access-token --resource https://database.windows.net/`.
        '''
        connection = azure_connect(
            server=os.environ['CTDS_AZURE_SERVER'],
            database=os.environ.get('CTDS_AZURE_DATABASE'),
            access_token=os.environ['CTDS_AZURE_TOKEN'],
            login_timeout=int(os.environ.get('CTDS_AZURE_LOGIN_TIMEOUT', '60')),
            timeout=15,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT SUSER_SNAME(), @@VERSION')
                row = cursor.fetchone()
            self.assertTrue(row[0])
            self.assertIn('Azure', row[1])
            expected = os.environ.get('CTDS_AZURE_IDENTITY')
            if expected:
                self.assertEqual(row[0], expected)
        finally:
            connection.close()

    @unittest.skipUnless(
        HAVE_AZURE_IDENTITY and all(os.environ.get(var) for var in AZURE_SP_VARS),
        'azure-identity and {} are required'.format(', '.join(AZURE_SP_VARS))
    )
    def test_azure_service_principal(self): # pragma: nocover
        '''
        Live check of the ActiveDirectoryServicePrincipal equivalent: a client
        secret credential passed as `credential=`, directly and through the pool.
        '''
        server = os.environ['CTDS_AZURE_SERVER']
        client_id = os.environ['AZURE_CLIENT_ID']
        params = {
            'database': os.environ.get('CTDS_AZURE_DATABASE'),
            'credential': entra.service_principal(
                os.environ['AZURE_TENANT_ID'],
                client_id,
                os.environ['AZURE_CLIENT_SECRET'],
            ),
            'login_timeout': int(os.environ.get('CTDS_AZURE_LOGIN_TIMEOUT', '60')),
            'timeout': 15,
        }

        def whoami(connection):
            with connection.cursor() as cursor:
                cursor.execute('SELECT SUSER_SNAME()')
                return cursor.fetchone()[0]

        # Direct connection: the login name for a service principal is
        # <client id>@<tenant id>. A paused database resumes on this first
        # login, so this call retries Azure's transient errors.
        with azure_connect(server=server, **params) as connection:
            self.assertTrue(whoami(connection).lower().startswith(client_id.lower()))

        # Through the pool: each new physical connection asks the credential
        # for a token.
        pool = ConnectionPool(ctds, dict(params, server=server))
        try:
            for _ in range(2):
                with pool.connection() as connection:
                    self.assertTrue(whoami(connection).lower().startswith(client_id.lower()))
        finally:
            pool.finalize()
