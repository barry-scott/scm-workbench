#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_main.py

'''
import sys
import os

import wb_platform_specific

def main( app_cls, argv ):
    #
    #   set a working STDOUT before loading most modules
    #
    # help debug when stdout goes nowhere useful
    # Mac OS X and Windows are the main problems
    if wb_platform_specific.isMacOs() or wb_platform_specific.isWindows():
        if '--noredirect' not in argv:
            sys.stdout = open( os.environ.get( 'WB_STDOUT_LOG', str(wb_platform_specific.getNullDevice()) ), 'w', 1 )
            sys.stderr = sys.stdout

    # don't pollute any subprocesses with env vars
    # from packaging processing
    for envvar in ['PYTHONPATH', 'PYTHONHOME', 'PYTHONEXECUTABLE']:
        if envvar in os.environ:
            del os.environ[ envvar ]

    # Create the win application and start its message loop
    app = app_cls( argv )

    app.main_window.show()

    rc = app.exec()

    # force clean up of objects to avoid segv on exit
    del app

    # prevent exit handlers from running as this allows for a segv
    # My guess is that there are some Qt objects that are not owned
    # but I have no way to take them down
    #os._exit( rc )
    return rc
