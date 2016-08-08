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
import locale

# must setup U_ very early on to allow module level strings to be
# marked as needing translation.

import builtins
# U_( 'static string' )
builtins.__dict__['U_'] = lambda s: s

def main( app_cls, argv ):
    #
    #   set a working STDOUT before loading most modules
    #
    # help debug when stdout goes nowhere useful
    # Mac OS X and Windows are the main problems
    if sys.platform == 'darwin':
        if '--noredirect' not in argv:
            sys.stdout = open( os.environ.get( 'WB_STDOUT_LOG', '/dev/null' ), 'w', 1 )
            sys.stderr = sys.stdout

    elif sys.platform.startswith( 'win' ):
        if '--noredirect' not in argv:
            sys.stdout = open( os.environ.get( 'WB_STDOUT_LOG', 'NUL' ), 'w' )
            sys.stderr = sys.stdout

    # don't pollute any subprocesses with env vars
    # from packaging processing
    for envvar in ['PYTHONPATH', 'PYTHONHOME', 'PYTHONEXECUTABLE']:
        if envvar in os.environ:
            del os.environ[ envvar ]

    # Create the win application and start its message loop
    app = app_cls( argv )

    app.main_window.show()

    rc = app.exec_()

    # force clean up of objects to avoid segv on exit
    del app

    # prevent exit handlers from running as this allows for a segv
    # My guess is that there are some Qt objects that are not owned
    # but I have no way to take them down
    #os._exit( rc )
    return rc
