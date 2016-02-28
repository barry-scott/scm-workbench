'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_platform_specific.py

'''

import sys

if sys.platform == 'win32':
    from wb_git_platform_win32_specific import *

elif sys.platform == 'darwin':
    from wb_git_platform_macosx_specific import *

else:
    from wb_git_platform_unix_specific import *

def getPreferencesFilename():
    return getApplicationDir() / 'GitWorkBench.xml'

def getLogFilename():
    return getApplicationDir() / 'GitWorkBench.log'

def getLastCheckinMessageFilename():
    return getApplicationDir() / 'log_message.txt'

def getLastLockMessageFilename():
    return getApplicationDir() / 'lock_message.txt'

def setupPlatform():
    app_dir = getApplicationDir()
    if not app_dir.exists():
        app_dir.mkdir( parents=True )
