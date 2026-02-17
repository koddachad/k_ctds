#!/usr/bin/env python
"""
Minimal setup.py — retained only for the C extension build logic that
cannot be expressed declaratively in pyproject.toml (platform-specific
compiler flags, env-var directory lookups, coverage/profiling toggles).

All package metadata now lives in pyproject.toml.
"""

import glob
import os
import os.path
import platform
import sys

import setuptools

# ---------------------------------------------------------------------------
# Version — single source of truth is pyproject.toml [project] version.
# These constants are compiled into the C extension via define_macros.
# ---------------------------------------------------------------------------
CTDS_MAJOR_VERSION = 2
CTDS_MINOR_VERSION = 1
CTDS_PATCH_VERSION = 1

# ---------------------------------------------------------------------------
# Build flags driven by environment variables
# ---------------------------------------------------------------------------
STRICT = os.environ.get('CTDS_STRICT')
WINDOWS = platform.system() == 'Windows'
COVERAGE = os.environ.get('CTDS_COVER', False)

LIBRARIES = [
    'sybdb',
    'ct',  # required for ct_config only
]

EXTRA_COMPILE_ARGS = []
EXTRA_LINK_ARGS = []

if not WINDOWS:
    if STRICT:
        EXTRA_COMPILE_ARGS += [
            '-ansi',
            '-Wall',
            '-Wextra',
            '-Werror',
            '-Wconversion',
            '-Wpedantic',
            '-std=c99',
        ]

    if os.environ.get('CTDS_PROFILE'):
        EXTRA_COMPILE_ARGS.append('-pg')
        profile_dir = os.environ['CTDS_PROFILE']
        if os.path.isdir(profile_dir):
            EXTRA_COMPILE_ARGS += ['-fprofile-dir', '"{0}"'.format(profile_dir)]
        EXTRA_LINK_ARGS.append('-pg')

    if COVERAGE:
        EXTRA_COMPILE_ARGS += ['-fprofile-arcs', '-ftest-coverage']
        EXTRA_LINK_ARGS.append('-fprofile-arcs')

    # pthread is required on macOS for thread-local storage support.
    if sys.platform == 'darwin':
        EXTRA_LINK_ARGS.append('-lpthread')
else:
    if STRICT:
        EXTRA_COMPILE_ARGS += [
            '/WX',
            '/wd4068',
            '/w14242',
            '/w14254',
            '/w14263',
            '/w14265',
            '/w14287',
            '/we4289',
            '/w14296',
            '/w14311',
            '/w14545',
            '/w14546',
            '/w14547',
            '/w14549',
            '/w14555',
            '/w14619',
            '/w14640',
            '/w14826',
            '/w14905',
            '/w14906',
            '/w14928',
            '/Zi',
        ]
    if COVERAGE:
        EXTRA_COMPILE_ARGS.append('/Od')
        EXTRA_LINK_ARGS.append('/DEBUG')

    LIBRARIES += [
        'shell32',
        'ws2_32',
    ]


def splitdirs(name):
    dirs = os.environ.get(name)
    return dirs.split(os.pathsep) if dirs else []


setuptools.setup(
    ext_modules=[
        setuptools.Extension(
            'k_ctds._tds',
            glob.glob(os.path.join('src', 'k_ctds', '*.c')),
            define_macros=[
                ('CTDS_MAJOR_VERSION', CTDS_MAJOR_VERSION),
                ('CTDS_MINOR_VERSION', CTDS_MINOR_VERSION),
                ('CTDS_PATCH_VERSION', CTDS_PATCH_VERSION),
                ('PY_SSIZE_T_CLEAN', '1'),
                ('MSDBLIB', '1'),
            ],
            include_dirs=splitdirs('CTDS_INCLUDE_DIRS'),
            library_dirs=splitdirs('CTDS_LIBRARY_DIRS'),
            # runtime_library_dirs is not supported on Windows.
            runtime_library_dirs=[] if WINDOWS else splitdirs('CTDS_RUNTIME_LIBRARY_DIRS'),
            extra_compile_args=EXTRA_COMPILE_ARGS,
            extra_link_args=EXTRA_LINK_ARGS,
            libraries=LIBRARIES,
            language='c',
        ),
    ],
)
