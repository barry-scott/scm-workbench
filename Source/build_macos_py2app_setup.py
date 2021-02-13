#
#   build_macos_py2app_setup.py
#
import sys
import os
from setuptools import setup
import wb_scm_version

import py2app

min_py2app = [0, 11]     # 0.11

py2app_version = [int(part) for part in py2app.__version__.split('.')]
if py2app_version < min_py2app:
    raise ValueError( 'build requires at least version %d.%d of py2app' % tuple(min_py2app) )

v = wb_scm_version.__dict__

if sys.argv[1] == '--package':
    del sys.argv[1]

else:
    v.APP_NAME = v.APP_NAME + '-Devel'

short_version = '%(major)d.%(minor)d.%(patch)d' % v
info_string = '%(APP_NAME)s %(major)d.%(minor)d.%(patch)d %(commit)s ©%(copyright_years)s Barry A. Scott. All Rights Reserved.' % v

setup(
    app =
        ['%s/Source/Scm/wb_scm_main.py' % (os.environ['BUILDER_TOP_DIR'],)],
    data_files =
        [],
    options =
        {'py2app':
            {
            'argv_emulation':
                False,
            'no_chdir':
                True,
            'iconfile':
                '%s/wb.icns' % (os.environ['DIST_DIR'],),
            'plist':
                dict(
                    CFBundleIdentifier='%(APP_ID)s' % v,
                    CFBundleName='%(APP_NAME)s' % v,
                    CFBundleVersion=short_version,
                    CFBundleShortVersionString=short_version,
                    CFBundleGetInfoString=info_string,
                    # claim we know about dark mode
                    NSRequiresAquaSystemAppearance='false',
                    ),
            }},
    setup_requires =
        ['py2app'],
)
