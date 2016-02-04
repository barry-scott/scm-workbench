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
    return os.path.join( getApplicationDir(), 'GitWorkBench.xml' )

def getLogFilename():
    return os.path.join( getApplicationDir(), 'GitWorkBench.log' )

def getLastCheckinMessageFilename():
    return os.path.join( getApplicationDir(), 'log_message.txt' )

def getLastLockMessageFilename():
    return os.path.join( getApplicationDir(), 'lock_message.txt' )

def setupPlatform():
    app_dir = getApplicationDir()
    if not os.path.exists( app_dir ):
        os.makedirs( app_dir )
