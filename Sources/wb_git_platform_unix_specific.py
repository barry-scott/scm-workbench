'''

 ====================================================================
 Copyright (c) 2003-2011 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_unix_specific.py

'''
import os
import types

def getApplicationDir():
    return os.path.join( os.environ['HOME'], '.WorkBench' )

def getLocalePath( app ):
    return os.path.join( app.app_dir, 'locale' )

def getNullDevice():
    return '/dev/null'
