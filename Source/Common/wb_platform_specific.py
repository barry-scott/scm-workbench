'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_specific.py

'''

import sys

__all_name_parts = None

if sys.platform == 'win32':
    from wb_platform_win32_specific import *

elif sys.platform == 'darwin':
    from wb_platform_macosx_specific import *

else:
    from wb_platform_unix_specific import *

def isWindows():
    return sys.platform == 'win32'

def isMacOs():
    return sys.platform == 'darwin'

def isUnix():
    return not isWindows() and not isMacOs()

def getPreferencesFilename():
    name = ''.join( __all_name_parts )
    filename = '%s.xml'   % (name,)
    return getPreferencesDir() / filename

def getLogFilename():
    name = ''.join( __all_name_parts )
    filename = '%s.log'   % (name,)
    return getPreferencesDir() / filename

def getLastCheckinMessageFilename():
    return getPreferencesDir() / 'log_message.txt'

def getLastLockMessageFilename():
    return getPreferencesDir() / 'lock_message.txt'

def setupPlatform( all_name_parts, argv0 ):
    setupPlatformSpecific( all_name_parts, argv0 )

    global __all_name_parts
    __all_name_parts = all_name_parts

    app_dir = getPreferencesDir()
    if not app_dir.exists():
        app_dir.mkdir( parents=True )
