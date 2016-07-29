'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_win32_specific.py

'''
import os
import pathlib

import ctypes
import ctypes.wintypes

CSIDL_APPDATA = 0x1a    # Application Data
CSIDL_WINDOWS = 0x24    # windows folder
SHGFP_TYPE_CURRENT = 0  # Want current, not default value
SHGFP_TYPE_DEFAULT = 1


app_dir = None

__all_name_parts = None

def setupPlatformSpecific( all_name_parts, argv0 ):
    global __all_name_parts
    __all_name_parts = all_name_parts

    global app_dir

    if argv0[1:3] ==':\\':
        app_dir = pathlib.Path( argv0 ).parent

    elif '\\' in argv0:
        app_dir = pathlib.Path( argv0 ).resolve().parent

    else:
        for folder in [os.getcwd()] + [p.strip() for p in os.environ.get( 'PATH', '' ).split( ';' )]:
            app_path = pathlib.Path( folder ) / argv0
            if app_path.exists():
                app_dir = app_path.parent
                break

def getAppDir():
    assert app_dir is not None, 'call setupPlatformSpecific() first'
    return app_dir

def getApplicationDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_APPDATA, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getWindowsDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_WINDOWS, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getLocalePath():
    return getApplicationDir() / 'locale'

def getNullDevice():
    return pathlib.Path( 'NUL' )

def getHomeFolder():
    return pathlib.Path( os.environ['USERPROFILE'] )

if __name__ == '__main__':
    print( getApplicationDir() )
