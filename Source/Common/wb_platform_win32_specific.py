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

__all__ = ('setupPlatformSpecific', 'getAppDir', 'getPreferencesDir'
          ,'getLocalePath', 'getDocUserGuide', 'getNullDevice'
          ,'getHomeFolder', 'getDefaultExecutableFolder', 'isInvalidFilename')

CSIDL_APPDATA = 0x1a        # Application Data
CSIDL_WINDOWS = 0x24        # windows folder
CSIDL_PROGRAM_FILES = 0x26  # program files folder

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

def getPreferencesDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_APPDATA, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getWindowsDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_WINDOWS, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getProgramFilesDir():
    buf = ctypes.create_unicode_buffer( ctypes.wintypes.MAX_PATH )
    ctypes.windll.shell32.SHGetFolderPathW( 0, CSIDL_PROGRAM_FILES, 0, SHGFP_TYPE_CURRENT, buf )

    return pathlib.Path( buf.value )

def getLocalePath():
    return getAppDir() / 'locale'

def getDocUserGuide():
    return app_dir / 'Documentation' / 'scm-workbench.html'

def getNullDevice():
    return pathlib.Path( 'NUL' )

def getHomeFolder():
    return pathlib.Path( os.environ['USERPROFILE'] )

def getDefaultExecutableFolder():
    return getProgramFilesDir()

__filename_bad_chars_set = set( '\\:/\000?<>*|"' )
__filename_reserved_names = set( ['nul', 'con', 'aux', 'prn',
    'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
    'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
    ] )

def isInvalidFilename( filename ):
    name_set = set( filename )

    if len( name_set.intersection( __filename_bad_chars_set ) ) != 0:
        return True

    name = filename.split( '.' )[0]
    if name.lower() in __filename_reserved_names:
        return True

    return False

if __name__ == '__main__':
    print( getPreferencesDir() )
