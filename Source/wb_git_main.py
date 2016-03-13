#!/usr/bin/python3
'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_main.py

'''
import sys
import os
import locale

# must setup U_ very early on to allow module level strings to be
# marked as needing translation.

import builtins
# U_( 'static string' )
builtins.__dict__['U_'] = lambda s: s


import wb_git_app

def prerequesitChecks():
    return 1

def main( argv ):
    #
    #   set a working STDOUT before loading most modules
    #
    # help debug when stdout goes nowhere useful
    # Mac OS X and Windows are the main problems
    if sys.platform == 'darwin':
        if '--noredirect' not in argv:
            sys.stdout = open( os.environ.get( 'WB_GIT_STDOUT_LOG', '/dev/null' ), 'w', 1 )
            sys.stderr = sys.stdout

    elif sys.platform.startswith( 'win' ):
        if '--noredirect' not in argv:
            sys.stdout = open( os.environ.get( 'WB_GIT_STDOUT_LOG', 'nul' ), 'w' )
            sys.stderr = sys.stdout

    # don't pollute any subprocesses with env vars
    # from packaging processing
    for envvar in ['PYTHONPATH', 'PYTHONHOME', 'PYTHONEXECUTABLE']:
        if envvar in os.environ:
            del os.environ[ envvar ]

    # Create the win application and start its message loop
    app = wb_git_app.WbGit_App( argv )

    if not prerequesitChecks():
        return 1

    app.main_window.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit( main( sys.argv ) )
