# -*- coding: utf-8 -*-

#
#   build-app-py2app-setup.py
#
import wb_scm_version
import os
from setuptools import setup

v = wb_scm_version.__dict__

short_version = '%(major)d.%(minor)d.%(patch)d' % v
info_string = '%(APP_NAME)s-Devel %(major)d.%(minor)d.%(patch)d %(commit)s ©%(copyright_years)s Barry A. Scott. All Rights Reserved.' % v

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
                'app.tmp/wb.icns',
            'plist':
                dict(
                    CFBundleIdentifier='%(APP_ID)s-devel' % v,
                    CFBundleName='%(APP_NAME)s-Devel' % v,
                    CFBundleVersion=short_version,
                    CFBundleShortVersionString=short_version,
                    CFBundleGetInfoString=info_string
                    ),
            }},
    setup_requires =
        ['py2app'],
)
