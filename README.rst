k-cTDS
======

.. include-documentation-begin-marker

.. image:: https://github.com/koddachad/k_ctds/actions/workflows/ci-cd.yml/badge.svg
        :target: https://github.com/koddachad/k_ctds/actions

.. image:: https://ci.appveyor.com/api/projects/status/tlgkdm69ldx7wc78?svg=true
        :target: https://ci.appveyor.com/project/koddachad/k-ctds/branch/master

.. image:: https://img.shields.io/pypi/v/k-ctds.svg
        :target: https://pypi.org/project/k-ctds/

.. image:: https://codecov.io/github/koddachad/k_ctds/graph/badge.svg
        :target: https://codecov.io/github/koddachad/k_ctds


`k-cTDS` is a full Python `DB API-2.0`_-compliant
SQL Server database library for `Linux`, `Windows`, and `Mac OS X` supporting
Python 3.

`k-cTDS` is a maintained fork of `cTDS <https://github.com/zillow/ctds>`_,
originally developed by Zillow.

The full documentation for `k-cTDS` can be found
`here <https://koddachad.github.io/k_ctds/>`_.

Features
--------

* Supports `Microsoft SQL Server <https://www.microsoft.com/sql-server>`_ 2008 and up.
* Complete `DB API-2.0`_ support.
* Python 3.9-3.13 support.
* Bulk insert (bcp) support.
* Written entirely in C.
* Pre-built wheels with bundled `FreeTDS`_ and `OpenSSL`_ for Linux, macOS, and Windows.
* TLS/SSL support out of the box (OpenSSL 3.0).

Installation
------------

Install from `PyPI`_ using `pip`_. Pre-built wheels are available for
Linux (x86_64, aarch64), macOS (x86_64, arm64), and Windows (AMD64):

.. code-block:: bash

    pip install k-ctds

That's it — the wheels bundle FreeTDS and OpenSSL so there is nothing else
to install. TLS/SSL connections to SQL Server (including Azure SQL) work
out of the box.

.. note::

    Pre-built wheels bundle **OpenSSL 3.0** (Apache 2.0 license) and
    **FreeTDS 1.5.x** (LGPL-2.0, dynamically linked). See
    ``THIRD_PARTY_NOTICES`` for details.


Using a Custom FreeTDS
^^^^^^^^^^^^^^^^^^^^^^

If you need to link against your own build of FreeTDS (for example, to use
a newer version or one compiled with different options), install from source:

.. code-block:: bash

    pip install k-ctds --no-binary k-ctds

Point the build at your FreeTDS installation using environment variables:

.. code-block:: bash

    export CTDS_INCLUDE_DIRS=/path/to/freetds/include
    export CTDS_LIBRARY_DIRS=/path/to/freetds/lib
    export CTDS_RUNTIME_LIBRARY_DIRS=/path/to/freetds/lib
    pip install k-ctds --no-binary k-ctds

On **Debian/Ubuntu** you can use the system FreeTDS:

.. code-block:: bash

    sudo apt-get install freetds-dev python3-dev
    pip install k-ctds --no-binary k-ctds

On **macOS** with Homebrew:

.. code-block:: bash

    brew install freetds
    pip install k-ctds --no-binary k-ctds

On **Windows** (requires Visual Studio 2022 Build Tools, CMake, and 7-Zip):

.. code-block:: powershell

    # Build FreeTDS from source (uses the included helper script)
    ./windows/freetds-install.ps1

    $Env:CTDS_INCLUDE_DIRS = "$(pwd)/build/include"
    $Env:CTDS_LIBRARY_DIRS = "$(pwd)/build/lib"
    pip install k-ctds --no-binary k-ctds


Dependencies
------------

When installed from a **pre-built wheel**: none — FreeTDS, OpenSSL, and
all native dependencies are bundled.

When installed from **source**: `FreeTDS`_ and its development headers
must be available on the system.

.. _`FreeTDS`: https://www.freetds.org/
.. _`OpenSSL`: https://www.openssl.org/
.. _`Python`: https://www.python.org/
.. _`DB API-2.0`: https://peps.python.org/pep-0249/
.. _`PyPI`: https://pypi.org/project/k-ctds/
.. _`pip`: https://pip.pypa.io/en/stable/

.. include-documentation-end-marker


Releasing
---------

Publishing new versions of the package and documentation is automated using
`Github Actions <https://docs.github.com/en/actions/>`_ workflows.
Official releases are marked using git
`tags <https://git-scm.com/book/en/v2/Git-Basics-Tagging>`_. Pushing the
tag to the git remote will trigger the automated deployment. E.g.

.. code-block:: console

    git tag -a v1.2.3 -m 'v1.2.3'
    git push --tags


Documentation
-------------

Generate documentation using the following:

.. code-block:: console

    tox -e docs
    # Generated to build/docs/

Documentation is hosted on `GitHub Pages <https://pages.github.com/>`_.
As such, the source code for the documentation pages must be committed
to the `gh-pages <https://github.com/koddachad/k_ctds/tree/gh-pages>`_ branch in
order to update the live documentation.


Development
-----------

Local development and testing is supported on Linux-based systems running
`tox`_ and `Docker`_. Docker containers are used for running a local instance
of `SQL Server on Linux`_. Only `Docker`_ and `tox`_ are required for running
tests locally on Linux or OS X systems. `pyenv`_ is recommended for managing
multiple local versions of Python. By default all tests are run against
the system version of `FreeTDS`_. `GNU Make`_ targets are provided to make
compiling specific `FreeTDS`_ versions locally for testing purposes. For
example:

.. code-block:: console

    # Run tests against FreeTDS version 1.1.24
    make test-1.1.24


Development and testing will require an instance of `SQL Server on Linux`_
running for validation. A script, **./scripts/ensure-sqlserver.sh**, is provided
to start a `Docker`_ container running the database and create the login used
by the tests.

.. code-block:: console

    # Start a docker-based SQL Server instance.
    # The default tox targets will do this automatically for you.
    make start-sqlserver

    # Run tests as needed ...

    # Stop the docker-base SQL Server instance.
    make stop-sqlserver


Testing
-------

Testing is designed to be relatively seamless using `Docker`_ containers
and `SQL Server on Linux`_. The `pytest`_ framework is used for running
the automated tests.

To run the tests against the system version of `FreeTDS`_ and `Python`_,
use:

.. code-block:: console

    tox


`GNU make`_ targets are provided for convenience and to provide a standard
method for building and installing the various versions of `FreeTDS`_ used
in testing. Most targets are wrappers around `tox`_ or replicate some
behavior in the CI/CD automation.

To run the tests against an arbitrary version of `FreeTDS`_:

.. code-block:: console

    # Python X.Y & FreeTDS Z.ZZ.ZZ
    make test_X.Y_Z.ZZ.ZZ


To run tests against all supported versions of `FreeTDS`_ and `Python`_
and additional linting and metadata checks:

.. code-block:: console

    make check


Valgrind
--------
`valgrind`_ is utilized to ensure memory is managed properly and to detect
defects such as memory leaks, buffer overruns, etc. Because `valgrind`_
requires Python is compiled with specific flags, a `Docker`_ file is provided
to `compile Python`_ as necessary to run the test suite under `valgrind`_.

To run test test suite under `valgrind`_:

.. code-block:: console

    make valgrind


.. _`Docker`: https://www.docker.com/
.. _`compile Python`: https://pythonextensionpatterns.readthedocs.io/en/latest/debugging/valgrind.html
.. _`SQL Server on Linux`: https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker
.. _`GNU make`: https://www.gnu.org/software/make/
.. _`pyenv`: https://github.com/pyenv/pyenv
.. _`pytest`: https://docs.pytest.org/en/stable/
.. _`tox`: https://tox.wiki/en/latest/
.. _`valgrind`: https://valgrind.org/
