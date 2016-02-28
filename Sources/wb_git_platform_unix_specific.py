'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_unix_specific.py

'''
import os
import types
import pathlib

def getApplicationDir():
    return pathlib.Path( os.environ['HOME'] ) / '.GitWorkBench'

def getLocalePath( app ):
    return pathlib.Path( app.app_dir ) / 'locale'

def getNullDevice():
    return pathlib.Path( '/dev/null' )
