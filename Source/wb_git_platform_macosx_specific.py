'''

 ====================================================================
 Copyright (c) 2004-2010 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_macosx_specific.py

'''
import os
import types
import pathlib

def getApplicationDir():
    return pathlib.Path( os.path.join( os.environ['HOME'] ) / 'Library/Preferences/org.tigris.git.Workbench'

def getLocalePath( app ):
    return pathlib.Path( os.environ.get( 'PYTHONHOME', app.app_dir ) ) / 'locale'

def getNullDevice():
    return pathlib.Path( '/dev/null' )
