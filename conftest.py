"""
Pytest conftest.py — loaded before test collection begins.

On Windows with Python 3.8+, the default DLL search path no longer includes
directories listed in the PATH environment variable when loading extension
module dependencies. FreeTDS DLLs (ct.dll, sybdb.dll) must be explicitly
registered via os.add_dll_directory() so that the _tds extension can find them.

This file should be placed in the project root (next to setup.py) or in the
tests/ directory.
"""
import os
import platform
import sys


def _register_freetds_dll_directory():
    """Register the FreeTDS DLL directory on Windows (Python 3.8+)."""
    if platform.system() != 'Windows':
        return

    if not hasattr(os, 'add_dll_directory'):
        # Python < 3.8 doesn't need this; PATH is still searched.
        return

    # Check BUILD_INSTALL_PREFIX (set in appveyor.yml / build_script.ps1).
    dll_dir = os.environ.get('BUILD_INSTALL_PREFIX')
    if dll_dir:
        lib_dir = os.path.join(dll_dir, 'lib')
        if os.path.isdir(lib_dir):
            os.add_dll_directory(lib_dir)
            return

    # Fallback: check CTDS_LIBRARY_DIRS (set during pip install).
    lib_dirs = os.environ.get('CTDS_LIBRARY_DIRS')
    if lib_dirs:
        for d in lib_dirs.split(os.pathsep):
            if os.path.isdir(d):
                os.add_dll_directory(d)


_register_freetds_dll_directory()
