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

__all_name_parts = None

def setupPlatformSpecific( all_name_parts ):
    global __all_name_parts
    __all_name_parts = all_name_parts

SHGFP_TYPE_CURRENT = 0
SHGFP_TYPE_DEFAULT = 1

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
