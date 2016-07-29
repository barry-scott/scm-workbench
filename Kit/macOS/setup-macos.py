# -*- coding: utf-8 -*-

#
#   setup-macos.py
#
import wb_scm_version
import os
from setuptools import setup

v = wb_scm_version.__dict__

short_version = '%(major)d.%(minor)d.%(patch)d' % v
info_string = 'SCM Workbench-Devel %(major)d.%(minor)d.%(patch)d %(commit)s ©%(copyright_years)s Barry A. Scott. All Rights Reserved.' % v


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
                'tmp/wb.icns',
            'plist':
                dict(
                    CFBundleIdentifier='org.barrys-emacs.scm-workbench-devel',
                    CFBundleName="SCM Workbench-Devel",
                    CFBundleVersion=short_version,
                    CFBundleShortVersionString=short_version,
                    CFBundleGetInfoString=info_string
                    ),
            }},
    setup_requires =
        ['py2app'],
)
