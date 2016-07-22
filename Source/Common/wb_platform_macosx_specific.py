'''

 ====================================================================
 Copyright (c) 2004-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_macosx_specific.py

'''
import os
import types
import pathlib

__all_name_parts = None

def setupPlatformSpecific( all_name_parts ):
    global __all_name_parts
    __all_name_parts = all_name_parts

def getApplicationDir():
    name = '-'.join( [part.lower() for part in __all_name_parts] )
    folder = 'Library/Preferences/org.barrys-emacs.%s' % (name,)

    return getHomeFolder() / folder

def getLocalePath():
    return pathlib.Path( os.environ.get( 'PYTHONHOME', getApplicationDir() ) ) / 'locale'

def getNullDevice():
    return pathlib.Path( '/dev/null' )

def getHomeFolder():
    return pathlib.Path( os.environ['HOME'] )
