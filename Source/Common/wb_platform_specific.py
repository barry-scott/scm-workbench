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
    from wb_git_platform_win32_specific import *

elif sys.platform == 'darwin':
    from wb_git_platform_macosx_specific import *

else:
    from wb_git_platform_unix_specific import *

def getPreferencesFilename():
    name = ''.join( __all_name_parts )
    filename = '%s.xml'   % (name,)
    return getApplicationDir() / filename

def getLogFilename():
    name = ''.join( __all_name_parts )
    filename = '%s.log'   % (name,)
    return getApplicationDir() / filename

def getLastCheckinMessageFilename():
    return getApplicationDir() / 'log_message.txt'

def getLastLockMessageFilename():
    return getApplicationDir() / 'lock_message.txt'

def setupPlatform( all_name_parts ):
    setupPlatformSpecific( all_name_parts )
    global __all_name_parts
    __all_name_parts = all_name_parts

    app_dir = getApplicationDir()
    if not app_dir.exists():
        app_dir.mkdir( parents=True )
