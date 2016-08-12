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

__all_name_parts = None
app_dir

def setupPlatformSpecific( all_name_parts, argv0 ):
    global __all_name_parts
    __all_name_parts = all_name_parts

    global app_dir

    if argv0.startswith( '/' ):
        app_dir = pathlib.Path( argv0 ).parent

    elif '/' in argv0:
        app_dir = pathlib.Path( argv0 ).resolve().parent

    else:
        for folder in [pathlib.Path( s.strip() ) for s in os.environ.get( 'PATH', '' ).split( ':' )]:
            app_path = folder / argv0
            if app_path.exists():
                app_dir = app_path.parent
                break

    if app_dir is None:
        app_dir = pathlib.Path( os.getcwd() )

def getPreferencesDir():
    name = ''.join( __all_name_parts )
    folder = '.%s' % (name,)
    return getHomeFolder() / folder

def getLocalePath():
    return getAppDir() / 'locale'

def getNullDevice():
    return pathlib.Path( '/dev/null' )

def getHomeFolder():
    return pathlib.Path( os.environ['HOME'] )

__filename_bad_chars_set = set( '/\000' )
def isInvalidFilename( filename ):
    name_set = set( folder_name )

    if len( name_set.intersection( __filename_bad_chars_set ) ) != 0:
        return True

    return False
