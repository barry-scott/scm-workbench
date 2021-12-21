#
#   build_macos_py2app_setup.py
#
import sys
import os
from setuptools import setup

import py2app

min_py2app = [0, 11]     # 0.11

py2app_version = [int(part) for part in py2app.__version__.split('.')]
if py2app_version < min_py2app:
    raise ValueError( 'build requires at least version %d.%d of py2app' % tuple(min_py2app) )

short_version = '1.2.3'
info_string = 'test-gui 1.2.3  ©2021 Barry A. Scott. All Rights Reserved.'

setup(
    app =
        ['gui_test.py'],
    data_files =
        [],
    options =
        {'py2app':
            {
            'argv_emulation':
                False,
            'no_chdir':
                True,
            'plist':
                dict(
                    CFBundleIdentifier='gui_test',
                    CFBundleName='gui_test',
                    CFBundleVersion=short_version,
                    CFBundleShortVersionString=short_version,
                    CFBundleGetInfoString=info_string,
                    ),
            }},
    setup_requires =
        ['py2app'],
)
