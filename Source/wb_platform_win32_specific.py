'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_win32_specific.py

'''
#from win32com.shell import shell, shellcon
import ctypes # and use instead of win32com.shell
import pathlib

__all_name_parts = None

def setupPlatformSpecific( all_name_parts ):
    global __all_name_parts = all_name_parts

SHGFP_TYPE_CURRENT = 0
SHGFP_TYPE_DEFAULT = 1

def getApplicationDir():
    name = ''.join( __all_name_parts )
    folder = '%s' % (name,)

    #QQQ implement using ctypes
    app_folder = shell.SHGetFolderPath( 0, shellcon.CSIDL_APPDATA,
                0, SHGFP_TYPE_CURRENT )
    return pathlib.Path( app_folder ) / folder

def getLocalePath():
    return getApplicationDir() / 'locale'

def getNullDevice():
    return pathlib.Path( 'NUL' )
