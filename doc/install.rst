Getting Started
===============

The easiest way to install `k-cTDS` is from `PyPI`_ using `pip`_::

    pip install k-ctds

Pre-built wheels are available for Linux (x86_64, aarch64), macOS
(x86_64, arm64), and Windows (AMD64). The wheels bundle `FreeTDS`_ and
`OpenSSL`_ so there is nothing else to install.

The rest of this page covers building from source, which is only
necessary when linking against a custom build of `FreeTDS`_.


Building From Source
--------------------

`k-cTDS` is built on top of `FreeTDS`_, which must be installed before
compiling from source.

Installing FreeTDS
------------------

It is **highly** recommended to use the latest stable version of `FreeTDS`_, if
possible. If this is not possible, `FreeTDS`_ can be installed using your
system's package manager.

.. warning::

    `FreeTDS`_ *1.0* or later is required. Older versions are not
    supported.

Installation From Source
^^^^^^^^^^^^^^^^^^^^^^^^

`FreeTDS`_ can be easily built from the latest stable source for use in a
`virtualenv`_ using the following:

.. code-block:: bash

    # Create the virtual environment.
    virtualenv ctds-venv && cd ctds-venv
    wget 'https://www.freetds.org/files/stable/freetds-patched.tar.gz'
    tar -xzf freetds-patched.tar.gz
    pushd freetds-*

    # The "--with-openssl" argument is required to connect to some databases,
    # such as Microsoft Azure.
    ./configure \
            --prefix "$(dirname $(pwd))" \
            --with-openssl=$(openssl version -d | sed  -r 's/OPENSSLDIR: "([^"]*)"/\1/') \
        && make && make install
    popd


Installation On Debian-based Systems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both *FreeTDS* and the *Python* development headers can easily be installed
using the system package manager on Debian-based systems, such as Ubuntu.

.. code-block:: bash

    sudo apt-get install freetds-dev python3-dev


Installation On Mac OS X
^^^^^^^^^^^^^^^^^^^^^^^^

On OS X, `homebrew`_ is recommended for installing `FreeTDS`_.

.. code-block:: bash

    brew update
    brew install freetds


Installation On Windows
^^^^^^^^^^^^^^^^^^^^^^^

On Windows, `FreeTDS`_ should be installed from the latest source code.
A powershell script is included which may aid in this.

You'll need `Visual Studio 2022 Build Tools`_ and `CMake`_, and `7-Zip`_ installed.

.. note::

    64-bit Python is required. The build toolchain targets ``amd64`` and is
    only tested against 64-bit Python in CI.

.. code-block:: powershell

    # Add cmake to the path if necessary, using:  $env:Path += ";c:\Program Files\CMake\bin\"
    ./windows/freetds-install.ps1
    # FreeTDS headers and include files are installed to ./build/include
    # and ./build/lib

PIP Installation
----------------

Once `FreeTDS`_ is installed, *k-cTDS* can be installed from source
using `pip`_.

When using a non-system version of `FreeTDS`_, set the following
environment variables to point at your FreeTDS installation:

.. code-block:: bash

    CTDS_INCLUDE_DIRS=$(pwd)/include \
        CTDS_LIBRARY_DIRS=$(pwd)/lib \
        CTDS_RUNTIME_LIBRARY_DIRS=$(pwd)/lib \
        pip install k-ctds --no-binary k-ctds

The three ``CTDS_*`` environment variables are read by ``setup.py``
during compilation of the C extension:

.. list-table::
   :widths: 35 65
   :header-rows: 1

   * - Variable
     - Purpose
   * - ``CTDS_INCLUDE_DIRS``
     - Directories containing FreeTDS header files (``sybdb.h``,
       ``ctpublic.h``). Passed to the C compiler as include paths.
       Separate multiple directories with ``:``.
   * - ``CTDS_LIBRARY_DIRS``
     - Directories containing FreeTDS shared libraries (``libsybdb``,
       ``libct``). Passed to the linker as library search paths.
       Separate multiple directories with ``:``.
   * - ``CTDS_RUNTIME_LIBRARY_DIRS``
     - Baked into the compiled extension as an RPATH so the dynamic
       linker can find FreeTDS at runtime without ``LD_LIBRARY_PATH``.
       Not supported on Windows.

When using the system version of `FreeTDS`_, no variables are needed:

.. code-block:: bash

    pip install k-ctds --no-binary k-ctds

When building on Windows, run the following in powershell:

.. code-block:: powershell

    # current directory must be the k-ctds root
    $Env:CTDS_INCLUDE_DIRS = "$(pwd)/build/include"
    $Env:CTDS_LIBRARY_DIRS = "$(pwd)/build/lib"
    $Env:CTDS_RUNTIME_LIBRARY_DIRS = "$(pwd)/build/lib"
    pip install -e .

    # After pip install, copy FreeTDS DLLs alongside the installed extension:
    Copy-Item "$Env:CTDS_LIBRARY_DIRS\*.dll" "$(python -c 'import site; print(site.getsitepackages()[0])')"

Alternatively, if you prefer not to copy DLLs, you can register the
directory at runtime before importing. On Python 3.8+, Windows no longer
searches ``PATH`` for DLL dependencies of extension modules, so
``os.add_dll_directory`` must be called before the first import:

.. code-block:: python

    import os
    os.add_dll_directory(r'C:\path\to\freetds\lib')
    import k_ctds

.. _FreeTDS: https://www.freetds.org
.. _OpenSSL: https://www.openssl.org/
.. _PyPI: https://pypi.org/project/k-ctds/
.. _homebrew: https://brew.sh/
.. _pip: https://pip.pypa.io/en/stable/
.. _virtualenv: https://virtualenv.pypa.io/en/latest/
.. _Visual Studio 2022 Build Tools: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
.. _CMake: https://cmake.org/
.. _7-Zip: https://www.7-zip.org/
