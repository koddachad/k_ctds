'''
Helpers for authenticating to Azure SQL with Microsoft Entra ID.

Each helper returns a credential object suitable for the ``credential``
argument of :py:func:`k_ctds.connect`. The ``azure-identity`` package is
required; install it with ``pip install k-ctds[entra]``.
'''


def _identity():
    try:
        import azure.identity # pylint: disable=import-outside-toplevel
    except ImportError as ex:
        raise ImportError(
            'azure-identity is required for Entra ID authentication; '
            'install it with "pip install k-ctds[entra]"'
        ) from ex
    return azure.identity


def service_principal(tenant_id, client_id, client_secret):
    '''
    Credential for an Entra ID service principal with a client secret (the
    equivalent of the `ActiveDirectoryServicePrincipal` method in other drivers).

    :param str tenant_id: The Entra tenant ID (GUID) or domain.
    :param str client_id: The application (client) ID of the service principal.
    :param str client_secret: The client secret.
    :return: A credential object for :py:func:`k_ctds.connect`.
    '''
    identity = _identity()
    return identity.ClientSecretCredential(tenant_id, client_id, client_secret)
